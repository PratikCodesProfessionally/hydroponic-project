"""
Hydroponik pH-Regelung — überarbeitete Fassung von ganzerCode.py.

Dies ist das Programm, das auf dem Raspberry Pi läuft (seit 17.09.2026).
Die Vorgängerfassung liegt unter iot/archiv/ganzerCode.py.

Gegenüber ganzerCode.py umgesetzt (Bezeichner wie in der Projektdokumentation,
Kapitel 3/4):

  a) Kalibrierte Umrechnung (Abschnitt 4.4) statt Herstellerformel + K=8,23;
     Werte werden aus kalibrierung.json geladen (siehe kalibrieren.py),
     damit eine neue Kalibrierung dieses Skript nicht verändert
  c) Regelentscheidung auf Mittelwert der Messfenster-Werte statt Einzelwert
  e) Zeitbegrenzte, mit dem Node-Server kompatible Pumpen-Endpunkte
     (/api/pumpe/test, /api/pumpe/stopp); alter /api/pump/<action> entfernt
  f) Plausibilitätsprüfung (3,0–9,5 pH) und try/except um die ADC-Abfrage,
     damit ein I2C-Fehler nicht das ganze Programm beendet (R-07, S-02)
  h) Flask bindet nur noch auf die Ethernet-Adresse des Einplatinenrechners
  k) Totband ±0,2 pH (PH_TOLERANZ) statt scharfer Schwelle
  n) Kontrollmessung nach 5 s entfällt; die Wirkung wird stattdessen zu
     Beginn des nächsten Messfensters bewertet (~5 min später statt 5 s,
     oberhalb der Elektroden-Ansprechzeit von <2 min)
  o) Temperaturkompensation der Steilheit (Gleichung 3.2)
  p) Log-Intervall ≤ 30 s (jetzt: jede Einzelmessung, alle 10 s)
  q) Pumpenzustand wird vor dem Logging korrekt erfasst
  r) Dosierzeitpunkt und -menge werden protokolliert (dosierungen_log.csv)

  Zusätzlich ergänzt, weil vom Dashboard bereits erwartet (siehe server.js):
  Dosierzähler pro Stunde/Tag, Sperrzeit-Anzeige, Ausfallalarm nach
  wirkungslosen Dosierungen (R-05, R-06).

Änderungen vom 18.09.2026 gegenüber dem Stand vom 17.09. (Abgleich mit
server.js, public/app.js und tools/plot_messreihe.py):

  - ph_spannung wird in VOLT gemeldet und geloggt (vorher mV). Dashboard,
    CSV-Export und Kennlinien-Auswertung rechnen durchgehend in Volt.
  - letzte_dosierung ist ein Zeitstempel-String (vorher Objekt, das im
    Dashboard als "[object Object]" erschien). Sekunden und ml stehen im
    Dosierprotokoll.
  - Not-Aus (/api/pumpe/stopp) holt sich NICHT mehr den Pumpen-Lock. Vorher
    wartete er, bis die laufende Dosierung von selbst endete, und war damit
    genau dann wirkungslos, wenn er gebraucht wurde.
  - Betriebsart --nur-messen: keine automatische Dosierung, manueller
    Testlauf über das Dashboard bleibt möglich. Ohne Flag: "regelung".
    (hydroponik.service startet bewusst mit --nur-messen.)
  - Log-, Dosierprotokoll- und Kalibrierdatei liegen neben diesem Skript,
    unabhängig vom Arbeitsverzeichnis. kalibrieren.py schreibt an dieselbe
    Stelle; vorher las dieses Skript relativ zum Aufrufort und fand die
    Kalibrierung nicht, wenn es aus dem Projektordner gestartet wurde.
  - CSV-Dateien mit abweichender Kopfzeile (z. B. altes 7-spaltiges Log von
    ganzerCode.py) werden beim Start mit Zeitstempel umbenannt statt
    fortgeschrieben.
  - Schlägt das Binden der API an API_HOST fehl (Adresse beim Start noch
    nicht auf eth0), wird alle 5 s erneut versucht statt still aufzugeben.

Bewusst NICHT umgesetzt, weil sie Messungen statt Codeänderungen brauchen:
  b) Ursache des Messrauschens (Abschnitt 5.1)
  g/j/m) Sperrzeit und Dosiermenge aus Sprungantwort (Abschnitt 4.5) —
         SPERRZEIT_S unten ist ein Platzhalter
  s) Wägeversuch mit Wiederholungen — FOERDERRATE_ML_S ist eine grobe,
     einfach gemessene Schätzung, keine belastbare Kennlinie
  u) Regelgüte im Dauerbetrieb

=== ANNAHMEN, die noch zu bestätigen sind (Zeilen mit "ANNAHME:") ===
  1) SPERRZEIT_S = 600 s (10 min) als Platzhalter bis Abschnitt 4.5 vorliegt.
  2) KEIN_EFFEKT_SCHWELLE = 0.1 pH als Schwelle für "wirkungslose" Dosierung —
     liegt unterhalb des bekannten Messrauschens (0,16–0,31 pH) und ist damit
     selbst noch unsicher; siehe Abschnitt 5.1.
  3) Manuelle Testdosierungen über /api/pumpe/test zählen auf dasselbe
     Tageslimit (MAX_ML_PRO_TAG) wie automatische Dosierungen, aber NICHT auf
     die stündliche Dosenzahl und die Sperrzeit der Regelung.
  4) max_dosierungen_tag im API-Feld ist aus der Stundengrenze abgeleitet
     (MAX_DOSEN_PRO_STUNDE * 24) und keine eigenständig festgelegte Zahl.

Aufruf:
    python3 iot/hydroponik.py --nur-messen   # messen, loggen, keine automatische Dosierung
    python3 iot/hydroponik.py                # mit aktiver pH-Regelung
"""

import time
import os
import json
import csv
import signal
import sys
import threading
from datetime import datetime

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_dht
from gpiozero import DigitalInputDevice, DigitalOutputDevice
from flask import Flask, jsonify, request
from flask_cors import CORS

# ============================
#   BETRIEBSART
# ============================
NUR_MESSEN  = "--nur-messen" in sys.argv
BETRIEBSART = "messbetrieb" if NUR_MESSEN else "regelung"

# ============================
#   PIN-ZUWEISUNGEN / DATEIEN
# ============================
DHT_PIN        = board.D17
FEUCHTE_PIN    = 27
PUMP_PIN       = 5
W1_DEVICE_PATH = "/sys/bus/w1/devices/"

# Alle Dateien liegen neben diesem Skript, unabhängig vom Arbeitsverzeichnis.
SKRIPT_VERZEICHNIS = os.path.dirname(os.path.abspath(__file__))
LOG_FILE        = os.getenv("HYDRO_LOG_FILE",
                            os.path.join(SKRIPT_VERZEICHNIS, "hydroponik_log.csv"))
DOSIER_LOG_FILE = os.path.join(SKRIPT_VERZEICHNIS, "dosierungen_log.csv")
KALIBRIER_DATEI = os.path.join(SKRIPT_VERZEICHNIS, "kalibrierung.json")

# Auf welcher Adresse der Einplatinenrechner die API bereitstellt (Punkt h).
# 192.168.10.1 = feste Ethernet-Adresse zum Anzeigerechner (Abschnitt 3.7.2).
# WICHTIG: Der Node-Server muss PI_API_BASE_URL=http://192.168.10.1:5000
# gesetzt haben, sonst ist der Pi über das WLAN nicht erreichbar.
# Zum Testen ohne Kabel:  HYDRO_API_HOST=0.0.0.0 python3 iot/hydroponik.py
API_HOST = os.getenv("HYDRO_API_HOST", "192.168.10.1")
API_PORT = 5000

# ============================
#   SENSOR & AKTOR SETUP
# ============================
dht            = adafruit_dht.DHT11(DHT_PIN, use_pulseio=False)
feuchte_sensor = DigitalInputDevice(FEUCHTE_PIN, pull_up=False)
pumpe          = DigitalOutputDevice(PUMP_PIN)
pumpe_lock     = threading.Lock()  # schützt gegen gleichzeitigen Zugriff
                                    # von Hauptschleife und Flask-Thread

# ============================
#   ADS1115 (pH-Sensor)
# ============================
i2c      = busio.I2C(board.SCL, board.SDA)
ads      = ADS.ADS1115(i2c, address=0x48)
ads.gain = 1
ph_chan  = AnalogIn(ads, 0)
ADC_MAX  = 32767      # Vollausschlag ADS1115 bei gain=1 -> 4,096 V

# ============================
#   KALIBRIERUNG (Abschnitt 4.4) — Punkt a)
# ============================
# Werte kommen aus kalibrierung.json (siehe kalibrieren.py), nicht mehr fest
# im Code. So löst eine neue Kalibrierung (z. B. nach dem Wässern der
# Elektrode, Punkt t) nie eine Änderung an diesem Skript aus.


def lade_kalibrierung() -> dict:
    if not os.path.isfile(KALIBRIER_DATEI):
        raise RuntimeError(
            f"Keine Kalibrierung gefunden ({KALIBRIER_DATEI}). "
            f"Bitte zuerst kalibrieren.py ausführen."
        )
    with open(KALIBRIER_DATEI, "r") as f:
        daten = json.load(f)
    for feld in ("u0_mv", "steilheit_mv_pro_ph", "t_kal_c"):
        if feld not in daten:
            raise RuntimeError(f"{KALIBRIER_DATEI} ist unvollständig (Feld '{feld}' fehlt).")
    print(f"Kalibrierung geladen (vom {daten.get('zeitstempel', 'unbekannt')}): "
          f"U0={daten['u0_mv']} mV, S={daten['steilheit_mv_pro_ph']} mV/pH, "
          f"T_kal={daten['t_kal_c']} °C, "
          f"{daten.get('steilheit_prozent_theorie', '?')}% der theor. Steilheit")
    return daten


_kalibrierung = lade_kalibrierung()
U0_KAL        = _kalibrierung["u0_mv"]
STEILHEIT_KAL = _kalibrierung["steilheit_mv_pro_ph"]
T_KAL         = _kalibrierung["t_kal_c"]

# ============================
#   pH-REGELUNG
# ============================
PH_SOLL       = 5.8     # realer Zielwert, R-01 (vorher: Anzeige 6,0 unkalibriert)
PH_TOLERANZ   = 0.2     # Totband, R-02 — Punkt k). Dosiert wird nur, wenn
                         # ph_mittel > PH_SOLL + PH_TOLERANZ (einseitig, da nur
                         # pH-Minus verfügbar ist)
PH_PLAUSIBEL_MIN = 3.0  # Punkt f)
PH_PLAUSIBEL_MAX = 9.5
PH_MAX_ABW    = 2.0     # ab dieser Abweichung wird maximal lange gepumpt
PH_MESSZYKLEN = 30      # pH-Messungen pro Durchlauf der Hauptschleife
PH_MESSPAUSE  = 10      # Sekunden zwischen zwei pH-Messungen
PUMP_MIN_S    = 2       # kürzeste Pumpdauer (provisorisch, siehe Docstring g/j/m)
PUMP_MAX_S    = 5       # längste Pumpdauer (provisorisch)

# ============================
#   SICHERHEITSGRENZEN (bereits festgelegte Werte übernommen)
# ============================
PUMPE_MAX_EIN_S     = 10    # harte Obergrenze je Einschaltvorgang (S-04);
                             # Name bewusst wie im Kommentar von server.js
FOERDERRATE_ML_S    = 1.7   # ml/s, aus Einzelmessung (Abschnitt 5.2, Punkt s offen)
MAX_ML_PRO_DOSIS    = 20    # R-04
MAX_DOSEN_PRO_STUNDE = 6    # R-05 (Ersatz, bis Sperrzeit aus 4.5 feststeht)
MAX_ML_PRO_TAG      = 150   # R-06
SPERRZEIT_S         = 600   # ANNAHME 1: Platzhalter für R-05, siehe Docstring
KEIN_EFFEKT_SCHWELLE = 0.1  # ANNAHME 2: siehe Docstring
KEIN_EFFEKT_ALARM_NACH = 3  # Anzahl wirkungsloser Dosierungen in Folge

# ============================
#   GLOBALER ZUSTAND
# ============================
sensor_data = {
    "luft_temp":    None,
    "luft_feuchte": None,
    "wasser_temp":  None,
    "ph":           None,
    "ph_spannung":  None,     # in VOLT (Dashboard, CSV-Export und Auswertung rechnen in V)
    "feuchtigkeit": None,
    "pumpe":        False,
    "betriebsart":  BETRIEBSART,
    "sollwert_ph":  PH_SOLL,
    "toleranz_ph":  PH_TOLERANZ,
    "dosierungen_gesamt":   0,
    "dosierungen_24h":      0,
    "max_dosierungen_tag":  MAX_DOSEN_PRO_STUNDE * 24,  # ANNAHME 4
    "dosierung_gesperrt":   False,
    "sperrzeit_rest_s":     0.0,
    "letzte_dosierung":     None,   # Zeitstempel-String, wie vom Dashboard erwartet
    "timestamp":    None
}

# Dosierhistorie im Speicher: [{"zeit": float(epoch), "sekunden": float,
#   "ml": float, "ph_vor": float, "ausgewertet": bool, "quelle": str}, ...]
dosen_liste = []
regelzustand = {
    "gesperrt": False,
    "wirkungslos_counter": 0,
}


def dosen_in_letzten(sekunden: float) -> list:
    grenze = time.time() - sekunden
    return [d for d in dosen_liste if d["zeit"] >= grenze]


def ml_in_letzten(sekunden: float) -> float:
    return sum(d["ml"] for d in dosen_in_letzten(sekunden))


def status_snapshot() -> dict:
    """Berechnet die Zähler-/Sperrzeit-Felder für /api/sensors neu."""
    jetzt = time.time()
    letzte = dosen_liste[-1] if dosen_liste else None
    sperrzeit_rest = 0.0
    if letzte is not None:
        sperrzeit_rest = max(0.0, SPERRZEIT_S - (jetzt - letzte["zeit"]))
    return {
        "dosierungen_gesamt":  len(dosen_liste),
        "dosierungen_24h":     len(dosen_in_letzten(86400)),
        "dosierung_gesperrt":  regelzustand["gesperrt"],
        "sperrzeit_rest_s":    round(sperrzeit_rest, 1),
        # Nur der Zeitpunkt: app.js setzt den Wert direkt als Text ein.
        # Dauer und Menge stehen in dosierungen_log.csv.
        "letzte_dosierung": (
            datetime.fromtimestamp(letzte["zeit"]).strftime("%Y-%m-%d %H:%M:%S")
            if letzte is not None else None
        ),
    }


def update_sensor_data(luft_temp, luft_feuchte, w_temp, ph, ph_spannung_mv, feucht):
    """Globalen Zustand an einer einzigen Stelle aktualisieren (Punkt q):
    pumpe.is_active wird HIER gelesen, also im selben Moment wie der Rest —
    nicht erst nach einem späteren pumpe.off().

    ph_spannung_mv kommt in mV aus read_ph() (die Kalibrierung rechnet in mV),
    nach außen geht der Wert in Volt."""
    sensor_data.update({
        "luft_temp":    luft_temp,
        "luft_feuchte": luft_feuchte,
        "wasser_temp":  w_temp,
        "ph":           ph,
        "ph_spannung":  round(ph_spannung_mv / 1000.0, 4) if ph_spannung_mv is not None else None,
        "feuchtigkeit": feucht,
        "pumpe":        pumpe.is_active,
        "timestamp":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    sensor_data.update(status_snapshot())


# ============================
#   FLASK API
# ============================
app = Flask(__name__)
CORS(app)


@app.route("/api/sensors")
@app.route("/api/sensoren")
def get_sensors():
    return jsonify(sensor_data)


def _dosierung_ausfuehren(sekunden: float, quelle: str) -> dict:
    """Führt eine zeitbegrenzte Dosierung aus (Punkt e) und protokolliert sie
    (Punkt r). Wird sowohl von der Regelung als auch von /api/pumpe/test
    genutzt, damit es nur eine Stelle gibt, die tatsächlich pumpe.on() ruft."""
    sekunden = min(max(sekunden, 0.0), PUMPE_MAX_EIN_S)
    ml = sekunden * FOERDERRATE_ML_S
    if ml > MAX_ML_PRO_DOSIS:
        ml = MAX_ML_PRO_DOSIS
        sekunden = ml / FOERDERRATE_ML_S

    ph_vor = sensor_data.get("ph")
    with pumpe_lock:
        try:
            pumpe.on()
            time.sleep(sekunden)
        finally:
            pumpe.off()

    eintrag = {
        "zeit": time.time(),
        "sekunden": round(sekunden, 2),
        "ml": round(ml, 2),
        "ph_vor": ph_vor,
        "ausgewertet": False,
        "quelle": quelle,
    }
    dosen_liste.append(eintrag)
    log_dosierung(eintrag)
    return eintrag


@app.route("/api/pumpe/test")
def pumpe_test():
    """Vom Node-Server aufgerufen als GET /api/pumpe/test?sekunden=N.
    Antwortet laut Vorgabe erst NACH Ablauf der Dosierzeit (blockierend)."""
    try:
        sekunden = float(request.args.get("sekunden", 2))
    except (TypeError, ValueError):
        return jsonify({"fehler": "Parameter 'sekunden' ist keine Zahl"}), 400
    if not 0 < sekunden <= PUMPE_MAX_EIN_S:
        return jsonify({"fehler": f"'sekunden' muss zwischen 0 und {PUMPE_MAX_EIN_S} liegen"}), 400

    # ANNAHME 3: manuelle Tests zählen auf das Tageslimit, nicht auf
    # Stundenzahl/Sperrzeit der automatischen Regelung.
    if regelzustand["gesperrt"]:
        return jsonify({"fehler": "Dosierung gesperrt (Ausfallalarm, siehe Log)"}), 423
    if ml_in_letzten(86400) >= MAX_ML_PRO_TAG:
        return jsonify({"fehler": f"Tageslimit von {MAX_ML_PRO_TAG} ml erreicht"}), 423
    if pumpe_lock.locked():
        return jsonify({"fehler": "Pumpe läuft bereits"}), 409

    eintrag = _dosierung_ausfuehren(sekunden, quelle="manuell")
    sensor_data.update(status_snapshot())
    return jsonify({"status": "ok", **eintrag})


@app.route("/api/pumpe/stopp")
def pumpe_stopp():
    """Vom Node-Server aufgerufen als GET /api/pumpe/stopp (Not-Aus).

    BEWUSST OHNE pumpe_lock: Während einer Dosierung hält
    _dosierung_ausfuehren den Lock bis zum Ende des Laufs. Mit Lock würde der
    Not-Aus warten, bis die Pumpe ohnehin aus ist - und wäre damit genau dann
    wirkungslos, wenn er gebraucht wird. Das nachfolgende pumpe.off() im
    finally-Block der Dosierung ist unschädlich."""
    pumpe.off()
    sensor_data["pumpe"] = False
    return jsonify({"status": "gestoppt", "pumpe": pumpe.is_active})


def api_thread():
    """Flask in eigenem Thread. Ist API_HOST beim Start noch nicht auf eth0
    gesetzt, scheitert das Binden mit 'Cannot assign requested address'.
    Statt still aufzugeben (die Hauptschleife liefe dann ohne API weiter),
    wird alle 5 s erneut versucht."""
    while True:
        try:
            app.run(host=API_HOST, port=API_PORT, use_reloader=False, threaded=True)
            return
        except OSError as e:
            print(f"API konnte nicht an {API_HOST}:{API_PORT} binden ({e}) - "
                  f"neuer Versuch in 5 s. Ist die Adresse auf eth0 gesetzt?")
            time.sleep(5)


flask_thread = threading.Thread(target=api_thread, daemon=True)
flask_thread.start()


# ============================
#   LOGGING
# ============================
def _csv_kopf_pruefen(pfad: str, spalten: list):
    """Passt die Kopfzeile einer vorhandenen Datei nicht zu den aktuellen
    Spalten (z. B. altes 7-spaltiges Log von ganzerCode.py), wird die Datei
    mit Zeitstempel umbenannt, statt sie mit fremden Zeilen fortzuschreiben."""
    if not os.path.isfile(pfad):
        return
    try:
        with open(pfad, "r", newline="") as f:
            kopf = next(csv.reader(f), [])
    except OSError:
        return
    if kopf and kopf != list(spalten):
        neu = f"{pfad}.{datetime.now().strftime('%Y%m%d-%H%M%S')}.alt"
        os.rename(pfad, neu)
        print(f"Kopfzeile von {os.path.basename(pfad)} passt nicht - "
              f"alte Datei umbenannt nach {os.path.basename(neu)}")


def log_data(data: dict):
    """Schreibt eine Messzeile. Wird pro Einzelmessung (alle 10 s)
    aufgerufen statt einmal pro 5-Minuten-Fenster — Punkt p), erfüllt S-01
    (Intervall ≤ 30 s)."""
    spalten = list(data.keys())
    _csv_kopf_pruefen(LOG_FILE, spalten)
    file_exists = os.path.isfile(LOG_FILE)
    try:
        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=spalten)
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
    except OSError as e:
        print(f"Logdatei: {e}")


def log_dosierung(eintrag: dict):
    """Eigenes Protokoll für Dosierzeitpunkt und -menge — Punkt r). Ohne diese
    Angaben lässt sich die Wirkung einer Dosierung nicht auswerten (Abschnitt
    5.3 / Sprungantwort in 4.5)."""
    zeile = {
        "timestamp": datetime.fromtimestamp(eintrag["zeit"]).strftime("%Y-%m-%d %H:%M:%S"),
        "sekunden":  eintrag["sekunden"],
        "ml":        eintrag["ml"],
        "ph_vor":    eintrag["ph_vor"],
        "quelle":    eintrag["quelle"],
    }
    _csv_kopf_pruefen(DOSIER_LOG_FILE, list(zeile.keys()))
    file_exists = os.path.isfile(DOSIER_LOG_FILE)
    try:
        with open(DOSIER_LOG_FILE, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=zeile.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(zeile)
    except OSError as e:
        print(f"Dosierprotokoll: {e}")


# ============================
#   DS18B20 (Wassertemperatur)
# ============================
def read_water_temp():
    try:
        device_folder = [d for d in os.listdir(W1_DEVICE_PATH) if d.startswith("28-")][0]
        device_file   = f"{W1_DEVICE_PATH}{device_folder}/w1_slave"
        with open(device_file, "r") as f:
            lines = f.readlines()
        if "YES" not in lines[0]:
            return None
        return float(lines[1].split("t=")[-1]) / 1000.0
    except Exception:
        return None


# ============================
#   pH-MESSUNG — Punkte a), f), o)
# ============================
def read_ph(wasser_temp=None):
    """Liest den pH-Wert kalibriert (Abschnitt 4.4) mit Temperaturkompensation
    der Steilheit (Gleichung 3.2). Filterung wie bisher: 10 Einzelwerte
    sortiert, Mittelwert der mittleren 6 gegen Ausreißer.

    Gibt (ph, spannung_mv) zurück, oder (None, None) bei einem I2C-Fehler
    bzw. (None, spannung_mv) wenn der Wert außerhalb des Plausibilitäts-
    bereichs liegt (Punkt f) — die Hauptschleife läuft in beiden Fällen
    weiter, es wird nur diese eine Messung verworfen (R-07, S-02)."""
    try:
        buf = []
        for _ in range(10):
            buf.append(ph_chan.value)
            time.sleep(0.01)
    except OSError as e:
        print(f"pH-Sensor: I2C-Fehler beim Lesen ({e})")
        return None, None

    buf.sort()
    avg_value = sum(buf[2:8]) / 6
    spannung_mv = avg_value * 4.096 / ADC_MAX * 1000  # ADS1115, gain=1, Vollausschlag 4,096 V

    steilheit = STEILHEIT_KAL
    if wasser_temp is not None:
        steilheit = STEILHEIT_KAL * (273.15 + wasser_temp) / (273.15 + T_KAL)  # Gleichung 3.2

    ph = 7 + (U0_KAL - spannung_mv) / steilheit
    ph = round(ph, 2)
    spannung_mv = round(spannung_mv, 1)

    if not (PH_PLAUSIBEL_MIN <= ph <= PH_PLAUSIBEL_MAX):
        print(f"pH-Wert {ph} außerhalb des Plausibilitätsbereichs "
              f"({PH_PLAUSIBEL_MIN}–{PH_PLAUSIBEL_MAX}) — Messung verworfen")
        return None, spannung_mv

    return ph, spannung_mv


def berechne_pumpdauer(ph_wert: float) -> float:
    """Pumpdauer in Sekunden (PUMP_MIN_S..PUMP_MAX_S), abhängig vom Abstand
    zum Sollwert. Provisorisch (siehe Docstring g/j/m) — sobald die
    Streckenverstärkung K_S aus der Sprungantwort (Abschnitt 4.5) vorliegt,
    ersetzt die dokumentierte Formel V = (ph_ist - PH_SOLL) / K_S * 0,5
    diese lineare Interpolation."""
    abweichung = abs(ph_wert - PH_SOLL)
    anteil     = min(abweichung / PH_MAX_ABW, 1.0)
    return PUMP_MIN_S + anteil * (PUMP_MAX_S - PUMP_MIN_S)


def bewerte_letzte_dosierung(ph_mittel_aktuell: float):
    """Vergleicht den pH-Mittelwert des aktuellen Fensters mit dem Wert vor
    der letzten (noch nicht bewerteten) Dosierung — Ersatz für die bisherige,
    zu frühe 5-s-Kontrollmessung (Punkt n). Löst nach
    KEIN_EFFEKT_ALARM_NACH wirkungslosen Dosierungen in Folge eine Sperre
    aus (R-05/R-06-Absicherung)."""
    if not dosen_liste:
        return
    letzte = dosen_liste[-1]
    if letzte["ausgewertet"] or letzte["ph_vor"] is None:
        return

    wirkung = letzte["ph_vor"] - ph_mittel_aktuell
    letzte["ausgewertet"] = True

    if wirkung < KEIN_EFFEKT_SCHWELLE:
        regelzustand["wirkungslos_counter"] += 1
        print(f"Dosierung ohne erkennbare Wirkung ({wirkung:+.2f} pH), "
              f"Zähler: {regelzustand['wirkungslos_counter']}/{KEIN_EFFEKT_ALARM_NACH}")
    else:
        regelzustand["wirkungslos_counter"] = 0

    if regelzustand["wirkungslos_counter"] >= KEIN_EFFEKT_ALARM_NACH:
        regelzustand["gesperrt"] = True
        print("ALARM: Dosierung gesperrt — mehrere Dosierungen in Folge ohne "
              "erkennbare Wirkung. Manuelle Prüfung erforderlich "
              "(Neustart des Programms hebt die Sperre auf).")


def darf_automatisch_dosieren() -> bool:
    if NUR_MESSEN or regelzustand["gesperrt"]:
        return False
    letzte = dosen_liste[-1] if dosen_liste else None
    if letzte is not None and (time.time() - letzte["zeit"]) < SPERRZEIT_S:
        return False
    if len(dosen_in_letzten(3600)) >= MAX_DOSEN_PRO_STUNDE:
        return False
    if ml_in_letzten(86400) >= MAX_ML_PRO_TAG:
        return False
    return True


# ============================
#   SAUBERES BEENDEN
# ============================
def cleanup(sig, frame):
    print("\nSystem wird beendet – Aktoren werden ausgeschaltet...")
    pumpe.off()          # ohne Lock, aus demselben Grund wie beim Not-Aus
    try:
        dht.exit()
    except Exception:
        pass
    sys.exit(0)


signal.signal(signal.SIGINT,  cleanup)
signal.signal(signal.SIGTERM, cleanup)

# ============================
#   HAUPTSCHLEIFE
# ============================
print("=" * 62)
print(f"Hydroponik-System gestartet - Betriebsart: {BETRIEBSART}")
if NUR_MESSEN:
    print("Keine automatische Dosierung (manueller Testlauf über das Dashboard möglich)")
else:
    print(f"Sollwert pH {PH_SOLL} ± {PH_TOLERANZ}, Eingriff ab {PH_SOLL + PH_TOLERANZ:.1f}")
print(f"API läuft auf http://{API_HOST}:{API_PORT}")
print(f"Log: {LOG_FILE}")
print("=" * 62)

while True:
    print("\n==============================")

    # --- Lufttemperatur & Luftfeuchte (DHT11) ---
    luft_temp    = None
    luft_feuchte = None
    try:
        luft_temp    = dht.temperature
        luft_feuchte = dht.humidity
        if luft_temp is not None and luft_feuchte is not None:
            print(f"Lufttemperatur:  {luft_temp:.1f} °C")
            print(f"Luftfeuchte:     {luft_feuchte:.1f} %")
        else:
            print("DHT11: keine Daten")
    except Exception as e:
        print(f"DHT11 Fehler: {e}")
        try:
            dht.exit()
            time.sleep(1)
            dht = adafruit_dht.DHT11(DHT_PIN, use_pulseio=False)
        except Exception:
            pass

    # --- Bodenfeuchtesensor ---
    feucht = feuchte_sensor.value
    print("Feuchtigkeit: erkannt" if feucht else "Feuchtigkeit: trocken")

    # --- Wassertemperatur (DS18B20) ---
    w_temp = read_water_temp()
    if w_temp is not None:
        print(f"Wassertemperatur: {w_temp:.2f} °C")
    else:
        print("Wassertemperatur: Fehler beim Lesen")

    # --- pH-Messfenster: PH_MESSZYKLEN Einzelmessungen, jede sofort
    #     geloggt (Punkt p) und aktualisiert; Entscheidung anschließend
    #     auf dem Mittelwert (Punkt c) ---
    ph_werte = []
    for _ in range(PH_MESSZYKLEN):
        ph_wert, ph_spannung = read_ph(w_temp)
        if ph_wert is not None:
            ph_werte.append(ph_wert)
            print(f"pH-Wert: {ph_wert:.2f}  (U = {ph_spannung:.1f} mV)")
        else:
            print("pH-Wert: ungültig/verworfen")

        update_sensor_data(luft_temp, luft_feuchte, w_temp, ph_wert, ph_spannung, feucht)
        log_data(sensor_data)  # Punkt p): Log-Intervall jetzt PH_MESSPAUSE (10 s)
        time.sleep(PH_MESSPAUSE)

    if not ph_werte:
        print("Kein gültiger pH-Wert in diesem Messfenster — keine Regelentscheidung möglich.")
        time.sleep(2)
        continue

    ph_mittel = sum(ph_werte) / len(ph_werte)
    print(f"pH-Mittelwert des Fensters: {ph_mittel:.2f} (n={len(ph_werte)}/{PH_MESSZYKLEN})")

    # --- Wirkung der letzten Dosierung bewerten (ersetzt die alte 5-s-Kontrollmessung) ---
    bewerte_letzte_dosierung(ph_mittel)

    # --- pH-Regelung: Totband (Punkt k) + Sicherheitsgrenzen ---
    if ph_mittel > PH_SOLL + PH_TOLERANZ:
        if darf_automatisch_dosieren():
            sekunden = berechne_pumpdauer(ph_mittel)
            print(f"pH zu hoch (Mittel {ph_mittel:.2f}) → Pumpe EIN für {sekunden:.1f} s (pH-Minus)")
            eintrag = _dosierung_ausfuehren(sekunden, quelle="automatik")
            print(f"Dosierung: {eintrag['sekunden']} s ≈ {eintrag['ml']} ml")
        else:
            if NUR_MESSEN:
                grund = "Messbetrieb (--nur-messen)"
            elif regelzustand["gesperrt"]:
                grund = "gesperrt (Ausfallalarm)"
            else:
                grund = "Sperrzeit/Stunden- oder Tageslimit noch aktiv"
            print(f"pH zu hoch, aber keine Dosierung: {grund}")

    time.sleep(2)
