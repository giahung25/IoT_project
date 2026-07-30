import serial
import serial.tools.list_ports
import time
import sys

def main():
    print("=== ESP32 Serial Monitor ===")
    ports = list(serial.tools.list_ports.comports())
    esp_ports = []
    for p in ports:
        device = p.device
        description = p.description or ""
        manufacturer = p.manufacturer or ""
        if "ACM" in device or "USB" in device or "Espressif" in manufacturer or "CH34" in description or "CP21" in description:
            esp_ports.append(device)
            
    if not esp_ports:
        print("Không tìm thấy cổng Serial nào! Hãy chắc chắn rằng ESP32 đã được cắm vào máy tính.")
        sys.exit(1)
        
    print(f"Danh sách cổng phát hiện được: {esp_ports}")
    # Ưu tiên cổng ttyUSB nếu có, nếu không thì ttyACM
    port = esp_ports[0]
    for p in esp_ports:
        if "USB" in p:
            port = p
            break
            
    print(f"Đang kết nối tới {port} với tốc độ 115200 baud...")
    
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        # Bật DTR/RTS để tương thích với ESP32-S3 JTAG/CDC
        ser.dtr = True
        ser.rts = True
        
        # Không tự động reset bằng DTR/RTS để tránh ESP32-S3 bị rơi vào chế độ DOWNLOAD MODE
        print("Mẹo: Nếu muốn khởi động lại ESP32, hãy nhấn nút cứng EN (hoặc RST) trên mạch.")
        time.sleep(0.5)
        
        print("Đang lắng nghe dữ liệu từ ESP32... Nhấn Ctrl+C để dừng.\n")
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"[ESP32]: {line}")
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nĐã dừng giám sát.")
    except PermissionError:
        print(f"\n❌ Lỗi: Không có quyền truy cập {port}.")
        print("Hãy chạy lệnh bằng quyền sudo hoặc thêm user vào nhóm uucp:")
        print(f"Lệnh chạy: echo 1 | sudo -S python {sys.argv[0]}")
    except Exception as e:
        print(f"Lỗi kết nối: {e}")

if __name__ == '__main__':
    main()
