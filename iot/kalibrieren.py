"""
Kalibrierung der pH-Messkette — eigenständiges Skript, getrennt von
hydroponik.py, damit eine neue Kalibrierung (z. B. nach dem Wässern der
Elektrode, Punkt t) den Regelungscode nicht verändert.

Verfahren (Abschnitt 4.4.1 der Dokumentation):
  - Zweipunktkalibrierung mit den Puffern pH 4,01 und 7,00 -> Steilheit
    und Nullpunkt (Gleichung 4.5/4.6). Der Sollwert 5,8 liegt zwischen
    diesen beiden Stützstellen, es wird also interpoliert, nicht
    extrapoliert.
  - Puffer pH 10,01 dient NUR der Verifikation (Gleichung 4.7), fließt
    nicht in Steilheit/Nullpunkt ein — oberhalb von pH 7 verfälscht der
    Alkalifehler der Glaselektrode sonst die Steilheitsberechnung.

Neu gegenüber der bisherigen Kalibrierung: Die Temperatur wird mit dem
DS18B20 direkt in der jeweiligen Pufferlösung gemessen (Sensor beim
Kalibrieren mit in den Becher halten), statt pauschal Raumtemperatur
anzunehmen (bisherige Einschränkung, siehe Abschnitt 4.4).

Ergebnis wird nach kalibrierung.json (neben diesem Skript) geschrieben und
von hydroponik.py beim Start eingelesen.

Aufruf:
    python3 iot/kalibrieren.py
"""

import json
import os
import statistics
import threading
import time
from datetime import datetime

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

SKRIPT_VERZEICHNIS = os.path.dirname(os.path.abspath(__file__))

W1_DEVICE_PATH   = "/sys/bus/w1/devices/"
KALIBRIER_DATEI  = os.path.join(SKRIPT_VERZEICHNIS, "kalibrierung.json")
ADC_MAX          = 32767   # Vollausschlag ADS1115 bei gain=1 -> 4,096 V
S_THEOR_25C      = 59.16   # mV/pH, Nernst-Steilheit bei 25 °C (Gleichung 2.3)
M06_GRENZE_PROZENT = 85.0  # Brauchbarkeitsgrenze aus M-06

# Messabstand während des Einpendelns. Es wird nicht automatisch anhand
# einer Schwankungsbreite gestoppt, sondern erst, wenn per Enter bestätigt
# wird, dass der angezeigte Wert stabil aussieht.
MESSABSTAND_S = 15

i2c     = busio.I2C(board.SCL, board.SDA)
ads     = ADS.ADS1115(i2c, address=0x48)
ads.gain = 1
ph_chan = AnalogIn(ads, 0)


def read_water_temp():
    """Identisch zu hydroponik.py — hier bewusst dupliziert, damit dieses
    Skript unabhängig läuft und nicht versehentlich die Hauptschleife von
    hydroponik.py mit importiert."""
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


def einzelmessung_mv() -> float:
    """Eine gefilterte Spannungsmessung: 10 Rohwerte, sortiert, Mittelwert
    der mittleren 6 — dieselbe Filterung wie in read_ph() (hydroponik.py)."""
    buf = []
    for _ in range(10):
        buf.append(ph_chan.value)
        time.sleep(0.01)
    buf.sort()
    avg_value = sum(buf[2:8]) / 6
    return avg_value * 4.096 / ADC_MAX * 1000


def messe_puffer(bezeichnung: str) -> tuple:
    """Fragt den Puffer ab und misst fortlaufend alle MESSABSTAND_S Sekunden.
    Jede Zwischenmessung wird mit Zeitstempel, Spannung, Temperatur und
    Differenz zur vorherigen Messung ausgegeben, damit das Einpendeln am
    Bildschirm sichtbar ist. Es wird so lange weitergemessen, bis die
    Bedienperson per Enter bestätigt, dass der zuletzt angezeigte Wert
    stabil ist — es gibt keinen automatischen Abbruch nach einer festen
    Anzahl Messungen. Gibt (spannung_mv, temperatur_c) der zuletzt vor der
    Bestätigung angezeigten Messung zurück."""
    input(f"\nElektrode UND Temperatursensor in Puffer {bezeichnung} geben, "
          f"dann Enter drücken, um mit der Messung zu beginnen ...")

    bestaetigt = threading.Event()

    def warte_auf_enter():
        input("  (Enter drücken, sobald der Wert stabil aussieht — die "
              "Messung läuft bis dahin weiter)\n")
        bestaetigt.set()

    threading.Thread(target=warte_auf_enter, daemon=True).start()

    letzte_spannung = None
    letzte_temperatur = None
    vorherige_spannung = None
    start = time.time()

    while True:
        u = einzelmessung_mv()
        t = read_water_temp()

        vergangen = time.time() - start
        zeile = f"  t={vergangen:5.0f} s   U={u:8.1f} mV"
        if t is not None:
            zeile += f"   T={t:5.1f} °C"
        if vorherige_spannung is not None:
            zeile += f"   Δ zur letzten Messung: {u - vorherige_spannung:+.1f} mV"
        print(zeile)

        letzte_spannung, letzte_temperatur = u, t
        vorherige_spannung = u

        # Bis zu MESSABSTAND_S Sekunden auf die Bestätigung warten; kommt sie
        # in dieser Zeit, sofort mit der zuletzt gedruckten Messung abbrechen.
        if bestaetigt.wait(timeout=MESSABSTAND_S):
            print(f"  -> übernommen: {letzte_spannung:.1f} mV"
                  + (f", {letzte_temperatur:.1f} °C" if letzte_temperatur is not None else ""))
            return letzte_spannung, letzte_temperatur


def nernst_steilheit_theorie(temperatur_c: float) -> float:
    """Theoretische Steilheit bei gegebener Temperatur, aus dem bekannten
    Wert 59,16 mV/pH bei 25 °C nach Gleichung 2.3 (Steilheit prop. zu T)."""
    return S_THEOR_25C * (273.15 + temperatur_c) / (273.15 + 25.0)


def main():
    print("=== Kalibrierung der pH-Messkette (2-Punkt: pH 4,01 / 7,00) ===")

    u_ph4, t_ph4 = messe_puffer("pH 4,01")
    u_ph7, t_ph7 = messe_puffer("pH 7,00")

    steilheit = (u_ph4 - u_ph7) / (7.00 - 4.01)   # Gleichung 4.5
    u0        = u_ph7                              # Gleichung 4.6, Nullpunkt bei pH 7,00

    if t_ph4 is not None and t_ph7 is not None:
        t_kal = statistics.mean([t_ph4, t_ph7])
    else:
        t_kal = t_ph4 if t_ph4 is not None else t_ph7
        print("WARNUNG: Temperatur nur an einem Puffer verfügbar — "
              "Prüfe den DS18B20-Anschluss.")

    if t_kal is None:
        print("FEHLER: Keine Temperaturmessung möglich. Ohne Kalibriertemperatur "
              "kann die Temperaturkompensation (Gleichung 3.2) nicht arbeiten.")
        t_kal = float(input("Ersatzweise Temperatur manuell eingeben (°C): "))

    steilheit_theorie = nernst_steilheit_theorie(t_kal)
    steilheit_prozent = abs(steilheit) / steilheit_theorie * 100

    print(f"\nSteilheit S  = {steilheit:.1f} mV/pH  "
          f"({steilheit_prozent:.1f} % der theoretischen Steilheit bei {t_kal:.1f} °C)")
    print(f"Nullpunkt U0 = {u0:.1f} mV (bei pH 7,00)")

    if steilheit_prozent < M06_GRENZE_PROZENT:
        print(f"ACHTUNG: {steilheit_prozent:.1f} % liegt unter der Brauchbarkeitsgrenze "
              f"von {M06_GRENZE_PROZENT:.0f} % (M-06). Elektrode wässern (Punkt t) "
              f"und erneut kalibrieren, bevor der Regelbetrieb gestartet wird.")

    # --- Verifikation mit pH 10,01 (fließt NICHT in Steilheit/Nullpunkt ein) ---
    u_ph10, t_ph10 = messe_puffer("pH 10,01 (nur Verifikation)")
    steilheit_bei_t10 = (steilheit * (273.15 + t_ph10) / (273.15 + t_kal)
                         if t_ph10 is not None else steilheit)
    ph_berechnet_10 = 7 + (u0 - u_ph10) / steilheit_bei_t10
    abweichung_10 = ph_berechnet_10 - 10.01
    print(f"\nVerifikation pH 10,01: berechnet {ph_berechnet_10:.2f} "
          f"(Abweichung {abweichung_10:+.2f} pH — Alkalifehler, siehe Abschnitt 4.4.3)")

    ergebnis = {
        "u0_mv": round(u0, 1),
        "steilheit_mv_pro_ph": round(steilheit, 2),
        "t_kal_c": round(t_kal, 1),
        "steilheit_prozent_theorie": round(steilheit_prozent, 1),
        "zeitstempel": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rohdaten": {
            "ph4_mv": round(u_ph4, 1), "ph4_temp_c": round(t_ph4, 1) if t_ph4 is not None else None,
            "ph7_mv": round(u_ph7, 1), "ph7_temp_c": round(t_ph7, 1) if t_ph7 is not None else None,
            "ph10_mv": round(u_ph10, 1), "ph10_temp_c": round(t_ph10, 1) if t_ph10 is not None else None,
        },
        "verifikation_ph10": {
            "berechnet": round(ph_berechnet_10, 2),
            "abweichung": round(abweichung_10, 2),
        },
    }

    with open(KALIBRIER_DATEI, "w") as f:
        json.dump(ergebnis, f, indent=2, ensure_ascii=False)

    print(f"\nGespeichert in {KALIBRIER_DATEI}. hydroponik.py verwendet diese Datei "
          f"automatisch beim nächsten Start.")


if __name__ == "__main__":
    main()
