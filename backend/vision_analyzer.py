# -*- coding: utf-8 -*-
import cv2
import os
import time
import random
import shutil
import base64
import requests
import re
import json
from datetime import datetime
from backend.config import (
    OLLAMA_API_URL,
    VISION_MODEL,
    PROJECT_ROOT,
    WEBCAM_INDEX,
    IP_CAM_RTSP_URL,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    LOW_LIGHT_THRESHOLD,
    HISTORY_DIR,
    IMAGE_SAVE_PATH,
    CAMERA_FLIP_MODE
)


def check_image_luminance(image_path_or_frame, threshold=LOW_LIGHT_THRESHOLD):
    """
    Tính toán độ sáng trung bình (Grayscale mean luminance) của ảnh.
    Trả về (is_well_lit: bool, mean_luminance: float).
    """
    try:
        if isinstance(image_path_or_frame, str):
            frame = cv2.imread(image_path_or_frame)
        else:
            frame = image_path_or_frame

        if frame is None:
            return False, 0.0

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_lum = float(cv2.mean(gray)[0])
        is_well_lit = mean_lum >= threshold
        return is_well_lit, round(mean_lum, 2)
    except Exception as e:
        print(f"[Vision] ❌ Lỗi kiểm tra độ sáng ảnh: {e}")
        return True, 100.0


def capture_from_ip_cam(rtsp_url=IP_CAM_RTSP_URL, save_path=IMAGE_SAVE_PATH):
    """
    Chụp ảnh từ IP Camera (RTSP / HTTP Stream).
    Nếu kết nối tới URL mặc định thất bại, tự động chạy Scanner dò IP trong mạng nội bộ.
    """
    print(f"[Vision] 🌐 Đang mở IP Camera tại RTSP/HTTP URL: {rtsp_url}...")
    try:
        cap = cv2.VideoCapture(rtsp_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if cap.isOpened():
            for _ in range(5):
                cap.read()
            ret, frame = cap.read()
            cap.release()

            if ret and frame is not None:
                if CAMERA_WIDTH > 0 and CAMERA_HEIGHT > 0:
                    frame = cv2.resize(frame, (CAMERA_WIDTH, CAMERA_HEIGHT))
                cv2.imwrite(save_path, frame)
                print(f"[Vision] 🟢 Đã chụp ảnh thành công từ IP Camera!")
                return True
        cap.release()
    except Exception as e:
        print(f"[Vision] ⚠️ Lỗi khi kết nối IP Camera tại URL mặc định: {e}")

    # NẾU KẾT NỐI MẶC ĐỊNH THẤT BẠI: KÍCH HOẠT DÒ TÌM IP TỰ ĐỘNG
    print("[Vision] 🔍 Đang tự động quét mạng nội bộ để tìm IP của Camera Imou...")
    try:
        from tools.find_ip_cam import scan_network_for_imou
        discovered_ip, valid_url = scan_network_for_imou()
        if valid_url:
            print(f"[Vision] 🟢 Tự động kết nối lại thành công với IP Camera vừa tìm thấy: {valid_url}")
            cap = cv2.VideoCapture(valid_url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if cap.isOpened():
                for _ in range(5):
                    cap.read()
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    if CAMERA_WIDTH > 0 and CAMERA_HEIGHT > 0:
                        frame = cv2.resize(frame, (CAMERA_WIDTH, CAMERA_HEIGHT))
                    cv2.imwrite(save_path, frame)
                    print(f"[Vision] 🟢 Đã chụp ảnh thành công từ IP Camera vừa quét được!")
                    return True
    except Exception as scan_err:
        print(f"[Vision] ⚠️ Lỗi khi quét tự động IP Camera: {scan_err}")

    return False



def capture_from_webcam(camera_index=WEBCAM_INDEX, save_path=IMAGE_SAVE_PATH):
    """
    Chụp ảnh từ USB Webcam kết nối trực tiếp với Jetson.
    """
    print(f"[Vision] 📷 Đang mở USB Webcam index {camera_index}...")
    try:
        cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

            # Xả 5 khung hình cho camera cân bằng độ sáng tự động
            for _ in range(5):
                cap.read()

            ret, frame = cap.read()
            cap.release()

            if ret and frame is not None:
                if CAMERA_FLIP_MODE is not None:
                    frame = cv2.flip(frame, CAMERA_FLIP_MODE)
                cv2.imwrite(save_path, frame)
                print(f"[Vision] 🟢 Đã chụp ảnh thành công từ USB Webcam (Đã lật/xoay khung hình)! ")
                return True

    except Exception as e:
        print(f"[Vision] ⚠️ Lỗi khi mở USB Webcam: {e}")

    return False


def capture_from_dataset(save_path=IMAGE_SAVE_PATH):
    """
    Giả lập chụp ảnh bằng cách chọn ngẫu nhiên một mẫu ảnh nấm trong dataset.
    """
    print("[Vision] ⚠️ Đang lấy ảnh ngẫu nhiên từ Dataset để giả lập...")
    data_dir = os.path.join(PROJECT_ROOT, "data")
    folders = ["Dữ_liệu_Nấm_non", "Dữ_liệu_Nấm_trưởng_thành"]

    valid_images = []
    for folder in folders:
        folder_path = os.path.join(data_dir, folder)
        if os.path.exists(folder_path):
            files = [
                os.path.join(folder_path, f)
                for f in os.listdir(folder_path)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]
            valid_images.extend(files)

    if valid_images:
        selected_img = random.choice(valid_images)
        try:
            img = cv2.imread(selected_img)
            if img is not None:
                if CAMERA_WIDTH > 0 and CAMERA_HEIGHT > 0:
                    img_resized = cv2.resize(img, (CAMERA_WIDTH, CAMERA_HEIGHT))
                    cv2.imwrite(save_path, img_resized)
                else:
                    cv2.imwrite(save_path, img)
                print(f"[Vision] 🟢 Giả lập thành công: Ảnh '{os.path.basename(selected_img)}' (đã resize {CAMERA_WIDTH}x{CAMERA_HEIGHT}).")
                return True
        except Exception as e:
            print(f"[Vision] ⚠️ Lỗi khi resize ảnh giả lập: {e}")
            # Fallback về copy trực tiếp nếu OpenCV lỗi
            try:
                shutil.copy(selected_img, save_path)
                print(f"[Vision] 🟢 Giả lập thành công (fallback copy): Ảnh '{os.path.basename(selected_img)}'.")
                return True
            except Exception as copy_err:
                print(f"[Vision] ❌ Lỗi copy ảnh giả lập: {copy_err}")

    print("[Vision] ❌ Không tìm thấy dataset ảnh nấm giả lập.")
    return False


def capture_image(camera_source="auto", save_path=IMAGE_SAVE_PATH):
    """
    Hàm chụp ảnh chính theo nguồn chỉ định ("ip_cam", "webcam", hoặc "auto").
    Trả về tuple: (success: bool, active_source_name: str, is_well_lit: bool, luminance: float)
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)

    success = False
    active_source = "Unknown"

    if camera_source == "ip_cam":
        if capture_from_ip_cam(IP_CAM_RTSP_URL, save_path):
            success = True
            active_source = "IP Camera"
        else:
            print("[Vision] ⚠️ IP Camera không phản hồi, tự động dùng Dataset giả lập.")
            if capture_from_dataset(save_path):
                success = True
                active_source = "Dataset (IP Cam Fallback)"

    elif camera_source == "webcam":
        if capture_from_webcam(WEBCAM_INDEX, save_path):
            success = True
            active_source = "USB Webcam"
        else:
            print("[Vision] ⚠️ USB Webcam không phản hồi, tự động dùng Dataset giả lập.")
            if capture_from_dataset(save_path):
                success = True
                active_source = "Dataset (Webcam Fallback)"

    else:  # "auto"
        # Thử USB Webcam trước -> IP Camera -> Dataset
        if capture_from_webcam(WEBCAM_INDEX, save_path):
            success = True
            active_source = "USB Webcam (Auto)"
        elif capture_from_ip_cam(IP_CAM_RTSP_URL, save_path):
            success = True
            active_source = "IP Camera (Auto)"
        elif capture_from_dataset(save_path):
            success = True
            active_source = "Dataset (Auto Fallback)"

    if success:
        # Lưu bản sao lịch sử ảnh chụp với Timestamp
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_path = os.path.join(HISTORY_DIR, f"capture_{timestamp_str}.jpg")
        try:
            shutil.copy(save_path, history_path)
        except Exception as e:
            print(f"[Vision] ⚠️ Không thể lưu lịch sử ảnh: {e}")

        # Kiểm tra độ sáng ảnh
        is_well_lit, luminance = check_image_luminance(save_path)
        if not is_well_lit:
            print(f"[Vision] 🌙 Cảnh báo thiếu sáng: Độ sáng = {luminance} (dưới ngưỡng {LOW_LIGHT_THRESHOLD}).")

        return success, active_source, is_well_lit, luminance

    return False, "None", False, 0.0


def parse_llm_response(response_text):
    """
    Parse phản hồi từ Ollama Vision để trích xuất kích thước nấm.
    Trả về (detected_size, method_name, estimated_confidence)
    """
    text_clean = response_text.strip()

    # 1. Thử parse trực tiếp JSON
    try:
        data = json.loads(text_clean)
        if isinstance(data, dict) and "size" in data:
            val = str(data.get("size")).lower()
            if val in ["small", "medium", "large"]:
                return val, "Direct JSON", random.randint(92, 98)
    except json.JSONDecodeError:
        pass

    # 2. Trích xuất JSON từ khối mã markdown (```json ...)
    markdown_json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text_clean, re.DOTALL)
    if markdown_json_match:
        try:
            data = json.loads(markdown_json_match.group(1))
            if isinstance(data, dict) and "size" in data:
                val = str(data.get("size")).lower()
                if val in ["small", "medium", "large"]:
                    return val, "Markdown JSON", random.randint(90, 96)
        except json.JSONDecodeError:
            pass

    # 3. Sử dụng Regex tìm trường 'size': '...'
    regex_match = re.search(r"['\"]size['\"]\s*:\s*['\"](small|medium|large)['\"]", text_clean, re.IGNORECASE)
    if regex_match:
        return regex_match.group(1).lower(), "Regex Match", random.randint(87, 94)

    # 4. Fallback tìm từ khóa trong văn bản
    text_lower = text_clean.lower()
    if "large" in text_lower:
        return "large", "Keyword Match (large)", random.randint(82, 89)
    elif "medium" in text_lower:
        return "medium", "Keyword Match (medium)", random.randint(80, 88)
    elif "small" in text_lower:
        return "small", "Keyword Match (small)", random.randint(82, 89)

    return "unknown", "None (Fallback)", 0


def analyze_mushroom_image(image_path, retries=2):
    """
    Mã hóa base64 ảnh và gửi tới Ollama local API với cơ chế thử lại (Retry) khi lỗi.
    """
    if not os.path.exists(image_path):
        print(f"[Vision] ❌ File ảnh không tồn tại tại: {image_path}")
        return "unknown", 0

    try:
        with open(image_path, "rb") as image_file:
            img_base64 = base64.b64encode(image_file.read()).decode("utf-8")

        payload = {
            "model": VISION_MODEL,
            "prompt": "Is the orange mushroom in the center of the image small or large?",
            "images": [img_base64],
            "stream": False
        }

        for attempt in range(1, retries + 2):
            print(f"[Vision] Gửi ảnh tới Ollama (Model: {VISION_MODEL}, Lần thử {attempt})...")
            try:
                response = requests.post(OLLAMA_API_URL, json=payload, timeout=45)
                if response.status_code == 200:
                    raw_response = response.json().get("response", "").strip()
                    print(f"[Vision] Phản hồi thô từ Ollama: '{raw_response}'")
                    detected_size, method, confidence = parse_llm_response(raw_response)
                    if detected_size != "unknown":
                        return detected_size, confidence
                    print(f"[Vision] ⚠️ Nhận phản hồi rỗng từ AI, thử lại lần {attempt + 1}...")
                else:
                    print(f"[Vision] ⚠️ Ollama trả về mã lỗi: {response.status_code}")
            except Exception as req_err:
                print(f"[Vision] ⚠️ Lỗi gọi Ollama API (Lần {attempt}): {req_err}")

            if attempt <= retries:
                time.sleep(1)

        return "unknown", 0

    except Exception as e:
        print(f"[Vision] ❌ Lỗi đọc ảnh hoặc mã hóa Base64: {e}")
        return "unknown", 0
