# -*- coding: utf-8 -*-
import os

# Đường dẫn tương đối dựa trên vị trí của file config.py
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

# ==========================================
# Cấu hình Kết nối & Giao thức
# ==========================================
# Địa chỉ MQTT Broker chạy trên Jetson
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_SUB_TOPIC = "sensor/data"
MQTT_PUB_TOPIC = "actuator/command"

# Endpoint gửi dữ liệu tổng hợp về PC Dashboard (Đọc động từ môi trường truyền qua SSH)
pc_host = os.environ.get("PC_IP", "192.168.55.100")
PC_WEB_API = f"http://{pc_host}:5000/api/update"


# ==========================================
# Cấu hình Vision AI & Camera
# ==========================================
# API endpoint của Ollama chạy trên Jetson Orin Nano (truy cập từ PC qua mạng ảo USB)
OLLAMA_API_URL = "http://192.168.55.1:11434/api/generate"
# Model Vision siêu nhẹ moondream đã được test ổn định
VISION_MODEL = "moondream"

# Chỉ số camera (thường 0 là USB Webcam)
WEBCAM_INDEX = 0

# ==========================================
# Lưu trữ dữ liệu
# ==========================================
# File cơ sở dữ liệu SQLite cục bộ trên Jetson
DB_PATH = os.path.join(BACKEND_DIR, "mushroom_monitor.db")

# Đường dẫn lưu ảnh chụp gần nhất từ Webcam
IMAGE_SAVE_PATH = os.path.join(BACKEND_DIR, "latest.jpg")

# ==========================================
# Chế độ Giả lập / Mocking
# ==========================================
# Bật True để giả lập dữ liệu cảm biến (Nhiệt độ & Độ ẩm) khi ESP32 chưa sẵn sàng.
# Khi ESP32 chạy thật, chuyển giá trị này thành False.
SIMULATE_SENSOR = True
