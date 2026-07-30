#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script quét mạng nội bộ tự động dò tìm địa chỉ IP của IP Camera Imou (RTSP Port 554).
Camera Imou: Username: admin | Safety Code: L201622F | Port: 554
"""

import socket
import cv2
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

IMOU_USER = "admin"
IMOU_PASS = "L201622F"
RTSP_PORT = 554


def get_local_ip_subnets():
    """Lấy danh sách dải IP mạng nội bộ của máy hiện tại (ví dụ: 192.168.1.x, 192.168.55.x)."""
    subnets = set()
    try:
        # Tạo kết nối giả lập để dò địa chỉ IP chính của máy
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()

        parts = local_ip.split(".")
        if len(parts) == 4:
            base_subnet = f"{parts[0]}.{parts[1]}.{parts[2]}"
            subnets.add(base_subnet)
    except Exception:
        pass

    # Thêm các dải phổ biến nếu chưa có
    subnets.add("192.168.1")
    subnets.add("192.168.0")
    subnets.add("192.168.55")
    return list(subnets)


def check_rtsp_port(ip, port=RTSP_PORT, timeout=0.6):
    """Kiểm tra xem IP có đang mở cổng RTSP 554 hay không."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            if result == 0:
                return ip
    except Exception:
        pass
    return None


def verify_imou_camera(ip):
    """
    Thử mở luồng RTSP của Imou với tài khoản admin và Safety Code L201622F
    để xác nhận chính xác thiết bị.
    """
    # Thử các cú pháp RTSP phổ biến của Imou/Dahua
    rtsp_urls = [
        f"rtsp://{IMOU_USER}:{IMOU_PASS}@{ip}:554/cam/realmonitor?channel=1&subtype=0",
        f"rtsp://{IMOU_USER}:{IMOU_PASS}@{ip}:554/live/ch0",
        f"rtsp://{IMOU_USER}:{IMOU_PASS}@{ip}:554/stream1"
    ]

    for url in rtsp_urls:
        try:
            cap = cv2.VideoCapture(url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    return ip, url
            cap.release()
        except Exception:
            pass

    return ip, None


def scan_network_for_imou(max_workers=50):
    """Quét toàn bộ dải IP mạng nội bộ để tìm Camera Imou."""
    subnets = get_local_ip_subnets()
    print(f"🔍 Bắt đầu quét các dải mạng nội bộ: {subnets} (Cổng RTSP: {RTSP_PORT})...")

    candidates = []

    for subnet in subnets:
        print(f"📡 Đang quét dải IP: {subnet}.1 -> {subnet}.254 ...")
        ip_list = [f"{subnet}.{i}" for i in range(1, 255)]

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ip = {executor.submit(check_rtsp_port, ip): ip for ip in ip_list}
            for future in as_completed(future_to_ip):
                result_ip = future.result()
                if result_ip:
                    print(f"  🟢 Phát hiện thiết bị mở cổng RTSP 554 tại: {result_ip}")
                    candidates.append(result_ip)

    if not candidates:
        print("❌ Không tìm thấy thiết bị nào đang mở cổng RTSP 554 trong mạng nội bộ.")
        return None, None

    print(f"\n🧪 Đang kiểm tra xác thực Imou trên {len(candidates)} thiết bị mở cổng RTSP...")

    for cand_ip in candidates:
        ip, valid_url = verify_imou_camera(cand_ip)
        if valid_url:
            print("\n=================================================================")
            print(f"🎉 ĐÃ TÌM THẤY CAMERA IMOU THÀNH CÔNG!")
            print(f"📌 Địa chỉ IP: {ip}")
            print(f"🔗 RTSP URL : {valid_url}")
            print("=================================================================\n")
            return ip, valid_url
        else:
            print(f"  ⚠️ IP {cand_ip} mở cổng 554 nhưng không xác thực được với tài khoản Imou.")

    print("⚠️ Không xác thực được camera Imou bằng mật khẩu mặc định trên các IP mở cổng 554.")
    return None, None


if __name__ == "__main__":
    ip, url = scan_network_for_imou()
    if ip and url:
        print("💡 Bạn có thể khởi chạy backend bằng lệnh:")
        print(f"   IP_CAM_URL=\"{url}\" .venv/bin/python3 -m backend.main_jetson")
    else:
        sys.exit(1)
