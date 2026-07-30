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
# API endpoint của Ollama chạy trên Jetson Orin Nano
OLLAMA_API_URL = "http://localhost:11434/api/generate"
# Model Vision siêu nhẹ moondream đã được test ổn định
VISION_MODEL = "moondream"

# Chỉ số camera USB (thường 0 là USB Webcam)
WEBCAM_INDEX = 0

# Cấu hình IP Camera Imou (SN: 88B44BKPSF16A26, User: admin, Safety Code: L201622F)
# Định dạng chuẩn RTSP Imou/Dahua: rtsp://admin:L201622F@<IP_ADDRESS>:554/cam/realmonitor?channel=1&subtype=0
ip_cam_ip = os.environ.get("IP_CAM_IP", "192.168.1.5")
default_imou_rtsp = f"rtsp://admin:L201622F@{ip_cam_ip}:554/cam/realmonitor?channel=1&subtype=0"
IP_CAM_RTSP_URL = os.environ.get("IP_CAM_URL", default_imou_rtsp)

# Nguồn camera mặc định: "webcam", "ip_cam", hoặc "auto"
DEFAULT_CAMERA_SOURCE = "webcam"

# Độ phân giải chụp ảnh camera
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

# Ngưỡng độ sáng trung bình tối thiểu (0-255). Nếu dưới ngưỡng này, coi như ban đêm/thiếu sáng.
LOW_LIGHT_THRESHOLD = 30

# ==========================================
# Lưu trữ dữ liệu
# ==========================================
# File cơ sở dữ liệu SQLite cục bộ trên Jetson
DB_PATH = os.path.join(BACKEND_DIR, "mushroom_monitor.db")

# Đường dẫn lưu ảnh chụp gần nhất từ Webcam
IMAGE_SAVE_PATH = os.path.join(BACKEND_DIR, "latest.jpg")

# Thư mục lưu lịch sử ảnh chụp trên Jetson
HISTORY_DIR = os.path.join(BACKEND_DIR, "captures")

# ==========================================
# Chế độ Giả lập / Mocking
# ==========================================
# Bật True để giả lập dữ liệu cảm biến (Nhiệt độ & Độ ẩm) khi ESP32 chưa sẵn sàng.
# Khi ESP32 chạy thật qua BLE-MQTT Bridge, chuyển giá trị này thành False.
SIMULATE_SENSOR = False


