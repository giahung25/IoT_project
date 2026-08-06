import requests
import time
import random

# Đổi IP này thành IP của máy tính bạn (ví dụ: 192.168.1.12 hoặc 192.168.55.100 nếu cắm cáp USB Jetson)
PC_SERVER_URL = "http://192.168.1.12:5000/api/update"

def send_data_to_pc(temp, hum, size, pump_status, harvest_alert, conf, esp_online):
    data = {
        "temperature": temp,
        "humidity": hum,
        "mushroom_size": size,
        "pump": pump_status,
        "harvest_alert": harvest_alert,
        "ai_confidence": conf,
        "esp32_online": esp_online
    }
    
    try:
        response = requests.post(PC_SERVER_URL, json=data, timeout=5)
        print("Data sent successfully:", response.status_code, response.json())
    except Exception as e:
        print("Failed to send data:", e)

if __name__ == '__main__':
    while True:
        # Giả lập Jetson đọc dữ liệu và xử lý Vision AI
        print("Phân tích ảnh và cập nhật dữ liệu...")
        
        t = round(random.uniform(25.0, 28.0), 1)
        h = round(random.uniform(80.0, 95.0), 1)
        s = random.choice(["small", "medium", "large"])
        
        send_data_to_pc(temp=t, hum=h, size=s, pump_status=False, harvest_alert=(s=="large"), conf=92, esp_online=True)
        
        # Đợi 5 giây trước khi gửi lần tiếp theo
        time.sleep(5)
