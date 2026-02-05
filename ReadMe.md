# Reinraum Sensor Ingestion (`data_ingestion_sum.py`)

Python script for reading multiple environmental sensors on a Raspberry Pi (I²C + HM3301) and publishing measurements to MQTT, including Zigbee2MQTT device state aggregation with age/status semantics.

---

## ✅ Features

- Reads **LPS22** (temperature, pressure) via I²C  
- Reads **SGP30** (eCO₂, TVOC) via I²C  
- Reads **FS3000** (air velocity / wind speed) via I²C (Qwiic)  
- Reads **HM3301** (PM2.5) via software-I²C bus (GPIO18 / bus id `3`)
- Subscribes to **Zigbee2MQTT** topics and tracks latest state per device
- Publishes structured JSON payloads to MQTT under a configurable prefix
- Adds semantic freshness states for Zigbee devices:
  - **OK**: last update < 10 min
  - **STALE**: ≥ 10 min
  - **OFFLINE**: ≥ 1 h

---

## 🧰 Hardware

| Component | Purpose |
|----------|---------|
| Raspberry Pi 4 (or compatible) | Runs script + MQTT publishing |
| Adafruit LPS22 | Temperature + Pressure |
| Adafruit SGP30 | eCO₂ + TVOC |
| SparkFun FS3000 | Air velocity / wind speed |
| Grove/Seeed HM3301 | PM2.5 fine dust |
| Zigbee devices via Zigbee2MQTT | Temp/Hum + Door contact |

---

## 📡 MQTT Topics

### Subscribed (Zigbee2MQTT)
The script subscribes to:
- `zigbee2mqtt/<friendly_name>`

> ⚠️ **Important:** `<friendly_name>` must match the **device name in the Zigbee2MQTT web UI**.

### Published (Measurements)
All measurements are published under:
- `reinraum1/<sensor>/<measurement>`

Examples:
- `reinraum1/lps22/temperature`
- `reinraum1/lps22/pressure`
- `reinraum1/sgp30/eco2`
- `reinraum1/sgp30/tvoc`
- `reinraum1/fs3000/wind_speed`
- `reinraum1/hm3301/pm2_5`

---

## 🧾 Payload Format (JSON)

All published values follow a consistent schema:

```json
{
  "value": 23.4,
  "unit": "°C",
  "timestamp": 1730000000000
}
