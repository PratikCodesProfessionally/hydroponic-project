#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hydroponik-Steuerung mit automatischer pH-Regelung
==================================================

Betriebsarten (Kommandozeile):

    python3 hydroponik.py --kalibrieren
        Gibt ausschliesslich die Rohspannung des pH-Sensors aus.
        Werkzeug fuer die Zweipunktkalibrierung. Keine Aktoren aktiv.

    python3 hydroponik.py --nur-messen
        Vollstaendiger Messbetrieb inkl. Logging und API,
        Dosierpumpe bleibt gesperrt. Standard fuer die Inbetriebnahme.

    python3 hydroponik.py --regeln
        Messbetrieb mit aktiver pH-Regelung.
        Erst verwenden, wenn Kalibrierung und Pumpenkennlinie vorliegen.
"""

import argparse
import csv
import os
import signal
import sys
import threading
import time
from datetime import datetime

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_dht
from gpiozero import DigitalInputDevice, DigitalOutputDevice
from flask import Flask, jsonify, request
from flask_cors import CORS


# ==================================================================
#   1  KONFIGURATION
# ==================================================================

# ---- Pinbelegung -------------------------------------------------
DHT_PIN         = board.D17          # DHT11, BCM 17
FEUCHTE_PIN     = 27                 # Kontaktsensor, BCM 27
PUMP_PIN        = 5                  # Dosierpumpe ueber Treiber, BCM 5
W1_DEVICE_PATH  = "/sys/bus/w1/devices/"
ADS_ADRESSE     = 0x48
ADS_KANAL       = 0
ADS_GAIN        = 1                  # Vollausschlag +/- 4,096 V

# ---- pH-Kalibrierung ---------------------------------------------
# ACHTUNG: Diese beiden Werte MUESSEN aus der Zweipunktkalibrierung
# stammen. Vorgehen siehe Funktion kalibriermodus() weiter unten.
#
#   STEIGUNG        = (pH2 - pH1) / (U2 - U1)      Einheit: pH/V
#   ACHSENABSCHNITT = pH1 - STEIGUNG * U1          Einheit: pH
#
# Plausibilitaet: 1/|STEIGUNG| sollte zwischen 0,050 und 0,059 V/pH
# liegen (Nernst-Steilheit). Ausserhalb -> Elektrode oder Verdrahtung
# pruefen, nicht weiterrechnen.

STEIGUNG        = None               # <-- eintragen, z. B. -17.85
ACHSENABSCHNITT = None               # <-- eintragen, z. B.  38.42

KALIBRIER_TEMPERATUR = 25.0          # Wassertemperatur waehrend der Kalibrierung, °C

# ---- Temperaturkompensation --------------------------------------
# Die Nernst-Steilheit ist temperaturabhaengig. Bei Abweichungen von
# wenigen Kelvin gegenueber der Kalibriertemperatur ist der Fehler
# klein; die Kompensation laesst sich zuschalten, sobald der
# Temperatureinfluss im Versuch belegt wurde.
TEMPERATURKOMPENSATION = False

# ---- Messung -----------------------------------------------------
PH_MESSWERTE       = 20              # Einzelmessungen je Mittelwert
PH_MESSABSTAND_S   = 0.05
PH_TRIM_ANTEIL     = 0.25            # Anteil der verworfenen Randwerte
PH_MIN_GUELTIG     = 0.0
PH_MAX_GUELTIG     = 14.0
SPANNUNG_MIN_GUELTIG = 0.05          # V, darunter: Sensor nicht angeschlossen
SPANNUNG_MAX_GUELTIG = 3.30          # V, darueber: Klemmung am ADS-Eingang

# ---- Regelung ----------------------------------------------------
# Alle Werte sind aus Kalibrierung, Pumpenkennlinie und
# Titrationsversuch herzuleiten und hier zu dokumentieren.
SOLLWERT_PH        = 5.8
TOLERANZ_PH        = 0.2             # Eingriff ab 6,0
SPERRZEIT_S        = 300             # aus Titrationsversuch (Einschwingzeit)
DOSIERZEIT_S       = 3.0             # aus Pumpenkennlinie
SICHERHEITSFAKTOR  = 0.5             # bewusste Unterdosierung, da nur pH- verfuegbar
PUMPE_MAX_EIN_S    = 10.0            # harte Obergrenze je Einschaltvorgang

# Begrenzung der Tagesmenge als gleitendes 24-h-Fenster (kein Kalendertag,
# damit nicht um Mitternacht die doppelte Menge moeglich ist).
# Der Wert ist eine Alarmschwelle, keine Betriebsgroesse: er gehoert deutlich
# ueber den Bedarf im Normalbetrieb gelegt, den der Titrationsversuch liefert.
# Loest die Sperre aus, ist etwas defekt (Leck, Fehlkalibrierung, zu hohe
# Pufferkapazitaet) - dann ist ein Blick von Hand faellig.
MAX_DOSIERUNGEN_TAG = 20
DOSIER_FENSTER_S    = 24 * 3600

# ---- Laufzeit ----------------------------------------------------
MESSINTERVALL_S    = 2               # Zyklus der Hauptschleife
LOG_INTERVALL_S    = 30              # Abstand der CSV-Eintraege
# Absoluter Pfad neben diesem Skript. Ein relativer Pfad wuerde als
# systemd-Service im Arbeitsverzeichnis des Dienstes landen, nicht im Projekt.
LOG_FILE           = os.getenv(
    "HYDRO_LOG_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "hydroponik_log.csv"),
)
API_PORT           = 5000

# Bindeadresse der API. "0.0.0.0" = alle Schnittstellen (eth0, WLAN, lokal).
# Zum Haerten auf die Adresse der Direktverbindung setzen, dann ist die API
# ueber das WLAN - und damit ueber die oeffentliche Hochschuladresse - nicht
# mehr erreichbar:
#     HYDRO_API_HOST=192.168.10.1 python3 iot/hydroponik.py --regeln
# Achtung: die Adresse muss beim Start bereits auf eth0 gesetzt sein, sonst
# scheitert das Binden mit "Cannot assign requested address".
API_HOST           = os.getenv("HYDRO_API_HOST", "0.0.0.0")

CSV_SPALTEN = [
    "timestamp", "ph", "ph_spannung", "wasser_temp",
    "luft_temp", "luft_feuchte", "feuchtigkeit",
    "pumpe", "dosierungen_gesamt", "dosierungen_24h",
    "dosierung_gesperrt", "betriebsart",
]


# ==================================================================
#   2  HARDWARE
# ==================================================================

i2c     = busio.I2C(board.SCL, board.SDA)
ads     = ADS.ADS1115(i2c, address=ADS_ADRESSE)
ads.gain = ADS_GAIN
ph_chan = AnalogIn(ads, ADS_KANAL)

dht            = adafruit_dht.DHT11(DHT_PIN, use_pulseio=False)
feuchte_sensor = DigitalInputDevice(FEUCHTE_PIN, pull_up=False)
pumpe          = DigitalOutputDevice(PUMP_PIN, initial_value=False)

pumpen_lock = threading.Lock()       # verhindert gleichzeitigen Zugriff
                                     # aus Hauptschleife und API


# ==================================================================
#   3  ZUSTAND
# ==================================================================

zustand = {
    "ph":                 None,
    "ph_spannung":        None,
    "wasser_temp":        None,
    "luft_temp":          None,
    "luft_feuchte":       None,
    "feuchtigkeit":       None,
    "pumpe":              False,
    "betriebsart":        "unbekannt",
    # Nur zur Anzeige in der Weboberflaeche - die Regelung liest weiterhin
    # direkt SOLLWERT_PH und TOLERANZ_PH.
    "sollwert_ph":        SOLLWERT_PH,
    "toleranz_ph":        TOLERANZ_PH,
    "letzte_dosierung":   None,
    "dosierungen_gesamt": 0,         # seit Programmstart, nur zur Information
    "dosierungen_24h":    0,         # massgeblich fuer die Mengenbegrenzung
    "max_dosierungen_tag": MAX_DOSIERUNGEN_TAG,
    "dosierung_gesperrt": False,     # True: Tagesgrenze erreicht, kein Eingriff mehr
    "sperrzeit_rest_s":   0,
    "timestamp":          None,
}

regelung_aktiv     = False
_letzte_dosierung  = 0.0             # monotone Zeit der letzten Dosierung
_dosier_zeitpunkte = []              # monotone Zeiten fuer das 24-h-Fenster
_laeuft            = True


# ==================================================================
#   4  MESSFUNKTIONEN
# ==================================================================

def lies_ph_spannung():
    """Gemittelte Sensorspannung in Volt, None bei Fehler."""
    try:
        werte = []
        for _ in range(PH_MESSWERTE):
            werte.append(ph_chan.voltage)
            time.sleep(PH_MESSABSTAND_S)
    except OSError as fehler:
        print(f"  [FEHLER] I2C-Zugriff auf ADS1115: {fehler}")
        return None

    werte.sort()
    rand = int(len(werte) * PH_TRIM_ANTEIL)
    kern = werte[rand:len(werte) - rand] or werte
    return sum(kern) / len(kern)


def spannung_zu_ph(spannung, wasser_temp=None):
    """Rechnet die Sensorspannung ueber die Kalibriergerade in pH um."""
    if spannung is None:
        return None

    if not (SPANNUNG_MIN_GUELTIG <= spannung <= SPANNUNG_MAX_GUELTIG):
        print(f"  [WARNUNG] Spannung {spannung:.4f} V ausserhalb des "
              f"gueltigen Bereichs - Sensor pruefen.")
        return None

    steigung = STEIGUNG
    if TEMPERATURKOMPENSATION and wasser_temp is not None:
        # Nernst-Steilheit skaliert mit der absoluten Temperatur
        steigung = STEIGUNG * (KALIBRIER_TEMPERATUR + 273.15) / (wasser_temp + 273.15)

    ph = steigung * spannung + ACHSENABSCHNITT

    if not (PH_MIN_GUELTIG <= ph <= PH_MAX_GUELTIG):
        print(f"  [WARNUNG] Berechneter pH {ph:.2f} unplausibel - verworfen.")
        return None

    return round(ph, 2)


def lies_ph(wasser_temp=None):
    """Liefert (pH, Spannung); beide None, wenn die Messung ungueltig ist."""
    spannung = lies_ph_spannung()
    return spannung_zu_ph(spannung, wasser_temp), spannung


def lies_wassertemperatur():
    """DS18B20 ueber 1-Wire, None bei Fehler."""
    try:
        ordner = [d for d in os.listdir(W1_DEVICE_PATH) if d.startswith("28-")]
        if not ordner:
            return None
        with open(f"{W1_DEVICE_PATH}{ordner[0]}/w1_slave", "r") as datei:
            zeilen = datei.readlines()
        if "YES" not in zeilen[0]:
            return None
        return round(float(zeilen[1].split("t=")[-1]) / 1000.0, 2)
    except (OSError, IndexError, ValueError):
        return None


def lies_luftwerte():
    """DHT11; initialisiert den Sensor bei Timing-Fehlern neu."""
    global dht
    try:
        return dht.temperature, dht.humidity
    except RuntimeError:
        return None, None                 # Timing-Fehler, im naechsten Zyklus erneut
    except Exception as fehler:
        print(f"  [FEHLER] DHT11: {fehler}")
        try:
            dht.exit()
            time.sleep(1)
            dht = adafruit_dht.DHT11(DHT_PIN, use_pulseio=False)
        except Exception:
            pass
        return None, None


# ==================================================================
#   5  AKTORIK
# ==================================================================

def pumpe_laufen_lassen(sekunden, grund=""):
    """Schaltet die Pumpe fuer eine begrenzte Zeit ein.

    Die Dauer wird hart auf PUMPE_MAX_EIN_S begrenzt. Der Lock stellt
    sicher, dass Regelung und API nicht gleichzeitig schalten.
    """
    dauer = min(max(sekunden, 0.0), PUMPE_MAX_EIN_S)
    if dauer <= 0:
        return 0.0

    if not pumpen_lock.acquire(blocking=False):
        print("  [ABGEWIESEN] Pumpe laeuft bereits.")
        return 0.0

    try:
        print(f"  [PUMPE] EIN fuer {dauer:.1f} s {grund}")
        pumpe.on()
        zustand["pumpe"] = True
        time.sleep(dauer)
    finally:
        pumpe.off()
        zustand["pumpe"] = False
        pumpen_lock.release()
        print("  [PUMPE] AUS")

    return dauer


def dosierungen_24h():
    """Anzahl der Dosierungen im gleitenden 24-h-Fenster."""
    global _dosier_zeitpunkte

    grenze = time.monotonic() - DOSIER_FENSTER_S
    _dosier_zeitpunkte = [zeit for zeit in _dosier_zeitpunkte if zeit > grenze]
    return len(_dosier_zeitpunkte)


def dosiere():
    """Fuehrt eine Chargendosierung aus und startet die Sperrzeit."""
    global _letzte_dosierung

    dauer = DOSIERZEIT_S * SICHERHEITSFAKTOR
    pumpe_laufen_lassen(dauer, "(pH-Korrektur)")

    _letzte_dosierung = time.monotonic()
    _dosier_zeitpunkte.append(_letzte_dosierung)
    zustand["dosierungen_gesamt"] += 1
    zustand["dosierungen_24h"] = dosierungen_24h()
    zustand["letzte_dosierung"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"  [REGELUNG] Dosierung {zustand['dosierungen_gesamt']} erfolgt "
          f"({zustand['dosierungen_24h']}/{MAX_DOSIERUNGEN_TAG} in 24 h), "
          f"Sperrzeit {SPERRZEIT_S} s laeuft.")


def regele(ph):
    """Zweipunktregelung mit Sperrzeit und Mengenbegrenzung."""
    if not regelung_aktiv:
        return

    if ph is None:
        print("  [REGELUNG] Keine gueltige Messung - kein Eingriff.")
        return

    verstrichen = time.monotonic() - _letzte_dosierung
    rest = max(0, SPERRZEIT_S - verstrichen)
    zustand["sperrzeit_rest_s"] = round(rest)

    # In jedem Zyklus mitfuehren, damit die Sperre auch dann in der API
    # sichtbar ist, wenn gerade kein Eingriff ansteht.
    anzahl_24h = dosierungen_24h()
    gesperrt = anzahl_24h >= MAX_DOSIERUNGEN_TAG
    zustand["dosierungen_24h"] = anzahl_24h
    zustand["dosierung_gesperrt"] = gesperrt

    obergrenze = SOLLWERT_PH + TOLERANZ_PH

    if ph <= obergrenze:
        return                                    # im Zielbereich, nur pH- verfuegbar

    if rest > 0:
        print(f"  [REGELUNG] pH {ph:.2f} zu hoch, Sperrzeit noch "
              f"{rest:.0f} s - kein Eingriff.")
        return

    if gesperrt:
        print(f"  [REGELUNG] Tagesgrenze erreicht "
              f"({anzahl_24h}/{MAX_DOSIERUNGEN_TAG} in 24 h) - Dosierung "
              "gesperrt, pH wird NICHT mehr korrigiert. System pruefen.")
        return

    print(f"  [REGELUNG] pH {ph:.2f} > {obergrenze:.2f} - dosiere pH-Minus.")
    dosiere()


# ==================================================================
#   6  LOGGING
# ==================================================================

def schreibe_log():
    zeile = {spalte: zustand.get(spalte) for spalte in CSV_SPALTEN}
    zeile["timestamp"] = zustand["timestamp"]
    neu = not os.path.isfile(LOG_FILE)
    try:
        with open(LOG_FILE, "a", newline="") as datei:
            schreiber = csv.DictWriter(datei, fieldnames=CSV_SPALTEN)
            if neu:
                schreiber.writeheader()
            schreiber.writerow(zeile)
    except OSError as fehler:
        print(f"  [FEHLER] Logdatei: {fehler}")


# ==================================================================
#   7  WEB-API
# ==================================================================

app = Flask(__name__)
CORS(app)


@app.route("/api/sensoren")
@app.route("/api/sensors")
def api_sensoren():
    return jsonify(zustand)


@app.route("/api/pumpe/test")
def api_pumpe_test():
    """Manueller Testlauf, z. B. fuer die Pumpenkennlinie.

    Aufruf: /api/pumpe/test?sekunden=5
    """
    try:
        sekunden = float(request.args.get("sekunden", 0))
    except ValueError:
        return jsonify({"fehler": "Parameter 'sekunden' ungueltig"}), 400

    if not 0 < sekunden <= PUMPE_MAX_EIN_S:
        return jsonify({
            "fehler": f"'sekunden' muss zwischen 0 und {PUMPE_MAX_EIN_S} liegen"
        }), 400

    gelaufen = pumpe_laufen_lassen(sekunden, "(manueller Test)")
    if gelaufen == 0.0:
        return jsonify({"fehler": "Pumpe belegt"}), 409
    return jsonify({"status": "ok", "sekunden": gelaufen})


@app.route("/api/pumpe/stopp")
def api_pumpe_stopp():
    """Nothalt - wirkt immer, unabhaengig vom Lock."""
    pumpe.off()
    zustand["pumpe"] = False
    return jsonify({"status": "gestoppt"})


def starte_api():
    thread = threading.Thread(
        target=lambda: app.run(host=API_HOST, port=API_PORT,
                               use_reloader=False, threaded=True),
        daemon=True,
    )
    thread.start()
    print(f"API laeuft auf http://{API_HOST}:{API_PORT}")


# ==================================================================
#   8  BETRIEBSARTEN
# ==================================================================

def kalibriermodus():
    """Gibt fortlaufend die Sensorspannung aus.

    Vorgehen
    --------
    1. Sensor mit destilliertem Wasser spuelen, vorsichtig abtupfen.
    2. In Pufferloesung pH 7,00 stellen, mindestens 2-3 Minuten warten,
       bis der Wert stabil steht. Spannung U7 und Wassertemperatur notieren.
    3. Spuelen, in Pufferloesung pH 4,01 stellen, erneut warten.
       Spannung U4 notieren.
    4. Berechnen:
           STEIGUNG        = (4.01 - 7.00) / (U4 - U7)
           ACHSENABSCHNITT = 7.00 - STEIGUNG * U7
    5. Pruefen: 1/|STEIGUNG| muss zwischen 0,050 und 0,059 V/pH liegen.
    6. Beide Werte oben eintragen, dann --nur-messen starten und
       gegen Puffer 7,00 verifizieren (Anzeige 7,0 +/- 0,1).
    """
    print(kalibriermodus.__doc__)
    print("=" * 62)
    print("KALIBRIERMODUS - Abbruch mit Strg+C\n")

    while _laeuft:
        spannung = lies_ph_spannung()
        temp = lies_wassertemperatur()
        if spannung is None:
            print("  Messung fehlgeschlagen")
        else:
            temp_text = f"{temp:.2f} °C" if temp is not None else "n/v"
            print(f"  U = {spannung:.4f} V     Roh = {ph_chan.value:6d}     "
                  f"T = {temp_text}")
        time.sleep(1)


def hauptschleife():
    print("=" * 62)
    print(f"Hydroponik-System gestartet - Betriebsart: {zustand['betriebsart']}")
    if regelung_aktiv:
        print(f"Sollwert pH {SOLLWERT_PH} +/- {TOLERANZ_PH}, "
              f"Eingriff ab {SOLLWERT_PH + TOLERANZ_PH:.1f}")
        print(f"Dosierzeit {DOSIERZEIT_S * SICHERHEITSFAKTOR:.1f} s, "
              f"Sperrzeit {SPERRZEIT_S} s")
    else:
        print("Dosierpumpe gesperrt (Messbetrieb)")
    print("=" * 62)

    letzter_log = 0.0

    while _laeuft:
        print("\n" + "-" * 62)

        wasser_temp = lies_wassertemperatur()
        ph, spannung = lies_ph(wasser_temp)
        luft_temp, luft_feuchte = lies_luftwerte()
        feucht = bool(feuchte_sensor.value)

        if ph is not None:
            print(f"  pH-Wert:          {ph:.2f}   ({spannung:.4f} V)")
        else:
            print("  pH-Wert:          ungueltig")

        if wasser_temp is not None:
            print(f"  Wassertemperatur: {wasser_temp:.2f} °C")
        if luft_temp is not None and luft_feuchte is not None:
            print(f"  Lufttemperatur:   {luft_temp:.1f} °C")
            print(f"  Luftfeuchte:      {luft_feuchte:.1f} %")
        print(f"  Kontaktsensor:    {'nass' if feucht else 'trocken'}")

        zustand.update({
            "ph":           ph,
            "ph_spannung":  round(spannung, 4) if spannung is not None else None,
            "wasser_temp":  wasser_temp,
            "luft_temp":    luft_temp,
            "luft_feuchte": luft_feuchte,
            "feuchtigkeit": feucht,
            "timestamp":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

        regele(ph)

        jetzt = time.monotonic()
        if jetzt - letzter_log >= LOG_INTERVALL_S:
            schreibe_log()
            letzter_log = jetzt

        time.sleep(MESSINTERVALL_S)


# ==================================================================
#   9  BEENDEN
# ==================================================================

def beenden(signalnummer=None, rahmen=None):
    global _laeuft
    _laeuft = False
    print("\nSystem wird beendet - Aktoren werden ausgeschaltet ...")
    try:
        pumpe.off()
    except Exception:
        pass
    try:
        dht.exit()
    except Exception:
        pass
    sys.exit(0)


signal.signal(signal.SIGINT, beenden)
signal.signal(signal.SIGTERM, beenden)


# ==================================================================
#   10  EINSTIEG
# ==================================================================

def main():
    global regelung_aktiv

    parser = argparse.ArgumentParser(description="Hydroponik-Steuerung")
    gruppe = parser.add_mutually_exclusive_group()
    gruppe.add_argument("--kalibrieren", action="store_true",
                        help="nur Sensorspannung ausgeben")
    gruppe.add_argument("--nur-messen", action="store_true",
                        help="Messbetrieb ohne Dosierung (Standard)")
    gruppe.add_argument("--regeln", action="store_true",
                        help="Messbetrieb mit aktiver pH-Regelung")
    argumente = parser.parse_args()

    try:
        if argumente.kalibrieren:
            zustand["betriebsart"] = "kalibrierung"
            kalibriermodus()
            return

        if STEIGUNG is None or ACHSENABSCHNITT is None:
            print("ABBRUCH: Kalibrierkonstanten STEIGUNG und ACHSENABSCHNITT "
                  "sind nicht gesetzt.\n"
                  "Zuerst 'python3 hydroponik.py --kalibrieren' ausfuehren "
                  "und die Werte im Kopf der Datei eintragen.")
            sys.exit(1)

        steilheit = 1.0 / abs(STEIGUNG)
        if not 0.045 <= steilheit <= 0.062:
            print(f"ABBRUCH: Kalibriersteilheit {steilheit * 1000:.1f} mV/pH "
                  "liegt ausserhalb des plausiblen Bereichs (50-59 mV/pH).\n"
                  "Elektrode, Pufferloesungen und Verdrahtung pruefen.")
            sys.exit(1)

        regelung_aktiv = bool(argumente.regeln)
        zustand["betriebsart"] = "regelung" if regelung_aktiv else "messbetrieb"

        starte_api()
        hauptschleife()

    finally:
        try:
            pumpe.off()
        except Exception:
            pass


if __name__ == "__main__":
    main()
