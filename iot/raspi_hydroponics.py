import csv
import os
import signal
import sys
import threading
import time
from datetime import datetime

import adafruit_ads1x15.ads1115 as ADS
import adafruit_dht
import board
import busio
from adafruit_ads1x15.analog_in import AnalogIn
from flask import Flask, jsonify
from flask_cors import CORS
from gpiozero import DigitalInputDevice, DigitalOutputDevice

# ============================
#   CONFIG
# ============================
HOST = os.getenv("HYDRO_HOST", "0.0.0.0")
PORT = int(os.getenv("HYDRO_PORT", "5000"))
LOG_FILE = os.getenv("HYDRO_LOG_FILE", "hydroponik_log.csv")

DHT_PIN = board.D17
FEUCHTE_PIN = int(os.getenv("HYDRO_FEUCHTE_PIN", "27"))
PUMP_PIN = int(os.getenv("HYDRO_PUMP_PIN", "5"))
W1_DEVICE_PATH = os.getenv("HYDRO_W1_DEVICE_PATH", "/sys/bus/w1/devices/")

POLL_INTERVAL_SECONDS = float(os.getenv("HYDRO_POLL_INTERVAL_SECONDS", "2"))

VREF = 4.95
ADC_MAX = 32767
OFFSET = 365

# ============================
#   HARDWARE SETUP
# ============================
dht = adafruit_dht.DHT11(DHT_PIN, use_pulseio=False)
feuchte_sensor = DigitalInputDevice(FEUCHTE_PIN, pull_up=False)
pumpe = DigitalOutputDevice(PUMP_PIN)

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c, address=0x48)
ads.gain = 1
ph_chan = AnalogIn(ads, 0)

# ============================
#   APP STATE
# ============================
sensor_data = {
    "luft_temp": None,
    "luft_feuchte": None,
    "wasser_temp": None,
    "ph": None,
    "feuchtigkeit": None,
    "pumpe": False,
    "timestamp": None,
}

app = Flask(__name__)
CORS(app)


def log_data(data: dict) -> None:
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)


def read_water_temp():
    try:
        device_folder = next(folder for folder in os.listdir(W1_DEVICE_PATH) if folder.startswith("28-"))
        device_file = f"{W1_DEVICE_PATH}{device_folder}/w1_slave"
        with open(device_file, "r", encoding="utf-8") as file_handle:
            lines = file_handle.readlines()
        if "YES" not in lines[0]:
            return None
        return float(lines[1].split("t=")[-1]) / 1000.0
    except Exception:
        return None


def read_ph():
    samples = []
    for _ in range(10):
        samples.append(ph_chan.value)
        time.sleep(0.01)

    samples.sort()
    average_value = sum(samples[2:8]) / 6
    sensor_value = average_value * 1023 / ADC_MAX
    ph = 7 - (1000 * (sensor_value - OFFSET) * VREF) / (59.16 * 1023)
    return round(7 + ph, 2)


def read_sensor_snapshot():
    luft_temp = None
    luft_feuchte = None

    try:
        luft_temp = dht.temperature
        luft_feuchte = dht.humidity
    except Exception:
        try:
            dht.exit()
        except Exception:
            pass
        time.sleep(1)
        return None

    return {
        "luft_temp": luft_temp,
        "luft_feuchte": luft_feuchte,
        "wasser_temp": read_water_temp(),
        "ph": read_ph(),
        "feuchtigkeit": feuchte_sensor.value,
        "pumpe": pumpe.is_active,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def update_state_forever():
    global sensor_data

    while True:
        snapshot = read_sensor_snapshot()
        if snapshot is None:
            continue

        sensor_data.update(snapshot)

        # pH-Autoregelung bleibt lokal auf dem Pi.
        current_ph = snapshot["ph"]
        try:
            if current_ph is not None and current_ph < 5.5:
                pumpe.on()
                time.sleep(2)
                pumpe.off()
                time.sleep(30)
            elif current_ph is not None and current_ph > 7.5:
                time.sleep(30)
        finally:
            sensor_data["pumpe"] = pumpe.is_active

        log_data(sensor_data)
        time.sleep(POLL_INTERVAL_SECONDS)


@app.get("/api/sensors")
def get_sensors():
    return jsonify(sensor_data)


@app.post("/api/sensors")
def post_sensors():
    return jsonify(sensor_data)


@app.get("/api/pump/<action>")
def pump_control(action):
    if action == "on":
        pumpe.on()
    elif action == "off":
        pumpe.off()
    else:
        return jsonify({"error": "Ungültige Aktion"}), 400

    sensor_data["pumpe"] = pumpe.is_active
    sensor_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return jsonify({"pump": action, "status": "ok"})


def cleanup(_sig, _frame):
    print("\nSystem wird beendet - Aktoren werden ausgeschaltet...")
    try:
        pumpe.off()
    finally:
        try:
            dht.exit()
        except Exception:
            pass
        sys.exit(0)


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


if __name__ == "__main__":
    print("Hydroponik-System gestartet...")
    print(f"API läuft auf http://{HOST}:{PORT}")

    updater_thread = threading.Thread(target=update_state_forever, daemon=True)
    updater_thread.start()

    app.run(host=HOST, port=PORT, use_reloader=False)