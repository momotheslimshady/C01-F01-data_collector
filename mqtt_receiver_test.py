#!/usr/bin/env python3
"""
MQTT Test-Client zum Empfangen und Anzeigen der Messdaten
"""
import paho.mqtt.client as mqtt
import json

MQTT_BROKER = "192.168.178.50"
MQTT_PORT = 1883
MQTT_TOPIC = "reinraum1/#"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✔ Connected to MQTT Broker")
        client.subscribe(MQTT_TOPIC)
        print(f"✔ Subscribed to: {MQTT_TOPIC}\n")
    else:
        print(f"❌ Connection failed with rc={rc}")

def on_message(client, userdata, msg):
    """Empfange und zeige MQTT Messages an"""
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        print(f"Topic: {msg.topic}")
        print(f"  Value: {payload.get('value')}")
        print(f"  Unit: {payload.get('unit')}")
        print(f"  Timestamp: {payload.get('timestamp')}")
        print()
    except json.JSONDecodeError:
        print(f"Topic: {msg.topic}")
        print(f"  Payload: {msg.payload.decode('utf-8')}")
        print()

if __name__ == "__main__":
    print("--- MQTT Receiver Test ---\n")
    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nDisconnected")
        client.disconnect()
