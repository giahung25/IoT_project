# 🚀 Hướng Dẫn Cài Đặt & Chạy Jetson Orin Nano

Tài liệu này hướng dẫn các bước thiết lập Jetson Orin Nano đóng vai trò là thiết bị Edge AI:
* Thu thập dữ liệu cảm biến từ ESP32 qua MQTT.
* Chụp ảnh từ Webcam USB.
* Chạy mô hình AI (Moondream qua Ollama) để phân tích kích thước nấm.
* Đẩy toàn bộ dữ liệu & trạng thái về máy tính PC đang chạy Web Dashboard.

---

## Bước 1: Cài đặt hệ sinh thái trên Jetson

Mở Terminal trên Jetson và chạy lần lượt các lệnh sau:

### 1.1 Cài đặt MQTT Broker (Mosquitto)
Dùng để giao tiếp nội bộ giữa ESP32 và Jetson:
```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients -y
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

### 1.2 Cài đặt thư viện Python
```bash
sudo apt install python3-pip -y
pip3 install paho-mqtt requests opencv-python
```

### 1.3 Cài đặt Ollama & Mô hình Moondream (Vision LLM)
```bash
# Cài đặt Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Tải mô hình nhận diện ảnh (moondream)
ollama run moondream
```
*(Lưu ý: Bấm Ctrl+D để thoát khỏi Ollama sau khi tải xong, nó sẽ chạy ngầm dưới nền).*

---

## Bước 2: Tải code điều khiển chính cho Jetson

Hãy tạo một file tên là `main_jetson.py` trên Jetson với nội dung sau:

```python
import paho.mqtt.client as mqtt
import requests
import cv2
import json
import time
import base64
import threading

# ================= CẤU HÌNH =================
PC_WEB_API = "http://192.168.1.12:5000/api/update"  # Đổi IP theo IP máy tính PC
OLLAMA_API = "http://localhost:11434/api/generate"
MQTT_BROKER = "localhost" # Mosquitto chạy ngay trên Jetson

# State lưu trữ tạm trên Jetson
current_temp = 0.0
current_hum = 0.0
mushroom_size = "unknown"

# ================= HÀM HỖ TRỢ =================
def capture_and_analyze():
    global mushroom_size
    print("📸 Đang chụp ảnh từ Webcam...")
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("❌ Lỗi Webcam!")
        return

    # Lưu ảnh ra file
    _, buffer = cv2.imencode('.jpg', frame)
    img_b64 = base64.b64encode(buffer).decode('utf-8')
    
    print("🧠 Đang gửi ảnh cho Ollama AI...")
    payload = {
        "model": "moondream",
        "prompt": "Analyze this mushroom image. Return JSON only with field 'size' having value 'small', 'medium', or 'large'.",
        "images": [img_b64],
        "stream": False
    }
    
    try:
        res = requests.post(OLLAMA_API, json=payload, timeout=30).json()
        response_text = res.get("response", "")
        # Phân tích text trả về (giả định trả về json dạng string)
        if "large" in response_text.lower():
            mushroom_size = "large"
        elif "medium" in response_text.lower():
            mushroom_size = "medium"
        else:
            mushroom_size = "small"
        print(f"✅ Kết quả AI: {mushroom_size}")
    except Exception as e:
        print(f"❌ Lỗi kết nối Ollama: {e}")

    # Gửi ngay cập nhật về PC
    send_to_pc()

def send_to_pc():
    data = {
        "temperature": current_temp,
        "humidity": current_hum,
        "mushroom_size": mushroom_size,
        "pump": current_hum < 70,             # Bật bơm nếu ẩm < 70%
        "harvest_alert": mushroom_size == "large", # Cảnh báo nếu nấm lớn
        "ai_confidence": 95, 
        "esp32_online": True
    }
    try:
        requests.post(PC_WEB_API, json=data, timeout=5)
        print("🚀 Đã đẩy dữ liệu về PC Server!")
    except Exception as e:
        print(f"⚠️ Lỗi đẩy dữ liệu PC: {e}")

# ================= MQTT HANDLER =================
def on_message(client, userdata, msg):
    global current_temp, current_hum
    try:
        payload = json.loads(msg.payload.decode())
        current_temp = payload.get("temperature", current_temp)
        current_hum = payload.get("humidity", current_hum)
        print(f"📡 Cảm biến: Temp={current_temp}C, Hum={current_hum}%")
        
        # Gửi dữ liệu về PC mỗi khi có cập nhật cảm biến
        send_to_pc()
    except Exception as e:
        pass

def mqtt_loop():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_BROKER, 1883, 60)
    client.subscribe("sensor/dht22")
    client.loop_forever()

# ================= MAIN RUN =================
if __name__ == "__main__":
    # Chạy MQTT lắng nghe ESP32 ở luồng riêng
    threading.Thread(target=mqtt_loop, daemon=True).start()
    
    # Vòng lặp chụp ảnh & AI định kỳ (mỗi 30 giây để test)
    while True:
        capture_and_analyze()
        time.sleep(30)
```

---

## Bước 3: Chạy hệ thống trên Jetson
Chỉ cần gọi:
```bash
python3 main_jetson.py
```
*(Hãy đảm bảo camera USB đã cắm vào Jetson, máy tính PC đã mở Web Server, và thay dòng `PC_WEB_API` trong code bằng IP máy tính của bạn).*
