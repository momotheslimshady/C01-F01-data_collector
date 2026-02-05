Reinraum Sensor Ingestion (data_ingestion_sum.py)

Python script for reading multiple environmental sensors on a Raspberry Pi (I²C + HM3301) and publishing measurements to MQTT, including Zigbee2MQTT device state aggregation (with age/status semantics).

What it does

Reads LPS22 (temperature, pressure) via I²C

Reads SGP30 (eCO₂, TVOC) via I²C

Reads FS3000 (air velocity / wind speed) via I²C (Qwiic)

Reads HM3301 (PM2.5) via software-I²C bus on GPIO18 (bus id 3)

Subscribes to Zigbee2MQTT topics for configured Zigbee devices and prints + republishes their latest state with:

OK (< 10 min)

STALE (≥ 10 min)

OFFLINE (≥ 1 h)

Also follows the repo convention of keeping naming consistent and avoiding mixed-language ambiguity (recommended project best practice). 

Best practices

Hardware / Components

Raspberry Pi 4 (or compatible)

I²C sensors:

Adafruit LPS22 (pressure/temp)

Adafruit SGP30 (air quality)

SparkFun FS3000 (air velocity, via Qwiic)

Grove / Seeed HM3301 (PM sensor, via software-I²C bus)

Zigbee devices integrated via Zigbee2MQTT:

Sonoff SNZB-02P (temperature/humidity)

Sonoff SNZB-04P (door/window contact)

MQTT Overview
Subscribed topics (Zigbee2MQTT)

zigbee2mqtt/<friendly_name>

Important: <friendly_name> must match what you configured in the Zigbee2MQTT UI.

Published topics (your measurement namespace)

Prefix:

reinraum1/

Published examples:

reinraum1/lps22/temperature

reinraum1/lps22/pressure

reinraum1/sgp30/eco2

reinraum1/sgp30/tvoc

reinraum1/fs3000/wind_speed

reinraum1/hm3301/pm2_5

Payload format (JSON):

{
  "value": 23.4,
  "unit": "°C",
  "timestamp": 1730000000000
}

Configuration

Edit these constants at the top of data_ingestion_sum.py:

BUS_D18_ID = 3
MQTT_BROKER = "192.168.178.50"
MQTT_PORT = 1883
Z2M_PREFIX = "zigbee2mqtt"
MQTT_PUBLISH_PREFIX = "reinraum1"

ZIGBEE_DEVICES = [
    "SNZB-02P",
    "SNZ-04P",
]

Zigbee friendly names

Replace the values in ZIGBEE_DEVICES with your actual Zigbee2MQTT friendly names.
If they don’t match, you will subscribe to the wrong topics and see n/a.

Setup (Python)
1) Enable I²C on Raspberry Pi

Enable I²C via raspi-config (Interface Options → I2C → Enable)

Reboot

2) Create and activate a venv
python3 -m venv hhz_venv
source hhz_venv/bin/activate
pip install --upgrade pip

3) Install dependencies
pip install \
  paho-mqtt \
  adafruit-circuitpython-lps2x \
  adafruit-circuitpython-sgp30 \
  qwiic-fs3000 \
  smbus2 \
  adafruit-blinka


If you saw ModuleNotFoundError: No module named 'paho', this fixes it:

pip install paho-mqtt

Run
source hhz_venv/bin/activate
python data_ingestion_sum.py


Stop with:

CTRL + C

Output (example)

Console prints one line per second, e.g.

Temp: 23.1°C | Druck: 1009.3hPa | eCO2: 450ppm | VOC: 12ppb | Wind: 0.14m/s | PM2.5: 3µg/m³ | ZB.Temp: 22.6°C (age 15s, OK) | ...

Zigbee status rules:

OK: last update < 10 min

STALE: ≥ 10 min

OFFLINE: ≥ 1 h

Troubleshooting
No MQTT connection

Verify broker IP/port (MQTT_BROKER, MQTT_PORT)

Ensure Mosquitto is reachable from the Pi:

nc -vz 192.168.178.50 1883

Zigbee values stay n/a

Check Zigbee2MQTT topic names in its UI/logs

Ensure ZIGBEE_DEVICES contains the exact friendly names

I²C devices not found

List I²C devices:

i2cdetect -y 1


Confirm wiring + power + correct bus

HM3301 read fails

This script expects HM3301 at address 0x40 and uses BUS_D18_ID = 3

If your software-I²C bus index differs, adjust BUS_D18_ID

Suggested repo structure
.
├── data_ingestion_sum.py
├── README.md
└── requirements.txt   (optional)


If you want, you can generate requirements.txt from your venv:

pip freeze > requirements.txt