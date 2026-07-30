# -*- coding: utf-8 -*-
import serial
import serial.tools.list_ports
import time
import sys
import re
import json
import logging
import paho.mqtt.client as mqtt

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Cấu hình MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_SUB_TOPIC = "actuator/command"
MQTT_PUB_TOPIC = "sensor/data"

# Đối tượng kết nối Serial
ser = None

def on_mqtt_connect(client, userdata, flags, rc, properties=None):
    logger.info("Connected to local MQTT Broker.")
    client.subscribe(MQTT_SUB_TOPIC)
    logger.info(f"Subscribed to topic: {MQTT_SUB_TOPIC}")

def on_mqtt_message(client, userdata, msg):
    global ser
    try:
        payload = msg.payload.decode('utf-8')
        logger.info(f"Received MQTT message on {msg.topic}: {payload}")
        
        # Gửi xuống ESP32 qua Serial (nếu đã kết nối)
        if ser and ser.is_open:
            logger.info(f"Forwarding command to USB Serial: {payload}")
            ser.write((payload + "\n").encode('utf-8'))
        else:
            logger.warning("Cannot forward command: Serial port is not open.")
    except Exception as e:
        logger.error(f"Error handling MQTT message: {e}")

def detect_esp32_port():
    ports = list(serial.tools.list_ports.comports())
    esp_ports = []
    for p in ports:
        device = p.device
        description = p.description or ""
        manufacturer = p.manufacturer or ""
        if "ACM" in device or "USB" in device or "Espressif" in manufacturer or "CH34" in description or "CP21" in description:
            esp_ports.append(device)
            
    if not esp_ports:
        return None
        
    # Ưu tiên cổng ttyUSB nếu có, nếu không thì ttyACM
    port = esp_ports[0]
    for p in esp_ports:
        if "USB" in p:
            port = p
            break
    return port

def main():
    global ser
    logger.info("=== ESP32 USB Serial to MQTT Bridge ===")
    
    # 1. Thiết lập kết nối MQTT
    mqtt_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message
    
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()  # Chạy vòng lặp MQTT ở luồng phụ
    except Exception as e:
        logger.error(f"Failed to connect to local MQTT broker: {e}")
        sys.exit(1)
        
    # 2. Vòng lặp kết nối và đọc dữ liệu từ Serial
    while True:
        port = detect_esp32_port()
        if not port:
            logger.warning("No ESP32 USB Serial port detected! Retrying in 5 seconds...")
            time.sleep(5)
            continue
            
        logger.info(f"Connecting to ESP32 on port {port} (115200 baud)...")
        try:
            ser = serial.Serial(port, 115200, timeout=1)
            ser.dtr = True
            ser.rts = True
            time.sleep(1) # Chờ kết nối ổn định
            
            logger.info("Connection established! Monitoring serial port...")
            
            while ser.is_open:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        logger.info(f"[Serial Data]: {line}")
                        
                        # Khớp regex để lấy Nhiệt độ và Độ ẩm
                        # Định dạng từ ESP32: "Nhiet do: 33.20 C   |   Do am: 70.60 %"
                        match = re.search(r"Nhiet do:\s*([\d\.]+)\s*C\s*\|\s*Do am:\s*([\d\.]+)\s*%", line)
                        if match:
                            try:
                                temp = float(match.group(1))
                                hum = float(match.group(2))
                                
                                # Đóng gói JSON gửi MQTT
                                data = {
                                    "temperature": temp,
                                    "humidity": hum,
                                    "esp32_online": True
                                }
                                payload = json.dumps(data)
                                mqtt_client.publish(MQTT_PUB_TOPIC, payload)
                                logger.info(f"Published to MQTT: {payload}")
                            except Exception as parse_err:
                                logger.error(f"Error parsing data values: {parse_err}")
                time.sleep(0.01)
                
        except PermissionError:
            logger.error(f"Permission denied accessing port {port}. Please run with sudo.")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Serial communication error: {e}")
            if ser:
                try:
                    ser.close()
                except:
                    pass
            time.sleep(5)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Stopping Serial-MQTT Bridge...")
