import sys
import json
import paho.mqtt.client as mqtt

# Configurations
JETSON_IP = "192.168.55.1"  # IP of the Jetson via USB Network
PORT = 1883
TOPIC = "sensor/data"

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("=== Connected to Jetson MQTT Broker successfully! ===")
        print(f"Listening for sensor data on topic: '{TOPIC}'...")
        print("Press Ctrl+C to stop.\n")
        client.subscribe(TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")
        sys.exit(1)

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8')
        data = json.loads(payload)
        
        if "temperature" in data and "humidity" in data:
            temp = data["temperature"]
            hum = data["humidity"]
            print(f"[Sensor Data] Temperature: {temp}°C | Humidity: {hum}%")
        elif "error" in data:
            print(f"[Sensor Error] {data['error']}")
        else:
            print(f"[Raw Data] {payload}")
    except Exception as e:
        print(f"Error parsing message: {e} | Raw payload: {msg.payload}")

if __name__ == '__main__':
    print("=== ESP32-Jetson BLE-MQTT Sensor Monitor ===")
    print(f"Connecting to Jetson at {JETSON_IP}:{PORT}...")
    
    # Setup MQTT Client
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(JETSON_IP, PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nStopping monitor...")
    except Exception as e:
        print(f"\nConnection error: {e}")
        print("Please check if the USB cable is connected and Jetson is turned on.")
