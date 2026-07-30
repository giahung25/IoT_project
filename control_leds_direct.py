#!/usr/bin/env python3
"""
=============================================================================
🌱 MUSHROOM IOT - DIRECT LED & ACTUATOR CONTROLLER FOR PC & JETSON
=============================================================================
Script Python điều khiển Bật/Tắt cụm Đèn LED & Rơ-le cho PC & Jetson.
Tự động hỗ trợ cả 2 phương thức:
 1. Firebase RTDB Cloud API (Chuẩn thư viện mặc định Python, KHÔNG cần pip)
 2. Mosquitto MQTT Broker Local (Nếu có thư viện paho-mqtt)
=============================================================================
"""

import sys
import time
import json
import urllib.request

FIREBASE_URL = "https://agrishroom-edge-default-rtdb.asia-southeast1.firebasedatabase.app/status.json"

# Kiểm tra xem có paho-mqtt không
MQTT_AVAILABLE = False
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

# Cấu hình kết nối MQTT
MQTT_HOSTS = ["192.168.55.1", "localhost", "127.0.0.1"]
MQTT_PORT = 1883
TOPIC_CONTROL = "actuator/command"

mqtt_client = None

# Trạng thái hiện tại của 5 cổng đầu ra
device_states = {
    "pump": False,          # GPIO 15 - LED 1 / Relay 1 (Phun sương)
    "harvest_alert": False, # GPIO 16 - LED 2 / Relay 2 (Cảnh báo)
    "grow_light": False,    # GPIO 17 - LED 3 / Relay 3 (Đèn quang hợp)
    "cooling_fan": False,   # GPIO 18 - LED 4 / Relay 4 (Quạt mát)
    "vent_gate": False      # GPIO 14 - Servo SG90 (Cửa gió)
}

# Mã màu ANSI
RESET   = "\033[0m"
BOLD    = "\033[1m"
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
WHITE   = "\033[37m"

def init_mqtt():
    global mqtt_client
    if not MQTT_AVAILABLE:
        return
    client = mqtt.Client()
    for host in MQTT_HOSTS:
        try:
            client.connect(host, MQTT_PORT, keepalive=10)
            client.loop_start()
            mqtt_client = client
            print(f"{GREEN}🟢 Đã kết nối MQTT Broker tại {host}:{MQTT_PORT}{RESET}")
            return
        except Exception:
            continue

def send_command(payload):
    payload_str = json.dumps(payload)
    
    # 1. Gửi qua Firebase Realtime Database (Mọi máy PC đều chạy được ngay không cần cài pip)
    try:
        req = urllib.request.Request(
            FIREBASE_URL,
            data=payload_str.encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='PATCH'
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                print(f"{GREEN}🟢 [Firebase RTDB ACK] Đã gửi lệnh:{RESET} {BOLD}{payload_str}{RESET}")
    except Exception as e:
        print(f"{RED}⚠️ Lỗi gửi Firebase: {e}{RESET}")

    # 2. Nếu có kết nối MQTT local với Jetson thì phát thêm qua MQTT
    if mqtt_client:
        try:
            mqtt_client.publish(TOPIC_CONTROL, payload_str)
            print(f"{CYAN}📡 [MQTT Direct ➔ BLE] Đã phát lệnh qua MQTT:{RESET} {payload_str}")
        except Exception as e:
            pass

def print_menu():
    print(f"\n{CYAN}{BOLD}╔════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}{BOLD}║     💡 BẢNG ĐIỀU KHIỂN ĐÈN LED & RƠ-LE TRỰC TIẾP (PC & JETSON ➔ ESP32)     ║{RESET}")
    print(f"{CYAN}{BOLD}╚════════════════════════════════════════════════════════════════════════════╝{RESET}")
    
    p_status = f"{GREEN}BẬT (HIGH){RESET}" if device_states["pump"] else f"{WHITE}TẮT (LOW){RESET}"
    a_status = f"{RED}CẢNH BÁO (HIGH){RESET}" if device_states["harvest_alert"] else f"{WHITE}TẮT (LOW){RESET}"
    l_status = f"{YELLOW}BẬT ĐÈN (HIGH){RESET}" if device_states["grow_light"] else f"{WHITE}TẮT (LOW){RESET}"
    f_status = f"{MAGENTA}BẬT QUẠT (HIGH){RESET}" if device_states["cooling_fan"] else f"{WHITE}TẮT (LOW){RESET}"
    v_status = f"{CYAN}MỞ (180°){RESET}" if device_states["vent_gate"] else f"{WHITE}ĐÓNG (0°){RESET}"

    print(f"  [1] 🔵 LED 1 / Relay 1 (GPIO 15 - Bơm Phun Sương) : {p_status}")
    print(f"  [2] 🔴 LED 2 / Relay 2 (GPIO 16 - Đèn/Còi Cảnh Báo): {a_status}")
    print(f"  [3] ⚪ LED 3 / Relay 3 (GPIO 17 - Đèn Quang Hợp)  : {l_status}")
    print(f"  [4] 🟡 LED 4 / Relay 4 (GPIO 18 - Quạt Mát)       : {f_status}")
    print(f"  [5] 🌀 Servo SG90     (GPIO 14 - Cửa Gió)         : {v_status}")
    print(f"      🟢 LED 5          (GPIO 7 - System Safe OK)   : {GREEN}SÁNG CỐ ĐỊNH (BO MẠCH OK){RESET}")
    print(f"{CYAN}──────────────────────────────────────────────────────────────────────────────{RESET}")
    print(f"  {RED}{BOLD}[0] TẮT TOÀN BỘ CÁC ĐÈN LED & RƠ-LE (ALL OFF){RESET}")
    print(f"  {GREEN}{BOLD}[9] BẬT TOÀN BỘ CÁC ĐÈN LED & RƠ-LE (ALL ON){RESET}")
    print(f"  {YELLOW}{BOLD}[A] BẮT ĐẦU TEST TỰ ĐỘNG BẬT ➔ TẮT LẦN LƯỢT TẤT CẢ ĐÈN{RESET}")
    print(f"  {WHITE}[Q] Thoát chương trình{RESET}")
    print(f"{CYAN}══════════════════════════════════════════════════════════════════════════════{RESET}")

def run_auto_test():
    print(f"\n{YELLOW}{BOLD}🧪 Bắt đầu kịch bản test lần lượt từng cổng phần cứng...{RESET}")
    steps = [
        ("🔵 LED 1 / Relay 1 (GPIO 15 - Bơm sương)", "pump"),
        ("🔴 LED 2 / Relay 2 (GPIO 16 - Cảnh báo)", "harvest_alert"),
        ("⚪ LED 3 / Relay 3 (GPIO 17 - Đèn quang hợp)", "grow_light"),
        ("🟡 LED 4 / Relay 4 (GPIO 18 - Quạt mát)", "cooling_fan"),
        ("🌀 Servo SG90 (GPIO 14 - Cửa gió)", "vent_gate"),
    ]
    
    # Đưa về trạng thái tắt hết ban đầu
    for _, k in steps:
        device_states[k] = False
    send_command(device_states)
    time.sleep(1)

    for name, key in steps:
        print(f"\n👉 Testing: {BOLD}{name}{RESET}")
        print(f"   ➔ {GREEN}BẬT (HIGH)...{RESET}")
        device_states[key] = True
        send_command(device_states)
        time.sleep(2.5)

        print(f"   ➔ {WHITE}TẮT (LOW)...{RESET}")
        device_states[key] = False
        send_command(device_states)
        time.sleep(1.5)

    print(f"\n{GREEN}{BOLD}✅ Đã hoàn thành test tự động! Tất cả các cổng đã về trạng thái TẮT.{RESET}\n")

def main():
    init_mqtt()
    
    # Ban đầu gửi lệnh đồng bộ tắt hết để bắt đầu sạch
    send_command(device_states)

    while True:
        print_menu()
        try:
            choice = input(f"{BOLD}Chọn thao tác [0-9, A, Q]: {RESET}").strip().upper()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{GREEN}👋 Đã thoát chương trình.{RESET}")
            break

        if choice == 'Q':
            print(f"{GREEN}👋 Đã thoát chương trình.{RESET}")
            break
        elif choice == '1':
            device_states["pump"] = not device_states["pump"]
            send_command(device_states)
        elif choice == '2':
            device_states["harvest_alert"] = not device_states["harvest_alert"]
            send_command(device_states)
        elif choice == '3':
            device_states["grow_light"] = not device_states["grow_light"]
            send_command(device_states)
        elif choice == '4':
            device_states["cooling_fan"] = not device_states["cooling_fan"]
            send_command(device_states)
        elif choice == '5':
            device_states["vent_gate"] = not device_states["vent_gate"]
            send_command(device_states)
        elif choice == '0':
            for k in device_states:
                device_states[k] = False
            print(f"{RED}{BOLD}🛑 Đã tắt toàn bộ thiết bị & đèn LED!{RESET}")
            send_command(device_states)
        elif choice == '9':
            for k in device_states:
                device_states[k] = True
            print(f"{GREEN}{BOLD}🟢 Đã bật toàn bộ thiết bị & đèn LED!{RESET}")
            send_command(device_states)
        elif choice == 'A':
            run_auto_test()
        else:
            print(f"{RED}⚠️ Lựa chọn không hợp lệ, vui lòng thử lại!{RESET}")
        
        time.sleep(0.5)

if __name__ == "__main__":
    main()
