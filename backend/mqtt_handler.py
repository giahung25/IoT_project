# -*- coding: utf-8 -*-
import json
import time
import random
import threading
from datetime import datetime
from backend.config import (
    MQTT_BROKER, MQTT_PORT, MQTT_SUB_TOPIC, MQTT_PUB_TOPIC,
    SIMULATE_SENSOR, DEFAULT_CAMERA_SOURCE
)

# Import paho.mqtt.client với cơ chế phòng ngừa lỗi
MQTT_AVAILABLE = False
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    print("[MQTT] ⚠️ Thư viện 'paho-mqtt' chưa được cài đặt. Hệ thống sẽ tự động chạy ở chế độ giả lập.")

# Biến dùng chung lưu dữ liệu cảm biến mới nhất nhận được
latest_sensor_data = {
    "temperature": 27.5,
    "humidity": 78.0,
    "esp32_online": False,
    "last_updated": None
}

# Biến điều khiển chế độ chụp và nguồn camera từ PC
capture_mode = "auto"
camera_source = DEFAULT_CAMERA_SOURCE
manual_capture_trigger = False

client = None
mqtt_connected = False

def get_capture_mode():
    global capture_mode
    return capture_mode

def get_camera_source():
    global camera_source
    return camera_source

def check_and_reset_manual_capture():
    global manual_capture_trigger
    if manual_capture_trigger:
        manual_capture_trigger = False
        return True
    return False

def on_connect(client_instance, userdata, flags, rc):
    global mqtt_connected
    if rc == 0:
        print(f"[MQTT] 🟢 Đã kết nối thành công tới Broker tại: {MQTT_BROKER}")
        mqtt_connected = True
        # Subscribe cả dữ liệu cảm biến và kênh lệnh điều khiển
        client_instance.subscribe(MQTT_SUB_TOPIC)
        client_instance.subscribe("mushroom/control")
        print(f"[MQTT] Đang lắng nghe trên: {MQTT_SUB_TOPIC} và mushroom/control")
    else:
        print(f"[MQTT] ❌ Kết nối thất bại, mã lỗi: {rc}")
        mqtt_connected = False

def on_message(client_instance, userdata, msg):
    global latest_sensor_data, capture_mode, camera_source, manual_capture_trigger
    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)
        
        # Phân biệt tin nhắn dựa trên Topic
        if msg.topic == "mushroom/control":
            if "capture_mode" in data:
                capture_mode = data["capture_mode"]
                print(f"[MQTT] 📥 Đổi chế độ chụp sang: {capture_mode}")
            if "camera_source" in data:
                camera_source = data["camera_source"]
                print(f"[MQTT] 📥 Đổi nguồn camera sang: {camera_source}")
            if data.get("action") == "capture":
                manual_capture_trigger = True
                if "camera_source" in data:
                    camera_source = data["camera_source"]
                print(f"[MQTT] 📥 Kích hoạt lệnh chụp ảnh thủ công từ PC Dashboard (Nguồn: {camera_source})!")

        else:
            # Hỗ trợ linh hoạt các dạng key: "temperature"/"temp" và "humidity"/"hum"
            if "temperature" in data:
                latest_sensor_data["temperature"] = round(float(data["temperature"]), 1)
            elif "temp" in data:
                latest_sensor_data["temperature"] = round(float(data["temp"]), 1)

            if "humidity" in data:
                latest_sensor_data["humidity"] = round(float(data["humidity"]), 1)
            elif "hum" in data:
                latest_sensor_data["humidity"] = round(float(data["hum"]), 1)

            if "co2_ppm" in data:
                latest_sensor_data["co2_ppm"] = int(data["co2_ppm"])
            if "light_lux" in data:
                latest_sensor_data["light_lux"] = int(data["light_lux"])
            if "sensor_source" in data:
                latest_sensor_data["sensor_source"] = str(data["sensor_source"])

            latest_sensor_data["esp32_online"] = True
            latest_sensor_data["last_updated"] = datetime.now().isoformat()
            print(f"[MQTT BLE-Bridge] 📥 Đã nhận dữ liệu ESP32 qua BLE: Temp={latest_sensor_data['temperature']}°C, Hum={latest_sensor_data['humidity']}%, CO2={latest_sensor_data.get('co2_ppm', 400)}ppm, Light={latest_sensor_data.get('light_lux', 0)}Lux ({latest_sensor_data.get('sensor_source', 'N/A')})")
    except Exception as e:
        print(f"[MQTT] ❌ Lỗi phân tích bản tin nhận được: {e}")



def on_disconnect(client_instance, userdata, rc):
    global mqtt_connected
    print("[MQTT] ⚠️ Đã mất kết nối tới Broker.")
    mqtt_connected = False
    latest_sensor_data["esp32_online"] = False

def simulate_sensor_thread():
    """Hàm chạy ngầm để sinh dữ liệu cảm biến giả lập khi chạy chế độ offline."""
    global latest_sensor_data
    print("[MQTT] 🟢 Khởi động luồng sinh dữ liệu giả lập (Virtual Sensor Data).")
    
    # Khởi tạo giá trị ban đầu
    t = 27.5
    h = 75.0
    
    while True:
        # Thay đổi nhiệt độ và độ ẩm một cách mượt mà để vẽ chart đẹp mắt
        t += random.uniform(-0.3, 0.3)
        t = max(24.0, min(32.0, t)) # giới hạn trong khoảng 24-32 độ
        
        h += random.uniform(-2.0, 2.0)
        h = max(60.0, min(95.0, h)) # giới hạn trong khoảng 60-95% độ ẩm để kích hoạt pump (<70)
        
        latest_sensor_data["temperature"] = round(t, 1)
        latest_sensor_data["humidity"] = round(h, 1)
        latest_sensor_data["esp32_online"] = True
        latest_sensor_data["last_updated"] = datetime.now().isoformat()
        
        # In log định kỳ
        # print(f"[MQTT - MOCK] Sinh dữ liệu ảo: Temp={latest_sensor_data['temperature']}°C, Hum={latest_sensor_data['humidity']}%")
        time.sleep(5)

def firebase_sync_thread():
    """Luồng lắng nghe Firebase RTDB, phát hiện lệnh điều khiển từ Web/PC và chuyển tiếp tới ESP32 qua BLE."""
    import urllib.request
    last_controls = {}
    FIREBASE_URL = "https://agrishroom-edge-default-rtdb.asia-southeast1.firebasedatabase.app/status.json"
    
    print("[Firebase Sync] 🟢 Đã khởi động luồng lắng nghe lệnh từ xa (Web / PC -> Firebase -> BLE ESP32)...")
    
    while True:
        try:
            req = urllib.request.Request(FIREBASE_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    current_controls = {}
                    for key in ["pump", "harvest_alert", "grow_light", "cooling_fan", "vent_gate"]:
                        if key in data:
                            current_controls[key] = bool(data[key])
                    
                    if current_controls and current_controls != last_controls:
                        print(f"[Firebase Sync] 📥 Lệnh thay đổi từ Web/PC: {current_controls}")
                        publish_command(full_payload=current_controls)
                        last_controls = current_controls
        except Exception as e:
            pass
        time.sleep(1.5)

def start_mqtt_client():
    """Khởi động MQTT Client và Luồng giả lập tương ứng cấu hình."""
    global client
    
    # 1. Khởi động luồng giả lập cảm biến nếu cấu hình yêu cầu
    if SIMULATE_SENSOR:
        thread = threading.Thread(target=simulate_sensor_thread, daemon=True)
        thread.start()
        
    # 2. Khởi động luồng đồng bộ lệnh từ xa Firebase -> BLE ESP32
    sync_thread = threading.Thread(target=firebase_sync_thread, daemon=True)
    sync_thread.start()

    # 3. Luôn kết nối MQTT Client để nhận các lệnh điều khiển (như chụp thủ công) từ PC
    if MQTT_AVAILABLE:
        try:
            client = mqtt.Client()
            client.on_connect = on_connect
            client.on_message = on_message
            client.on_disconnect = on_disconnect
            
            print(f"[MQTT] Đang kết nối tới Broker: {MQTT_BROKER}:{MQTT_PORT}...")
            client.connect_async(MQTT_BROKER, MQTT_PORT, keepalive=60)
            client.loop_start()
        except Exception as e:
            print(f"[MQTT] ❌ Không kết nối được MQTT Broker do lỗi: {e}")
            if not SIMULATE_SENSOR:
                print("[MQTT] Kích hoạt cảm biến ảo làm dự phòng.")
                thread = threading.Thread(target=simulate_sensor_thread, daemon=True)
                thread.start()
    else:
        print("[MQTT] ⚠️ Thư viện 'paho-mqtt' không sẵn có. Không thể nhận lệnh từ PC.")


def publish_command(pump_status=None, harvest_alert=None, grow_light=None, cooling_fan=None, vent_gate=None, full_payload=None):
    """Gửi lệnh điều khiển thiết bị chấp hành tới ESP32 qua topic actuator/command."""
    global client, mqtt_connected
    
    if full_payload and isinstance(full_payload, dict):
        payload = full_payload
    else:
        payload = {}
        if pump_status is not None: payload["pump"] = pump_status
        if harvest_alert is not None: payload["harvest_alert"] = harvest_alert
        if grow_light is not None: payload["grow_light"] = grow_light
        if cooling_fan is not None: payload["cooling_fan"] = cooling_fan
        if vent_gate is not None: payload["vent_gate"] = vent_gate
    
    payload_str = json.dumps(payload)
    
    if MQTT_AVAILABLE and client and mqtt_connected:
        try:
            client.publish(MQTT_PUB_TOPIC, payload_str)
            print(f"[MQTT] 📤 Đã gửi lệnh điều khiển tới ESP32 qua BLE: {payload_str}")
        except Exception as e:
            print(f"[MQTT] ❌ Gửi lệnh thất bại: {e}")
    else:
        print(f"[MQTT - MOCK] 📤 Đã xuất lệnh (Giả lập): {payload_str}")
