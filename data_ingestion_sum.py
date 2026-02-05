import time
import json
import threading

import board
import smbus2

# --- SENSOR LIBRARIES ---
import adafruit_lps2x
import adafruit_sgp30
import qwiic_fs3000

# --- MQTT ---
import paho.mqtt.client as mqtt

# -------------------------------------------------
# KONFIGURATION
# -------------------------------------------------
BUS_D18_ID = 3                      # HM3301 Software-I2C
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
Z2M_PREFIX = "zigbee2mqtt"

# >>> ZIGBEE FRIENDLY NAMES (aus eurer Web-UI) <<<
ZIGBEE_DEVICES = [
    "SNZB-02P",   # Temp / Hum (SNZB-02P)
    "SNZ-04P",   # Door Sensor (SNZB-04P)
]

latest_zigbee = {}
latest_zigbee_ts = {}
zigbee_lock = threading.Lock()

# -------------------------------------------------
# HM3301 FEINSTAUBSENSOR
# -------------------------------------------------
class HM3301_D18:
    def __init__(self, bus_id):
        self.address = 0x40
        try:
            self.bus = smbus2.SMBus(bus_id)
            self.connected = True
        except Exception as e:
            print(f"❌ HM3301 Bus Fehler: {e}")
            self.connected = False

    def read(self):
        if not self.connected:
            return None, None, None
        try:
            self.bus.write_byte(self.address, 0x88)
            data = self.bus.read_i2c_block_data(self.address, 0x00, 29)
            pm1_0 = (data[4] << 8) | data[5]
            pm2_5 = (data[6] << 8) | data[7]
            pm10  = (data[8] << 8) | data[9]
            return pm1_0, pm2_5, pm10
        except Exception:
            return None, None, None

# -------------------------------------------------
# MQTT CALLBACKS
# -------------------------------------------------
def on_mqtt_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✔ MQTT verbunden (Zigbee2MQTT)")
        for dev in ZIGBEE_DEVICES:
            client.subscribe(f"{Z2M_PREFIX}/{dev}")
    else:
        print(f"❌ MQTT Fehler rc={rc}")

def on_mqtt_message(client, userdata, msg):
    try:
        dev = msg.topic.split("/", 1)[1]
        payload = json.loads(msg.payload.decode("utf-8"))
        with zigbee_lock:
            latest_zigbee[dev] = payload
            latest_zigbee_ts[dev] = time.time()
    except Exception:
        pass

def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_mqtt_connect
    client.on_message = on_mqtt_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    threading.Thread(target=client.loop_forever, daemon=True).start()

# -------------------------------------------------
# ZIGBEE FORMATIERUNG
# -------------------------------------------------
# Best Practice:
# Zigbee sensors operate as low-power sleepy end devices and only transmit
# data upon state changes or periodic wake-ups. The backend stores the
# last known state plus a timestamp. Use semantic age/status for downstream
# logic and human-readable output:
#   OK     : last value < 10 min
#   STALE  : >= 10 min
#   OFFLINE: >= 1 h
def format_zigbee_outputs(max_age_s=120):
    """Return formatted Zigbee outputs including age and status.

    Status semantics:
      - OK: last value < 10 minutes
      - STALE: last value >= 10 minutes
      - OFFLINE: last value >= 1 hour
    """
    out = []
    now = time.time()

    with zigbee_lock:
        for dev in ZIGBEE_DEVICES:
            payload = latest_zigbee.get(dev)
            ts = latest_zigbee_ts.get(dev)
            age = now - (ts or 0)

            # No data at all
            if not payload or ts is None:
                out.append(f"{dev}: n/a")
                continue

            # Determine status based on age
            if age >= 3600:
                status = "OFFLINE"
            elif age >= 600:
                status = "STALE"
            else:
                status = "OK"

            # Human-friendly age string
            if age < 60:
                age_str = f"{int(age)}s"
            elif age < 3600:
                age_str = f"{int(age // 60)}m"
            else:
                age_str = f"{int(age // 3600)}h"

            # Append fields with age and status
            if "temperature" in payload:
                out.append(f"ZB.Temp: {payload['temperature']:.1f}°C (age {age_str}, {status})")
            if "humidity" in payload:
                out.append(f"ZB.Hum: {payload['humidity']:.0f}% (age {age_str}, {status})")
            if "contact" in payload:
                out.append(f"ZB.Door: {'OPEN' if payload['contact'] is False else 'CLOSED'} (age {age_str}, {status})")
            if "battery" in payload:
                out.append(f"ZB.Bat: {payload['battery']}% (age {age_str}, {status})")

    return out

# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():
    print("--- INITIALISIERE SENSOREN ---")
    start_mqtt()

    i2c = board.I2C()

    try:
        lps = adafruit_lps2x.LPS22(i2c)
        print("✔ LPS22 bereit")
    except Exception:
        lps = None
        print("❌ LPS22 nicht gefunden")

    try:
        sgp = adafruit_sgp30.Adafruit_SGP30(i2c)
        sgp.iaq_init()
        print("✔ SGP30 bereit")
    except Exception:
        sgp = None
        print("❌ SGP30 nicht gefunden")

    try:
        fs3000 = qwiic_fs3000.QwiicFS3000()
        if fs3000.is_connected():
            fs3000.begin()
            print("✔ FS3000 bereit")
        else:
            fs3000 = None
    except Exception:
        fs3000 = None

    hm3301 = HM3301_D18(BUS_D18_ID)

    print("\n--- MESSUNG STARTET ---\n")

    try:
        while True:
            outputs = []

            if lps:
                outputs.append(f"Temp: {lps.temperature:.1f}°C")
                outputs.append(f"Druck: {lps.pressure:.1f}hPa")

            if sgp:
                try:
                    outputs.append(f"eCO2: {sgp.eCO2}ppm")
                    outputs.append(f"VOC: {sgp.TVOC}ppb")
                except:
                    outputs.append("SGP30: busy")

            if fs3000:
                try:
                    outputs.append(f"Wind: {fs3000.read_meters_per_second():.2f}m/s")
                except:
                    outputs.append("Wind: err")

            if hm3301.connected:
                _, pm25, _ = hm3301.read()
                outputs.append(f"PM2.5: {pm25}µg/m³" if pm25 else "PM2.5: err")

            outputs.extend(format_zigbee_outputs())

            print(" | ".join(outputs))
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nMessung beendet.")

if __name__ == "__main__":
    main()
