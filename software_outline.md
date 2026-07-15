# 📝 Bản Phác Thảo Phần Mềm (Software Outline)

Hệ thống Edge AI & IoT Giám sát Sinh trưởng Nấm được chia thành 3 thành phần chính: **ESP32 Firmware**, **Edge Server Python Backend**, và **Web Dashboard**.

---

## 📡 1. Mạch ESP32 (Firmware - `esp32_iot_node.ino`)
Nhiệm vụ: Kết nối Wi-Fi, đọc cảm biến gửi lên MQTT và nhận lệnh điều khiển thiết bị chấp hành.

```cpp
// Thư viện cần dùng: WiFi.h, PubSubClient.h, DHT.h, ArduinoJson.h

#define DHTPIN 4
#define DHTTYPE DHT11
#define RELAY_PUMP 26
#define RELAY_ALERT 27

// Khai báo cấu hình WiFi & MQTT Broker (Jetson Orin Nano)
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqtt_server = "192.168.1.110"; // IP của Jetson
const int mqtt_port = 1883;

void setup() {
    Serial.begin(115200);
    pinMode(RELAY_PUMP, OUTPUT);
    pinMode(RELAY_ALERT, OUTPUT);
    // Tắt các thiết bị lúc khởi động
    digitalWrite(RELAY_PUMP, LOW);
    digitalWrite(RELAY_ALERT, LOW);
    
    setup_wifi();
    client.setServer(mqtt_server, mqtt_port);
    client.setCallback(callback); // Hàm xử lý lệnh MQTT nhận về
}

void loop() {
    if (!client.connected()) {
        reconnect();
    }
    client.loop();

    // Định kỳ đọc cảm biến mỗi 5 giây
    long now = millis();
    if (now - lastMsg > 5000) {
        lastMsg = now;
        float h = dht.readHumidity();
        float t = dht.readTemperature();
        
        // Tạo JSON payload gửi lên topic "sensor/data"
        StaticJsonDocument<200> doc;
        doc["temperature"] = t;
        doc["humidity"] = h;
        doc["timestamp"] = get_iso_time();
        
        char buffer[256];
        serializeJson(doc, buffer);
        client.publish("sensor/data", buffer);
    }
}

// Xử lý khi nhận gói tin MQTT từ topic "actuator/command"
void callback(char* topic, byte* message, unsigned int length) {
    // Parse JSON: {"pump": true/false, "harvest_alert": true/false}
    // Điều khiển các chân GPIO tương ứng:
    // - pump == true -> digitalWrite(RELAY_PUMP, HIGH)
    // - harvest_alert == true -> digitalWrite(RELAY_ALERT, HIGH)
}
```

---

## 🖥️ 2. Edge Server (Python Backend - Jetson)
Nhiệm vụ: Chạy dưới nền, lắng nghe MQTT, chụp ảnh Webcam, gọi Ollama API (Vision LLM), chạy Decision Engine và lưu SQLite.

### 2.1 File cấu hình (`backend/config.py`)
```python
# Cấu hình IP và Cổng kết nối
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_SUB_TOPIC = "sensor/data"
MQTT_PUB_TOPIC = "actuator/command"

OLLAMA_API_URL = "http://localhost:11434/api/generate"
VISION_MODEL = "moondream" # Model Vision siêu nhẹ chạy trên Jetson

WEBCAM_INDEX = 0
DB_PATH = "../database/mushroom_monitor.db"
IMAGE_TEMP_PATH = "../dashboard/static/images/latest.jpg"
```

### 2.2 Xử lý nhận dữ liệu và lưu Database (`backend/mqtt_handler.py` & `backend/database.py`)
- Lắng nghe MQTT topic `sensor/data`.
- Ghi dữ liệu cảm biến vào bảng `sensor_logs` trong SQLite.

### 2.3 Chụp và phân tích ảnh (`backend/vision_analyzer.py`)
```python
import cv2
import requests
import base64

def capture_image(camera_index, save_path):
    cap = cv2.VideoCapture(camera_index)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(save_path, frame)
    cap.release()
    return ret

def analyze_mushroom_image(image_path, model_name, api_url):
    with open(image_path, "rb") as image_file:
        img_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        
    payload = {
        "model": model_name,
        "prompt": "Analyze this mushroom image. Return JSON only with field 'size' having value 'small' or 'large'. No explanation.",
        "images": [img_base64],
        "stream": False
    }
    
    response = requests.post(api_url, json=payload)
    # Parse text trả về từ LLM tìm JSON và trả về kết quả
    return response.json().get("response")
```

### 2.4 Logic ra quyết định (`backend/decision_engine.py`)
```python
def process_rules(temp, humidity, mushroom_size):
    # Khai báo mặc định
    pump = False
    harvest_alert = False
    
    # R4 & R5: Trạng thái nấm từ AI
    if mushroom_size == "large":
        harvest_alert = True
        
    # R1, R2, R3: Trạng thái môi trường
    if humidity < 70.0:
        pump = True
    elif temp > 35.0:
        pump = True
        
    return {"pump": pump, "harvest_alert": harvest_alert}
```

### 2.5 Điều phối chính (`backend/main.py`)
- Khởi chạy vòng lặp chính (mỗi 30s):
  1. Đọc dữ liệu nhiệt độ, độ ẩm mới nhất nhận từ MQTT.
  2. Chụp ảnh từ Webcam USB.
  3. Gửi ảnh đến Ollama để nhận dạng kích cỡ (`small` / `large`).
  4. Chạy `decision_engine.py` để lấy trạng thái điều khiển.
  5. Publish kết quả điều khiển dưới dạng JSON lên topic `actuator/command`.
  6. Lưu log sự kiện và cập nhật cơ sở dữ liệu SQLite.

---

## 🌐 3. Web Dashboard (Flask - `dashboard/app.py`)
Nhiệm vụ: Cung cấp API cập nhật trạng thái và vẽ giao diện giám sát Real-time.

- **Backend Flask (`app.py`)**:
  - Endpoint `/api/status`: Trả về dữ liệu nhiệt ẩm hiện tại, trạng thái thiết bị và kết quả AI gần nhất.
  - Endpoint `/api/history`: Trả về mảng dữ liệu lịch sử phục vụ vẽ biểu đồ đường (Chart.js).
  - Giao diện HTML tĩnh được dựng bằng Vanilla CSS để tối ưu tốc độ và độ nhẹ.

- **Frontend JS (`dashboard.js`)**:
  - Sử dụng cơ chế Fetch API (hoặc WebSocket) tự động thăm dò (polling) mỗi 3-5 giây để cập nhật giá trị nhiệt ẩm dạng đồng hồ đo (Gauge).
  - Tự động thay đổi màu nền cảnh báo trên web sang nhấp nháy đỏ khi trạng thái `harvest_alert == true`.
