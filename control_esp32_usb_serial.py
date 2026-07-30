#!/usr/bin/env python3
"""
=============================================================================
🔌 MUSHROOM IOT - DIRECT USB SERIAL ESP32 CONTROLLER (NO JETSON / NO WEB)
=============================================================================
Script Python kết nối TRỰC TIẾP tới bo mạch ESP32 cắm qua cổng USB (UART)
phát lệnh Bật/Tắt các bóng đèn LED & Rơ-le ngay tức thì (0.000s delay).
=============================================================================
"""

import sys
import time
import json
import glob

try:
    import serial
except ImportError:
    print("❌ Thư viện 'pyserial' chưa được cài đặt. Vui lòng cài: pip install pyserial")
    sys.exit(1)

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

def find_esp32_port():
    ports = glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')
    if not ports:
        print(f"{RED}❌ Không tìm thấy cổng Serial ESP32 nào cắm vào máy! (/dev/ttyACM* hoặc /dev/ttyUSB*){RESET}")
        sys.exit(1)
    
    # Ưu tiên ttyACM1 hoặc ttyACM0
    for p in ports:
        if 'ttyACM1' in p:
            return p
    return ports[0]

# Trạng thái 5 thiết bị
device_states = {
    "pump": False,          # GPIO 15 - LED 1 / Relay 1 (Phun sương)
    "harvest_alert": False, # GPIO 16 - LED 2 / Relay 2 (Cảnh báo)
    "grow_light": False,    # GPIO 17 - LED 3 / Relay 3 (Đèn quang hợp)
    "cooling_fan": False,   # GPIO 18 - LED 4 / Relay 4 (Quạt mát)
    "vent_gate": False      # GPIO 14 - Servo SG90 (Cửa gió)
}

def send_command(ser, payload):
    payload_str = json.dumps(payload) + "\n"
    ser.write(payload_str.encode('utf-8'))
    ser.flush()
    print(f"{GREEN}🔌 [USB Serial ➔ ESP32] Đã gửi lệnh trực tiếp:{RESET} {BOLD}{payload_str.strip()}{RESET}")
    
    # Đọc phản hồi từ ESP32 nếu có
    time.sleep(0.1)
    while ser.in_waiting > 0:
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                print(f"   {CYAN}📩 [ESP32 Serial Response]: {line}{RESET}")
        except Exception:
            break

def print_menu(port_name):
    print(f"\n{CYAN}{BOLD}╔════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}{BOLD}║   🔌 ĐIỀU KHIỂN ESP32 TRỰC TIẾP QUA USB SERIAL ({port_name})             ║{RESET}")
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

def run_auto_test(ser):
    print(f"\n{YELLOW}{BOLD}🧪 Bắt đầu kịch bản test lần lượt từng cổng phần cứng qua USB Serial...{RESET}")
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
    send_command(ser, device_states)
    time.sleep(1)

    for name, key in steps:
        print(f"\n👉 Testing: {BOLD}{name}{RESET}")
        print(f"   ➔ {GREEN}BẬT (HIGH)...{RESET}")
        device_states[key] = True
        send_command(ser, device_states)
        time.sleep(2)

        print(f"   ➔ {WHITE}TẮT (LOW)...{RESET}")
        device_states[key] = False
        send_command(ser, device_states)
        time.sleep(1)

    print(f"\n{GREEN}{BOLD}✅ Đã hoàn thành test tự động qua USB Serial! Tất cả các cổng đã về TẮT.{RESET}\n")

def main():
    port_name = find_esp32_port()
    print(f"🔌 Đang mở cổng USB Serial tại {BOLD}{port_name}{RESET} (Baudrate: 115200)...")
    
    try:
        ser = serial.Serial(port_name, 115200, timeout=1)
        time.sleep(1.5) # Đợi ESP32 khởi động lại UART
        print(f"{GREEN}🟢 Kết nối trực tiếp ESP32 qua USB thành công!{RESET}")
    except Exception as e:
        print(f"{RED}❌ Không thể mở cổng Serial {port_name}: {e}{RESET}")
        sys.exit(1)

    # Ban đầu gửi lệnh đồng bộ tắt hết
    send_command(ser, device_states)

    while True:
        print_menu(port_name)
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
            send_command(ser, device_states)
        elif choice == '2':
            device_states["harvest_alert"] = not device_states["harvest_alert"]
            send_command(ser, device_states)
        elif choice == '3':
            device_states["grow_light"] = not device_states["grow_light"]
            send_command(ser, device_states)
        elif choice == '4':
            device_states["cooling_fan"] = not device_states["cooling_fan"]
            send_command(ser, device_states)
        elif choice == '5':
            device_states["vent_gate"] = not device_states["vent_gate"]
            send_command(ser, device_states)
        elif choice == '0':
            for k in device_states:
                device_states[k] = False
            print(f"{RED}{BOLD}🛑 Đã tắt toàn bộ thiết bị & đèn LED!{RESET}")
            send_command(ser, device_states)
        elif choice == '9':
            for k in device_states:
                device_states[k] = True
            print(f"{GREEN}{BOLD}🟢 Đã bật toàn bộ thiết bị & đèn LED!{RESET}")
            send_command(ser, device_states)
        elif choice == 'A':
            run_auto_test(ser)
        else:
            print(f"{RED}⚠️ Lựa chọn không hợp lệ, vui lòng thử lại!{RESET}")
        
        time.sleep(0.3)

if __name__ == "__main__":
    main()
