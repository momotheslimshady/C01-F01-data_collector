import time
import board
import busio
import smbus2

# --- BIBLIOTHEKEN IMPORTIEREN ---
import adafruit_lps2x
import adafruit_sgp30
import qwiic_fs3000

# --- KONFIGURATION ---
BUS_D18_ID = 3  # Software-I2C auf D18/D19

# --- KLASSE FÜR HM3301 (Feinstaub) auf D18 ---
class HM3301_D18:
    def __init__(self, bus_id):
        self.address = 0x40
        try:
            self.bus = smbus2.SMBus(bus_id)
            self.connected = True
        except Exception as e:
            print(f"Fehler beim Öffnen von Bus {bus_id}: {e}")
            self.connected = False

    def read(self):
        if not self.connected: return None, None, None
        try:
            # Befehl zum Messen senden
            self.bus.write_byte(self.address, 0x88)
            # Daten abholen (29 Bytes)
            data = self.bus.read_i2c_block_data(self.address, 0x00, 29)
            
            # Werte extrahieren (Standard Particulate Matter)
            pm1_0 = (data[4] << 8) | data[5]
            pm2_5 = (data[6] << 8) | data[7]
            pm10  = (data[8] << 8) | data[9]
            return pm1_0, pm2_5, pm10
        except Exception:
            return None, None, None

def main():
    print("--- SENSOREN INITIALISIEREN ---")
    
    # I2C Bus für Standard Sensoren (Bus 1)
    i2c_std = board.I2C()

    # --- SENSOR 1: LPS22 (Druck/Temp) ---
    try:
        lps = adafruit_lps2x.LPS22(i2c_std)
        print("✔ LPS22 (Druck/Temp) bereit")
    except Exception:
        lps = None
        print("❌ LPS22 nicht gefunden")

    # --- SENSOR 2: SGP30 (Luftqualität) ---
    try:
        sgp = adafruit_sgp30.Adafruit_SGP30(i2c_std)
        sgp.iaq_init() 
        print("✔ SGP30 (VOC/eCO2) bereit")
    except Exception:
        sgp = None
        print("❌ SGP30 nicht gefunden")

    # --- SENSOR 3: FS3000 (Wind) ---
    try:
        fs3000 = qwiic_fs3000.QwiicFS3000()
        if fs3000.is_connected():
            fs3000.begin()
            print("✔ FS3000 (Wind) bereit")
        else:
            fs3000 = None
            print("❌ FS3000 nicht verbunden")
    except Exception:
        fs3000 = None
        print("❌ FS3000 Fehler")

    # --- SENSOR 4: HM3301 (Feinstaub) auf D18 ---
    hm3301 = HM3301_D18(BUS_D18_ID)
    if hm3301.connected:
        print(f"✔ HM3301 (Feinstaub) auf Bus {BUS_D18_ID} bereit")
    else:
        print(f"❌ HM3301 auf Bus {BUS_D18_ID} nicht erreichbar")

    print("\n--- MESSUNG GESTARTET (Beenden mit STRG+C) ---\n")

    try:
        while True:
            outputs = []
            
            # Globaler Try-Block für den gesamten Durchlauf
            try:
                # A) LPS22 lesen
                if lps:
                    try:
                        outputs.append(f"Temp: {lps.temperature:.1f}°C")
                        outputs.append(f"Druck: {lps.pressure:.1f}hPa")
                    except Exception:
                        outputs.append("LPS22: err")

                # B) SGP30 lesen (Hier fangen wir den OSError gezielt ab)
                if sgp:
                    try:
                        outputs.append(f"eCO2: {sgp.eCO2}ppm")
                        outputs.append(f"VOC: {sgp.TVOC}ppb")
                    except (OSError, RuntimeError):
                        outputs.append("SGP30: busy")

                # C) FS3000 lesen
                if fs3000:
                    try:
                        wind_ms = fs3000.read_meters_per_second()
                        outputs.append(f"Wind: {wind_ms:.2f}m/s")
                    except Exception:
                        outputs.append("Wind: err")

                # D) HM3301 lesen (D18 / Bus 3)
                if hm3301.connected:
                    try:
                        pm1, pm25, pm10 = hm3301.read()
                        if pm25 is not None:
                            outputs.append(f"PM2.5: {pm25}µg/m³")
                        else:
                            outputs.append("PM2.5: err")
                    except Exception:
                        outputs.append("PM2.5: err")

                # Ausgabe in einer Zeile
                if outputs:
                    print(" | ".join(outputs))
                else:
                    print("Warte auf Sensordaten...")

            except OSError as e:
                # Falls der Bus komplett blockiert ist
                print(f"⚠️ I2C Bus Fehler: {e}")
                time.sleep(0.5)

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nMessung durch Benutzer beendet.")
    finally:
        if hm3301.connected:
            hm3301.bus.close()

if __name__ == "__main__":
    main()