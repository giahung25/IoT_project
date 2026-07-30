#!/usr/bin/env python3
"""
=============================================================================
🌱 MUSHROOM IOT - REALTIME SENSOR & LED ACTUATORS MONITOR & HARDWARE TESTER
=============================================================================
Script Python theo dõi dữ liệu cảm biến, trí tuệ nhân tạo (AI) & trạng thái
các bóng đèn LED / Rơ-le thời gian thực trực tiếp trên Terminal PC.
Hỗ trợ kiểm tra tự động bật/tắt cụm đèn LED (GPIO 14 - 19 & GPIO 48).
=============================================================================
"""

import time
import json
import urllib.request
import os
import sys
from datetime import datetime

FIREBASE_URL = "https://agrishroom-edge-default-rtdb.asia-southeast1.firebasedatabase.app/status.json"

# Mã màu ANSI cho Terminal đẹp mắt
RESET   = "\033[0m"
BOLD    = "\033[1m"
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
WHITE   = "\033[37m"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def fetch_sensor_data():
    try:
        req = urllib.request.Request(FIREBASE_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                return data
    except Exception as e:
        return None
    return None

def patch_firebase_state(payload):
    """Gửi cập nhật trạng thái bật/tắt thiết bị lên Firebase RTDB."""
    try:
        data_bytes = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(FIREBASE_URL, data=data_bytes, headers={'Content-Type': 'application/json'}, method='PATCH')
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"{RED}❌ Lỗi kết nối Firebase: {e}{RESET}")
        return False

def format_zone_color(zone_name):
    if "Bình Thường" in str(zone_name) or "Normal" in str(zone_name) or "Optimal" in str(zone_name):
        return f"{GREEN}{BOLD}{zone_name}{RESET}"
    elif "Khô" in str(zone_name) or "Dehydration" in str(zone_name):
        return f"{YELLOW}{BOLD}{zone_name}{RESET}"
    elif "Ẩm" in str(zone_name) or "Wet" in str(zone_name):
        return f"{BLUE}{BOLD}{zone_name}{RESET}"
    else:
        return f"{RED}{BOLD}{zone_name}{RESET}"

def run_hardware_led_test():
    """Tác vụ tự động kiểm tra bật/tắt lần lượt toàn bộ các bóng đèn LED & Rơ-le."""
    print(f"\n{YELLOW}{BOLD}========================================================================{RESET}")
    print(f"{YELLOW}{BOLD}🧪 BẮT ĐẦU KIỂM TRA BẬT/TẮT CỤM ĐÈN LED & RƠ-LE PHẦN CỨNG ESP32-S3...{RESET}")
    print(f"{YELLOW}{BOLD}========================================================================{RESET}\n")

    test_steps = [
        ("🔵 LED 1 / Relay 1 (GPIO 15 - Bơm Phun Sương)", "pump", True, False),
        ("🔴 LED 2 / Relay 2 (GPIO 16 - Còi & Đèn Cảnh Báo)", "harvest_alert", True, False),
        ("⚪ LED 3 / Relay 3 (GPIO 17 - Đèn Quang Hợp)", "grow_light", True, False),
        ("🟡 LED 4 / Relay 4 (GPIO 18 - Quạt Thông Gió)", "cooling_fan", True, False),
        ("🌀 Servo SG90 (GPIO 14 - Cửa Gió Thông Khí)", "vent_gate", True, False),
    ]

    for name, key, on_val, off_val in test_steps:
        print(f"👉 {CYAN}Đang kiểm tra: {BOLD}{name}{RESET}...")
        
        # BẬT
        print(f"   [1/2] Gửi lệnh: {GREEN}{BOLD}BẬT (HIGH){RESET}...")
        ok_on = patch_firebase_state({key: on_val})
        if ok_on:
            print(f"   {GREEN}🟢 Firebase ACK: {name} ➔ BẬT THÀNH CÔNG!{RESET}")
        else:
            print(f"   {RED}🔴 Lỗi gửi lệnh BẬT!{RESET}")
        time.sleep(2)

        # TẮT
        print(f"   [2/2] Gửi lệnh: {WHITE}{BOLD}TẮT (LOW){RESET}...")
        ok_off = patch_firebase_state({key: off_val})
        if ok_off:
            print(f"   {GREEN}🟢 Firebase ACK: {name} ➔ TẮT THÀNH CÔNG!{RESET}\n")
        else:
            print(f"   {RED}🔴 Lỗi gửi lệnh TẮT!{RESET}\n")
        time.sleep(1)

    print(f"{GREEN}{BOLD}✅ HOÀN TẤT KIỂM TRA BẬT/TẮT TẤT CẢ CÁC ĐÈN LED & THIẾT BỊ!{RESET}")
    print(f"{WHITE}Đang quay lại giao diện theo dõi thời gian thực sau 3 giây...{RESET}")
    time.sleep(3)

def render_dashboard(data):
    clear_screen()
    now_str = datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
    
    temp = data.get("temperature", 0.0)
    hum = data.get("humidity", 0.0)
    vpd = data.get("vpd", 0.0)
    co2 = data.get("co2_ppm", 400)
    light = data.get("light_lux", 0)
    growth_zone = data.get("growth_zone", "N/A")
    esp_online = data.get("esp32_online", False)

    # Đèn & Relays state
    pump_status = data.get("pump", False)
    harvest_alert = data.get("harvest_alert", False)
    grow_light = data.get("grow_light", False)
    cooling_fan = data.get("cooling_fan", False)
    vent_gate = data.get("vent_gate", False)
    
    mushroom_size = data.get("mushroom_size", "unknown")
    ai_conf = data.get("ai_confidence", 0)
    active_camera = data.get("active_camera", "N/A")
    sensor_src = data.get("sensor_source", "Auto-Detect")
    last_updated = data.get("last_updated", "N/A")

    esp_badge = f"{GREEN}{BOLD}🟢 ONLINE (BLE Wireless){RESET}" if esp_online else f"{RED}{BOLD}🔴 OFFLINE{RESET}"
    
    # Badges trạng thái Đèn & Rơ-le
    led1_badge = f"{BLUE}{BOLD}🔵 ĐANG BẬT (HIGH){RESET}" if pump_status else f"{WHITE}⚪ TẮT (LOW){RESET}"
    led2_badge = f"{RED}{BOLD}🔴 CẢNH BÁO (HIGH){RESET}" if harvest_alert else f"{GREEN}🟢 Bình Thường (LOW){RESET}"
    led3_badge = f"{YELLOW}{BOLD}⚪ ĐANG BẬT ĐÈN (HIGH){RESET}" if grow_light else f"{WHITE}⚪ TẮT (LOW){RESET}"
    led4_badge = f"{MAGENTA}{BOLD}🟡 ĐANG BẬT QUẠT (HIGH){RESET}" if cooling_fan else f"{WHITE}⚪ TẮT (LOW){RESET}"
    servo_badge = f"{CYAN}{BOLD}🌀 MỞ (Góc 180°){RESET}" if vent_gate else f"{WHITE}🚪 ĐÓNG (Góc 0°){RESET}"
    led5_badge = f"{GREEN}{BOLD}🟢 SYSTEM SAFE (OK){RESET}"
    
    # Neopixel Status
    if harvest_alert or co2 > 1000:
        neopixel_badge = f"{RED}{BOLD}🔴 RED ALARM / ERROR{RESET}"
    elif pump_status or grow_light or cooling_fan:
        neopixel_badge = f"{YELLOW}{BOLD}🟡 YELLOW ACTUATING{RESET}"
    else:
        neopixel_badge = f"{CYAN}{BOLD}❇️ CYAN NORMAL{RESET}"

    # Định dạng CO2 cảnh báo
    co2_color = GREEN if co2 < 1000 else RED
    co2_status = "Bình thường" if co2 < 1000 else "⚠️ CAO (Cần thông gió)"

    # Định dạng Kích thước Nấm
    size_map = {
        "large": f"{GREEN}{BOLD}🍄 LỚN (Đã đạt chuẩn thu hoạch){RESET}",
        "small": f"{CYAN}{BOLD}🍄 NHỎ (Đang phát triển){RESET}",
        "medium": f"{CYAN}{BOLD}🍄 TRUNG BÌNH{RESET}"
    }
    size_str = size_map.get(mushroom_size, f"{YELLOW}⏳ Đang phân tích / Chưa phát hiện{RESET}")

    print(f"{CYAN}{BOLD}╔════════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}{BOLD}║         🌱 MUSHROOM IOT - REALTIME SENSOR & LED ACTUATOR MONITOR                ║{RESET}")
    print(f"{CYAN}{BOLD}╚════════════════════════════════════════════════════════════════════════════════╝{RESET}")
    print(f" 🕒  Thời gian máy PC : {BOLD}{now_str}{RESET}")
    print(f" 📡  Cập nhật Firebase : {WHITE}{last_updated[:19].replace('T', ' ')}{RESET}")
    print(f" 📶  Trạng thái ESP32  : {esp_badge}")
    print(f" 📍  Nguồn Cảm Biến    : {MAGENTA}{BOLD}{sensor_src}{RESET}")
    print(f"{CYAN}──────────────────────────────────────────────────────────────────────────────────{RESET}")
    
    print(f"{BOLD}📊 THÔNG SỐ CẢM BIẾN VI KHÍ HẬU (FULL SENSOR SUITE):{RESET}")
    print(f"   • 🌡️  Nhiệt Độ (DHT)  : {BOLD}{YELLOW}{temp:.1f} °C{RESET}")
    print(f"   • 💧  Độ Ẩm (DHT)     : {BOLD}{CYAN}{hum:.1f} %{RESET}")
    print(f"   • 📈  Áp Suất VPD     : {BOLD}{MAGENTA}{vpd:.2f} kPa{RESET}")
    print(f"   • 💨  Nồng Độ CO₂     : {BOLD}{co2_color}{co2} ppm{RESET} ({co2_status})")
    print(f"   • ☀️  Ánh Sáng (BH1750): {BOLD}{YELLOW}{light} Lux{RESET}")
    print(f"   • 🔵  Vùng Môi Trường : {format_zone_color(growth_zone)}")
    print(f"{CYAN}──────────────────────────────────────────────────────────────────────────────────{RESET}")

    print(f"{BOLD}💡 TRẠNG THÁI CỤM ĐÈN BÁO LED & THIẾT BỊ CHẤP HÀNH (ESP32 PINS):{RESET}")
    print(f"   • 🔵  LED 1 / Relay 1 (GPIO 15 - Phun Sương) : {led1_badge}")
    print(f"   • 🔴  LED 2 / Relay 2 (GPIO 16 - Cảnh Báo)  : {led2_badge}")
    print(f"   • ⚪  LED 3 / Relay 3 (GPIO 17 - Đèn Quang Hợp): {led3_badge}")
    print(f"   • 🟡  LED 4 / Relay 4 (GPIO 18 - Quạt Mát)   : {led4_badge}")
    print(f"   • 🌀  Servo SG90 (GPIO 14 - Cửa Gió)         : {servo_badge}")
    print(f"   • 🟢  LED 5 (GPIO 7 - System Safe OK)        : {led5_badge}")
    print(f"   • 🌈  Neopixel Diagnostic (GPIO 48)          : {neopixel_badge}")
    print(f"{CYAN}──────────────────────────────────────────────────────────────────────────────────{RESET}")

    print(f"{BOLD}🤖 TRÍ TUỆ NHÂN TẠO VISION AI (Ollama Moondream):{RESET}")
    print(f"   • 📷  Camera Nguồn  : {WHITE}{active_camera}{RESET}")
    print(f"   • 📏  Kích Thước Nấm: {size_str}")
    print(f"   • 🎯  Độ Tin Cậy AI : {BOLD}{GREEN}{ai_conf}%{RESET}")
    print(f"{CYAN}══════════════════════════════════════════════════════════════════════════════════{RESET}")
    print(f" {YELLOW}[T] Chạy test tự động bật/tắt cụm Đèn LED{RESET} | {WHITE}Ctrl+C để thoát{RESET}\n")

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['--test', 'test', '-t']:
        run_hardware_led_test()
    
    print(f"{GREEN}🚀 Đang kết nối tới Firebase Realtime Database...{RESET}")
    while True:
        data = fetch_sensor_data()
        if data:
            render_dashboard(data)
        else:
            print(f"{RED}⚠️  Không thể lấy dữ liệu từ Firebase. Đang thử lại sau 2 giây...{RESET}")
        time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{GREEN}👋 Đã dừng theo dõi cảm biến. Chúc bạn một ngày tốt lành!{RESET}")
        sys.exit(0)
