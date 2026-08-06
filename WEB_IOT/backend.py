from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timezone
import os
import shutil
import json
import random
import time
import threading

app = Flask(__name__, static_folder='dashboard')
CORS(app)

@app.after_request
def add_no_cache_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


import sys
simulation_mode = os.environ.get("SIMULATION_MODE", "0") == "1"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.decision_engine import calculate_vpd, evaluate_growth_zone


# Global state to store the latest status and history
current_status = {
    "temperature":    0.0,
    "humidity":       0.0,
    "mushroom_size":  "unknown",
    "pump":           False,
    "harvest_alert":  False,
    "ai_confidence":  0,
    "esp32_online":   False,
    "last_updated":   datetime.now(timezone.utc).isoformat(),
    "capture_mode":   "auto",        # "auto" hoặc "manual"
    "camera_source":  "auto",        # "auto", "ip_cam", hoặc "webcam"
    "active_camera":  "Simulation (Dataset)",
    "vpd":            0.45,
    "vp_sat":         0.90,
    "vp_act":         0.45,
    "growth_zone":    "🟢 Vùng Tối Ưu (Optimal)",
    "zone_code":      "optimal",
    "health_score":   95,
    "estimated_harvest_hours": 18
}


history_data = []
ai_history_data = []

def publish_mqtt_control(payload):
    """Gửi lệnh điều khiển MQTT tới broker của Jetson (hoặc localhost khi chạy giả lập)."""
    try:
        import paho.mqtt.publish as publish
        broker_ip = os.environ.get("JETSON_IP", "192.168.55.1") if not simulation_mode else "localhost"
        publish.single("mushroom/control", payload=json.dumps(payload), hostname=broker_ip, port=1883)
        print(f"[Backend MQTT] Đã gửi lệnh điều khiển tới Broker ({broker_ip}): {payload}")
    except Exception as e:
        print(f"[Backend MQTT] ❌ Gửi lệnh MQTT thất bại: {e}")


def simulate_capture():
    """Sinh ảnh và kết quả AI giả lập cục bộ (Dùng cho Chế độ Giả Lập)."""
    global current_status, ai_history_data
    static_images_dir = os.path.join(app.static_folder, 'static', 'images')

    # Ưu tiên lấy ảnh từ dataset thật trong thư mục data/
    data_dir = os.path.join(PROJECT_ROOT, 'data')
    valid_mock_images = []

    if os.path.exists(data_dir):
        for root, _, files in os.walk(data_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    valid_mock_images.append(os.path.join(root, file))

    size = random.choice(["small", "large"])
    conf = random.randint(85, 97)

    if valid_mock_images:
        src_path = random.choice(valid_mock_images)
        os.makedirs(static_images_dir, exist_ok=True)
        dest_path = os.path.join(static_images_dir, 'latest.jpg')
        try:
            shutil.copy(src_path, dest_path)

            timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            history_dir = os.path.join(static_images_dir, 'history')
            os.makedirs(history_dir, exist_ok=True)
            history_filename = f"latest_{timestamp_str}.jpg"
            history_path = os.path.join(history_dir, history_filename)
            shutil.copy(dest_path, history_path)

            current_status["latest_image_url"] = f"/static/images/history/{history_filename}"
            current_status["camera_image"] = f"/static/images/history/{history_filename}"
            current_status["active_camera"] = "Simulation (Dataset)"
        except Exception as e:
            print(f"[Simulator] Lỗi copy ảnh dataset: {e}")


            
    current_status["mushroom_size"] = size
    current_status["ai_confidence"] = conf
    current_status["pump"] = current_status["humidity"] < 70 or current_status["temperature"] > 35
    current_status["harvest_alert"] = size == "large"
    current_status["last_updated"] = datetime.now(timezone.utc).isoformat()
    
    ai_entry = {
        "timestamp": current_status["last_updated"],
        "mushroom_size": size,
        "ai_confidence": conf,
        "image_path": current_status.get("latest_image_url", "/static/images/latest.jpg")
    }
    ai_history_data.append(ai_entry)
    
    if len(ai_history_data) > 15:
        old_entry = ai_history_data.pop(0)
        old_img_path = old_entry.get("image_path", "")
        if "history/" in old_img_path:
            local_img_path = os.path.join(app.static_folder, old_img_path.lstrip('/'))
            if os.path.exists(local_img_path):
                try:
                    os.remove(local_img_path)
                except:
                    pass
    print(f"[Simulator] 📸 Chụp ảnh & Phân tích nấm (Giả Lập): Kích thước = {size}, Độ tin cậy = {conf}%")

last_real_sensor_time = 0

def local_simulator():
    """Thread chạy ngầm sinh dữ liệu cảm biến và tự động chụp (nếu bật Auto) ở chế độ Giả Lập."""
    global current_status, last_real_sensor_time
    print("[Simulator] 🟢 Khởi chạy luồng giả lập dữ liệu cục bộ...")
    t = 27.0
    h = 75.0

    cycle_counter = 0
    while True:
        # Chỉ sinh dữ liệu nhiệt/ẩm ảo nếu trong 15s qua KHÔNG có dữ liệu thực tế từ Jetson/ESP32 đẩy lên
        if time.time() - last_real_sensor_time > 15:
            t += random.uniform(-0.2, 0.2)
            t = max(24.0, min(35.0, t))
            h += random.uniform(-1.5, 1.5)
            h = max(60.0, min(95.0, h))

            current_status["temperature"] = round(t, 1)
            current_status["humidity"] = round(h, 1)
            current_status["esp32_online"] = simulation_mode
            current_status["last_updated"] = datetime.now(timezone.utc).isoformat()

            # Tính toán VPD và Vùng Sinh Trưởng
            vpd, vp_sat, vp_act = calculate_vpd(t, h)
            zone_info = evaluate_growth_zone(t, h, vpd)
            current_status["vpd"] = vpd
            current_status["vp_sat"] = vp_sat
            current_status["vp_act"] = vp_act
            current_status["growth_zone"] = zone_info["zone_name"]
            current_status["zone_code"] = zone_info["zone_code"]
            current_status["health_score"] = zone_info["health_score"]
            current_status["estimated_harvest_hours"] = 18 if current_status["mushroom_size"] == "small" else 0

            # Thêm vào history_data
            history_entry = {
                "timestamp": current_status["last_updated"],
                "temperature": current_status["temperature"],
                "humidity": current_status["humidity"]
            }
            history_data.append(history_entry)
            if len(history_data) > 48:
                history_data.pop(0)

            
        # 2. Tự động chụp mỗi 15s nếu đang ở chế độ auto
        if current_status["capture_mode"] == "auto":
            if cycle_counter % 3 == 0:  # 5s * 3 = 15s
                simulate_capture()
                
        cycle_counter += 1
        time.sleep(5)



# ==========================================
# Giao diện tĩnh (Frontend)
# ==========================================
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# ==========================================
# API cho Frontend lấy dữ liệu (GET)
# ==========================================
@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(current_status)

@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify(history_data)

@app.route('/api/ai-history', methods=['GET'])
def get_ai_history():
    return jsonify(ai_history_data)


# ==========================================
# API cho Jetson đẩy dữ liệu lên (POST)
# ==========================================
@app.route('/api/update', methods=['POST'])
def update_data():
    global current_status, history_data, ai_history_data, last_real_sensor_time

    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    # Cập nhật mốc thời gian nhận dữ liệu cảm biến thực tế
    if "temperature" in data or "humidity" in data:
        last_real_sensor_time = time.time()

    # Cập nhật current_status
    for key in current_status.keys():
        if key in data and data[key] is not None:
            current_status[key] = data[key]


    current_status["last_updated"] = datetime.now(timezone.utc).isoformat()

    # Tính toán lại chỉ số VPD và Vùng sinh trưởng
    t = current_status.get("temperature", 27.0)
    h = current_status.get("humidity", 75.0)
    vpd, vp_sat, vp_act = calculate_vpd(t, h)
    zone_info = evaluate_growth_zone(t, h, vpd)
    current_status["vpd"] = vpd
    current_status["vp_sat"] = vp_sat
    current_status["vp_act"] = vp_act
    current_status["growth_zone"] = zone_info["zone_name"]
    current_status["zone_code"] = zone_info["zone_code"]
    current_status["health_score"] = zone_info["health_score"]
    current_status["estimated_harvest_hours"] = 18 if current_status.get("mushroom_size") == "small" else 0

    if not current_status.get("camera_image"):
        current_status["camera_image"] = current_status.get("latest_image_url", "/static/images/latest.jpg")

    
    # Cập nhật lịch sử (chỉ lưu nhiệt độ và độ ẩm cho biểu đồ)
    if "temperature" in data and "humidity" in data:
        history_entry = {
            "timestamp": current_status["last_updated"],
            "temperature": current_status["temperature"],
            "humidity": current_status["humidity"]
        }
        history_data.append(history_entry)
        
        # Giữ tối đa 48 bản ghi (4 giờ, mỗi 5 phút)
        if len(history_data) > 48:
            history_data.pop(0)
            
    # Cập nhật lịch sử nhận dạng AI
    if "mushroom_size" in data and data["mushroom_size"] != "unknown":
        img_url = current_status.get("latest_image_url", "/static/images/latest.jpg")
        
        ai_entry = {
            "timestamp": current_status["last_updated"],
            "mushroom_size": data["mushroom_size"],
            "ai_confidence": data.get("ai_confidence", 0),
            "image_path": img_url
        }
        ai_history_data.append(ai_entry)
        
        # Tự động dọn dẹp ảnh cũ để tiết kiệm dung lượng (giữ tối đa 15 bản ghi)
        if len(ai_history_data) > 15:
            old_entry = ai_history_data.pop(0)
            old_img_path = old_entry.get("image_path", "")
            if "history/" in old_img_path:
                local_img_path = os.path.join(app.static_folder, old_img_path.lstrip('/'))
                if os.path.exists(local_img_path):
                    try:
                        os.remove(local_img_path)
                        print(f"[Backend] Deleted old history image: {local_img_path}")
                    except Exception as e:
                        print(f"[Backend] Error deleting old image: {e}")
            
    return jsonify({"message": "Data updated successfully", "status": current_status}), 200


# ==========================================
# API cho Jetson upload ảnh camera lên (POST)
# ==========================================
@app.route('/api/upload_image', methods=['POST'])
def upload_image():
    global current_status
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Tạo thư mục static/images nếu chưa có
    dest_dir = os.path.join(app.static_folder, 'static', 'images')
    os.makedirs(dest_dir, exist_ok=True)
    
    # Lưu đè lên file latest.jpg
    dest_path = os.path.join(dest_dir, 'latest.jpg')
    try:
        file.save(dest_path)
        
        # Đồng thời lưu một bản sao lịch sử kèm timestamp
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        history_dir = os.path.join(dest_dir, 'history')
        os.makedirs(history_dir, exist_ok=True)
        
        history_filename = f"latest_{timestamp_str}.jpg"
        history_path = os.path.join(history_dir, history_filename)
        shutil.copy(dest_path, history_path)
        
        # Lưu URL ảnh lịch sử mới nhất vào state để ghi nhận trong update_data
        current_status["latest_image_url"] = f"/static/images/history/{history_filename}"
        current_status["camera_image"] = f"/static/images/history/{history_filename}"

        return jsonify({"message": "Image uploaded successfully", "path": f"/static/images/history/{history_filename}"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to save image: {str(e)}"}), 500



# ==========================================
# API Cấu hình (Tập trung thay đổi chế độ chụp)
# ==========================================
@app.route('/api/settings', methods=['POST'])
def update_settings():
    global current_status
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400
        
    if "capture_mode" in data:
        current_status["capture_mode"] = data["capture_mode"]
        publish_mqtt_control({"capture_mode": data["capture_mode"]})

    if "camera_source" in data:
        current_status["camera_source"] = data["camera_source"]
        publish_mqtt_control({"camera_source": data["camera_source"]})
        
    if data.get("action") == "capture":
        if simulation_mode:
            # Chạy giả lập chụp ngay lập tức trên luồng phụ
            threading.Thread(target=simulate_capture).start()
        else:
            # Gửi lệnh MQTT kích hoạt Jetson chụp ảnh thật kèm theo camera_source đã chọn
            publish_mqtt_control({
                "action": "capture",
                "camera_source": current_status.get("camera_source", "auto")
            })
            
    return jsonify({"message": "Settings updated", "status": current_status}), 200



if __name__ == '__main__':
    if simulation_mode:
        sim_thread = threading.Thread(target=local_simulator, daemon=True)
        sim_thread.start()
        
    # Lắng nghe trên mọi IP để Jetson có thể gửi dữ liệu đến
    app.run(host='0.0.0.0', port=5000, debug=True)


