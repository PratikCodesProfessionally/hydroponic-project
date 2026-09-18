import time
import os
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
from flask import Flask, jsonify
from flask_cors import CORS

# ============================
#   PIN-ZUWEISUNGEN
# ============================
DHT_PIN        = board.D17
FEUCHTE_PIN    = 27
PUMP_PIN       = 5
W1_DEVICE_PATH = "/sys/bus/w1/devices/"
LOG_FILE       = "hydroponik_log.csv"

# ============================
#   SENSOR & AKTOR SETUP
# ============================
dht           = adafruit_dht.DHT11(DHT_PIN, use_pulseio=False)
feuchte_sensor = DigitalInputDevice(FEUCHTE_PIN, pull_up=False)
pumpe         = DigitalOutputDevice(PUMP_PIN)

# ============================
#   ADS1115 (pH-Sensor)
# ============================
i2c     = busio.I2C(board.SCL, board.SDA)
ads     = ADS.ADS1115(i2c, address=0x48)
ads.gain = 1
ph_chan = AnalogIn(ads, 0)

VREF   = 4.95
ADC_MAX = 32767
OFFSET  = 365

# ============================
#   pH-REGELUNG
# ============================
PH_SOLL       = 6.0    # Richtwert
PH_MAX_ABW    = 2.0    # ab dieser Abweichung wird maximal lange gepumpt
PH_MESSZYKLEN = 30     # pH-Messungen pro Durchlauf der Hauptschleife
PH_MESSPAUSE  = 10     # Sekunden zwischen zwei pH-Messungen
PUMP_MIN_S    = 2      # kürzeste Pumpdauer
PUMP_MAX_S    = 5      # längste Pumpdauer

# ============================
#   GLOBALER ZUSTAND (für API)
# ============================
sensor_data = {
    "luft_temp":    None,
    "luft_feuchte": None,
    "wasser_temp":  None,
    "ph":           None,
    "feuchtigkeit": None,
    "pumpe":        False,
    "timestamp":    None
}

def update_sensor_data(luft_temp, luft_feuchte, w_temp, ph, feucht):
    """Globalen Zustand an einer einzigen Stelle aktualisieren."""
    sensor_data.update({
        "luft_temp":    luft_temp,
        "luft_feuchte": luft_feuchte,
        "wasser_temp":  w_temp,
        "ph":           ph,
        "feuchtigkeit": feucht,
        "pumpe":        pumpe.is_active,
        "timestamp":    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# ============================
#   FLASK API
# ============================
app = Flask(__name__)
CORS(app)

@app.route("/api/sensors")
def get_sensors():
    return jsonify(sensor_data)

@app.route("/api/pump/<action>")
def pump_control(action):
    if action == "on":
        pumpe.on()
    elif action == "off":
        pumpe.off()
    else:
        return jsonify({"error": "Ungültige Aktion"}), 400
    return jsonify({"pump": action, "status": "ok"})

# Flask in eigenem Thread starten (blockiert nicht die Hauptschleife)
flask_thread = threading.Thread(
    target=lambda: app.run(host="0.0.0.0", port=5000, use_reloader=False),
    daemon=True
)
flask_thread.start()

# ============================
#   LOGGING
# ============================
def log_data(data: dict):
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

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
#   pH-MESSUNG
# ============================
def read_ph():
    buf = []
    for _ in range(10):
        buf.append(ph_chan.value)
        time.sleep(0.01)
    buf.sort()
    avg_value    = sum(buf[2:8]) / 6
    spannung_mv = avg_value * 4.096 / 32767 * 1000
    print(f"U = {spannung_mv:.1f} mV")
    sensor_value = avg_value * 1023 / ADC_MAX
    ph =  7 - (1000 * (sensor_value - OFFSET) * VREF) / (59.16 * 1023)
    return 8.23 + round(ph, 2)

def berechne_pumpdauer(ph_wert: float) -> int:
    """Pumpdauer in ganzen Sekunden (PUMP_MIN_S..PUMP_MAX_S),
    abhängig vom Abstand zum pH-Richtwert PH_SOLL."""
    abweichung = abs(ph_wert - PH_SOLL)
    anteil     = min(abweichung / PH_MAX_ABW, 1.0)   # 0.0 .. 1.0
    return int(PUMP_MIN_S + round(anteil * (PUMP_MAX_S - PUMP_MIN_S)))

# ============================
#   SAUBERES BEENDEN
# ============================
def cleanup(sig, frame):
    print("\nSystem wird beendet – Aktoren werden ausgeschaltet...")
    pumpe.off()
    dht.exit()
    sys.exit(0)

signal.signal(signal.SIGINT,  cleanup)
signal.signal(signal.SIGTERM, cleanup)

# ============================
#   HAUPTSCHLEIFE
# ============================
print("Hydroponik-System gestartet...")
print(f"API läuft auf http://0.0.0.0:5000\n")

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
        dht.exit()
        time.sleep(1)
        dht = adafruit_dht.DHT11(DHT_PIN, use_pulseio=False)

    # --- Bodenfeuchtesensor ---
    feucht = feuchte_sensor.value
    if feucht:
        print("Feuchtigkeit: erkannt")
    else:
        print("Feuchtigkeit: trocken")

    # --- Wassertemperatur (DS18B20) ---
    w_temp = read_water_temp()
    if w_temp is not None:
        print(f"Wassertemperatur: {w_temp:.2f} °C")
    else:
        print("Wassertemperatur: Fehler beim Lesen")

    # --- pH messen & globalen Zustand aktualisieren (für API) ---
    ph = None
    for _ in range(PH_MESSZYKLEN):
        ph = read_ph()
        print(f"pH-Wert: {ph:.2f}")
        update_sensor_data(luft_temp, luft_feuchte, w_temp, ph, feucht)
        time.sleep(PH_MESSPAUSE)

    # --- pH-Regelung ---
    if ph is not None and ph > PH_SOLL:
        pump_dauer = berechne_pumpdauer(ph)   # int zwischen PUMP_MIN_S und PUMP_MAX_S
        print(f"pH zu hoch ({ph:.2f}) → Pumpe EIN für {pump_dauer} s (pH-Up)")
        pumpe.on()
        time.sleep(pump_dauer)
        pumpe.off()
        print("Pumpe AUS – Stabilisierung...")
        time.sleep(5)
        ph = read_ph()
        print(f"pH nach Regelung: {ph:.2f}")
        update_sensor_data(luft_temp, luft_feuchte, w_temp, ph, feucht)

    # --- In CSV loggen ---
    log_data(sensor_data)

    time.sleep(2)
