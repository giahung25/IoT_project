# -*- coding: utf-8 -*-
import time
import requests
import os
from datetime import datetime

from backend.config import (
    WEBCAM_INDEX,
    IMAGE_SAVE_PATH,
    PC_WEB_API,
    SIMULATE_SENSOR
)
from backend.database import init_db, save_sensor_data, save_ai_log
from backend.mqtt_handler import start_mqtt_client, latest_sensor_data, publish_command
from backend.vision_analyzer import capture_image, analyze_mushroom_image
from backend.decision_engine import process_rules

def send_status_to_pc(temp, hum, size, pump_status, harvest_alert, conf, esp_online):
    """Gửi dữ liệu trạng thái tổng hợp dạng JSON tới PC Dashboard Web Server."""
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
        response = requests.post(PC_WEB_API, json=data, timeout=5)
        if response.status_code == 200:
            print(f"[PC Link] 🟢 Đã đồng bộ trạng thái thành công với PC Dashboard.")
        else:
            print(f"[PC Link] ❌ PC server trả về mã lỗi: {response.status_code}")
    except Exception as e:
        print(f"[PC Link] ❌ Không thể kết nối với PC Dashboard tại {PC_WEB_API}: {e}")

def send_sensor_only_status(temp, hum, esp_online):
    """Chỉ gửi dữ liệu cảm biến tới PC Dashboard Web Server để cập nhật biểu đồ theo thời gian thực."""
    data = {
        "temperature": temp,
        "humidity": hum,
        "esp32_online": esp_online
    }
    try:
        response = requests.post(PC_WEB_API, json=data, timeout=2)
    except Exception as e:
        # Im lặng khi không kết nối được để tránh ngập log cảm biến
        pass

def upload_image_to_pc(image_path):
    """Upload ảnh chụp mới nhất từ webcam biên lên PC Dashboard để hiển thị."""
    if not os.path.exists(image_path):
        return
    
    upload_url = PC_WEB_API.replace('/api/update', '/api/upload_image')
    try:
        with open(image_path, 'rb') as img_file:
            files = {'file': ('latest.jpg', img_file, 'image/jpeg')}
            response = requests.post(upload_url, files=files, timeout=10)
            if response.status_code == 200:
                print(f"[PC Link] 🟢 Đã upload ảnh thành công lên PC Dashboard.")
            else:
                print(f"[PC Link] ❌ PC server từ chối upload ảnh: {response.status_code}")
    except Exception as e:
        print(f"[PC Link] ❌ Không thể upload ảnh lên PC Dashboard: {e}")

def main():
    print("=================================================================")
    print("🚀 Bắt đầu khởi động Edge Server Python Backend trên Jetson...")
    print("=================================================================")
    
    # 1. Khởi tạo Database cục bộ
    init_db()
    
    # 2. Bắt đầu lắng nghe MQTT (hoặc chạy luồng sinh dữ liệu ảo)
    start_mqtt_client()
    
    # Đợi 1-2 giây cho luồng giả lập/MQTT bắt đầu nhận dữ liệu ổn định
    time.sleep(2)
    
    print("\n[System] 🟢 Hệ thống Edge Server Jetson đang hoạt động...")
    print("Nhấn Ctrl + C để dừng hệ thống.\n")
    
    cycle_count = 1
    last_auto_time = 0
    last_sensor_sync_time = 0
    auto_interval = 30
    sensor_sync_interval = 5
    
    from backend.mqtt_handler import get_capture_mode, check_and_reset_manual_capture
    
    try:
        while True:
            current_time = time.time()
            mode = get_capture_mode()
            is_manual_triggered = check_and_reset_manual_capture()
            
            # 3. Đồng bộ dữ liệu cảm biến định kỳ lên PC (mỗi 5 giây)
            if current_time - last_sensor_sync_time >= sensor_sync_interval:
                temp = latest_sensor_data["temperature"]
                hum = latest_sensor_data["humidity"]
                esp_online = latest_sensor_data["esp32_online"]
                
                # Lưu vào database cục bộ
                save_sensor_data(temp, hum)
                
                # Đồng bộ nhanh chỉ dữ liệu cảm biến để cập nhật biểu đồ
                send_sensor_only_status(temp, hum, esp_online)
                last_sensor_sync_time = current_time
            
            # 4. Kiểm tra điều kiện chụp ảnh và phân tích Vision AI (Camera + Ollama)
            should_run_vision = False
            trigger_reason = ""
            
            if is_manual_triggered:
                should_run_vision = True
                trigger_reason = "Chụp thủ công (Yêu cầu từ PC)"
            elif mode == "auto" and (current_time - last_auto_time >= auto_interval):
                should_run_vision = True
                trigger_reason = f"Tự động (Chu Kỳ #{cycle_count})"
                last_auto_time = current_time
            
            if should_run_vision:
                print(f"\n--- [{trigger_reason}] Bắt đầu xử lý lúc: {datetime.now().strftime('%H:%M:%S')} ---")
                
                # Lấy dữ liệu cảm biến hiện thời
                temp = latest_sensor_data["temperature"]
                hum = latest_sensor_data["humidity"]
                esp_online = latest_sensor_data["esp32_online"]
                
                # Chụp ảnh từ camera (hoặc lấy từ dataset giả lập nếu không có camera)
                img_success = capture_image(WEBCAM_INDEX, IMAGE_SAVE_PATH)
                
                mushroom_size = "unknown"
                ai_confidence = 0
                
                if img_success:
                    # Upload ảnh lên PC Dashboard
                    upload_image_to_pc(IMAGE_SAVE_PATH)
                    
                    # Gọi Ollama phân tích hình ảnh nấm
                    mushroom_size, ai_confidence = analyze_mushroom_image(IMAGE_SAVE_PATH)
                    
                    # Lưu log kết quả AI vào Database cục bộ
                    save_ai_log(IMAGE_SAVE_PATH, mushroom_size, ai_confidence)
                else:
                    print("[Vision] ⚠️ Bỏ qua chu kỳ phân tích AI do không có ảnh.")
                
                # Chạy Decision Engine để lấy lệnh điều khiển
                decisions = process_rules(temp, hum, mushroom_size)
                pump_status = decisions["pump"]
                harvest_alert = decisions["harvest_alert"]
                
                print(f"[Decision] Kết quả: Bơm = {pump_status}, Cảnh báo thu hoạch = {harvest_alert}")
                
                # Gửi lệnh điều khiển ngược về ESP32 qua MQTT
                publish_command(pump_status, harvest_alert)
                
                # Đồng bộ toàn bộ trạng thái lên PC Dashboard Web Server
                send_status_to_pc(
                    temp=temp,
                    hum=hum,
                    size=mushroom_size,
                    pump_status=pump_status,
                    harvest_alert=harvest_alert,
                    conf=ai_confidence,
                    esp_online=esp_online
                )
                
                if mode == "auto":
                    cycle_count += 1
            
            # Lặp sau mỗi 1 giây để kiểm tra trigger thủ công nhanh chóng
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n=================================================================")
        print("🛑 Đã nhận lệnh dừng từ người dùng. Đang thoát hệ thống...")
        print("=================================================================")

if __name__ == '__main__':
    main()

