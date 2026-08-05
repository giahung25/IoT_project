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

from backend.decision_engine import calculate_vpd, evaluate_growth_zone

FIREBASE_RTDB_URL = "https://agrishroom-edge-default-rtdb.asia-southeast1.firebasedatabase.app/status.json"

def get_image_base64(image_path, max_dim=400, quality=70):
    """Mã hóa file ảnh thành chuỗi Base64 Data URI với nén dung lượng phù hợp cho Firebase."""
    if not os.path.exists(image_path):
        return None
    try:
        import cv2
        import base64
        img = cv2.imread(image_path)
        if img is None:
            return None
        h, w = img.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / float(max(h, w))
            img = cv2.resize(img, (int(w * scale), int(h * scale)))
        ret, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if ret:
            b64_str = base64.b64encode(buffer).decode('utf-8')
            return f"data:image/jpeg;base64,{b64_str}"
    except Exception as e:
        print(f"[Firebase] ⚠️ Lỗi mã hóa base64 ảnh: {e}")
    return None

def send_to_firebase(data):
    """Gửi/Cập nhật (PATCH) dữ liệu thời gian thực trực tiếp tới Firebase Realtime Database trên Đám Mây."""
    try:
        data_copy = dict(data)
        data_copy["last_updated"] = datetime.utcnow().isoformat() + "Z"
        # Dùng PATCH để cập nhật (merge) từng trường dữ liệu mà KHÔNG xóa các trường hiện có trên Firebase
        requests.patch(FIREBASE_RTDB_URL, json=data_copy, timeout=5)
    except Exception as e:
        print(f"[Firebase] ❌ Lỗi kết nối Firebase RTDB: {e}")

def send_status_to_pc(temp, hum, size, pump_status, harvest_alert, conf, esp_online, active_camera="N/A", camera_source="auto", grow_light=False, cooling_fan=False, vent_gate=False, **kwargs):
    """Gửi dữ liệu trạng thái tổng hợp dạng JSON tới PC Dashboard & Đám Mây Firebase."""
    vpd, vp_sat, vp_act = calculate_vpd(temp, hum)
    zone_info = evaluate_growth_zone(temp, hum, vpd)

    data = {
        "temperature": temp,
        "humidity": hum,
        "co2_ppm": latest_sensor_data.get("co2_ppm", 400),
        "light_lux": latest_sensor_data.get("light_lux", 0),
        "sensor_source": latest_sensor_data.get("sensor_source", "Auto-Detect"),
        "mushroom_size": size,
        "pump": pump_status,
        "harvest_alert": harvest_alert,
        "grow_light": grow_light,
        "cooling_fan": cooling_fan,
        "vent_gate": vent_gate,
        "ai_confidence": conf,
        "esp32_online": esp_online,
        "active_camera": active_camera,
        "camera_source": camera_source,
        "vpd": vpd,
        "vp_sat": vp_sat,
        "vp_act": vp_act,
        "growth_zone": zone_info["zone_name"],
        "zone_code": zone_info["zone_code"],
        "zone_desc": zone_info["zone_desc"],
        "health_score": zone_info["health_score"],
        "estimated_harvest_hours": 18 if size == "small" else 0
    }

    
    # Mã hóa ảnh camera mới nhất dạng Base64 để hiển thị trực tiếp thời gian thực trên Firebase / Web
    img_b64 = get_image_base64(IMAGE_SAVE_PATH)
    if img_b64:
        data["camera_image"] = img_b64
        data["latest_image_url"] = img_b64
    
    send_to_firebase(data)
    
    try:
        response = requests.post(PC_WEB_API, json=data, timeout=5)
        if response.status_code == 200:
            print(f"[PC Link] 🟢 Đã đồng bộ trạng thái thành công với PC Dashboard.")
        else:
            print(f"[PC Link] ❌ PC server trả về mã lỗi: {response.status_code}")
    except Exception as e:
        print(f"[PC Link] ❌ Không thể kết nối với PC Dashboard tại {PC_WEB_API}: {e}")


def send_sensor_only_status(temp, hum, esp_online, active_camera="N/A", camera_source="auto"):
    """Gửi dữ liệu cảm biến và nguồn camera thực tế tới PC Dashboard & Firebase."""
    vpd, vp_sat, vp_act = calculate_vpd(temp, hum)
    zone_info = evaluate_growth_zone(temp, hum, vpd)

    data = {
        "temperature": temp,
        "humidity": hum,
        "co2_ppm": latest_sensor_data.get("co2_ppm", 400),
        "light_lux": latest_sensor_data.get("light_lux", 0),
        "sensor_source": latest_sensor_data.get("sensor_source", "Auto-Detect"),
        "esp32_online": esp_online,
        "active_camera": active_camera,
        "camera_source": camera_source,
        "vpd": vpd,
        "vp_sat": vp_sat,
        "vp_act": vp_act,
        "growth_zone": zone_info["zone_name"],
        "zone_code": zone_info["zone_code"],
        "health_score": zone_info["health_score"]
    }
    send_to_firebase(data)
    try:
        hist_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "temperature": temp,
            "humidity": hum
        }
        requests.post("https://agrishroom-edge-default-rtdb.asia-southeast1.firebasedatabase.app/history.json", json=hist_entry, timeout=3)
    except Exception:
        pass

    try:
        response = requests.post(PC_WEB_API, json=data, timeout=2)
    except Exception as e:
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
    
    from backend.mqtt_handler import get_capture_mode, check_and_reset_manual_capture, get_camera_source
    
    try:
        while True:
            current_time = time.time()
            mode = get_capture_mode()
            cam_src = get_camera_source()
            is_manual_triggered = check_and_reset_manual_capture()
            
            # 3. Đồng bộ dữ liệu cảm biến định kỳ lên PC (mỗi 5 giây)
            if current_time - last_sensor_sync_time >= sensor_sync_interval:
                temp = latest_sensor_data["temperature"]
                hum = latest_sensor_data["humidity"]
                esp_online = latest_sensor_data["esp32_online"]
                
                # Lưu vào database cục bộ
                save_sensor_data(temp, hum)
                
                # Đồng bộ nhanh dữ liệu cảm biến & nguồn camera để cập nhật giao diện PC
                send_sensor_only_status(temp, hum, esp_online, active_camera=cam_src, camera_source=cam_src)
                last_sensor_sync_time = current_time

            
            # 4. Kiểm tra điều kiện chụp ảnh và phân tích Vision AI (Camera + Ollama)
            should_run_vision = False
            trigger_reason = ""
            
            if is_manual_triggered:
                should_run_vision = True
                trigger_reason = f"Chụp thủ công (Yêu cầu từ PC - Nguồn: {cam_src})"
            elif mode == "auto" and (current_time - last_auto_time >= auto_interval):
                should_run_vision = True
                trigger_reason = f"Tự động (Chu Kỳ #{cycle_count} - Nguồn: {cam_src})"
                last_auto_time = current_time
            
            if should_run_vision:
                print(f"\n--- [{trigger_reason}] Bắt đầu xử lý lúc: {datetime.now().strftime('%H:%M:%S')} ---")
                
                # Lấy dữ liệu cảm biến hiện thời
                temp = latest_sensor_data["temperature"]
                hum = latest_sensor_data["humidity"]
                esp_online = latest_sensor_data["esp32_online"]
                
                # Chụp ảnh từ camera nguồn được chọn
                img_success, active_source, is_well_lit, luminance = capture_image(cam_src, IMAGE_SAVE_PATH)
                
                mushroom_size = "unknown"
                ai_confidence = 0
                
                if img_success:
                    # Upload ảnh lên PC Dashboard
                    upload_image_to_pc(IMAGE_SAVE_PATH)
                    
                    if is_well_lit:
                        # Gọi Ollama phân tích hình ảnh nấm
                        mushroom_size, ai_confidence = analyze_mushroom_image(IMAGE_SAVE_PATH)
                        # Lưu log kết quả AI vào Database cục bộ
                        save_ai_log(IMAGE_SAVE_PATH, mushroom_size, ai_confidence)
                    else:
                        print(f"[Vision] 🌙 Bỏ qua phân tích Vision AI do thiếu sáng (Độ sáng: {luminance}).")
                else:
                    print("[Vision] ⚠️ Bỏ qua chu kỳ phân tích AI do không chụp được ảnh.")
                
                # Chạy Decision Engine để lấy lệnh điều khiển
                co2_val = latest_sensor_data.get("co2_ppm", 400)
                light_val = latest_sensor_data.get("light_lux", 500)
                decisions = process_rules(temp, hum, mushroom_size, co2_ppm=co2_val, light_lux=light_val)
                pump_status = decisions["pump"]
                harvest_alert = decisions["harvest_alert"]
                grow_light = decisions["grow_light"]
                cooling_fan = decisions["cooling_fan"]
                vent_gate = decisions["vent_gate"]
                
                print(f"[Decision] Kết quả: Bơm={pump_status}, Cảnh báo={harvest_alert}, Đèn={grow_light}, Quạt={cooling_fan}, Cửa gió={vent_gate}")
                
                # Gửi lệnh điều khiển ngược về ESP32 qua MQTT -> BLE
                publish_command(
                    pump_status=pump_status,
                    harvest_alert=harvest_alert,
                    grow_light=grow_light,
                    cooling_fan=cooling_fan,
                    vent_gate=vent_gate
                )
                
                # Đồng bộ toàn bộ trạng thái lên PC Dashboard Web Server & Firebase
                send_status_to_pc(
                    temp=temp,
                    hum=hum,
                    size=mushroom_size,
                    pump_status=pump_status,
                    harvest_alert=harvest_alert,
                    conf=ai_confidence,
                    esp_online=esp_online,
                    active_camera=active_source,
                    camera_source=cam_src,
                    grow_light=grow_light,
                    cooling_fan=cooling_fan,
                    vent_gate=vent_gate
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

