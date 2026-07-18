#!/bin/bash

# Thư mục chứa dự án
PROJECT_DIR="/home/GiaHung/Projects/IoT_project"
cd "$PROJECT_DIR" || exit

clear
echo "================================================================"
echo "   🌱 HỆ THỐNG GIÁM SÁT SINH TRƯỞNG NẤM - KÍCH HOẠT 🌱"
echo "================================================================"
echo " Chọn luồng hoạt động:"
echo "   1) Luồng GIẢ LẬP (Simulation Mode) - Chạy local PC không cần Jetson"
echo "   2) Luồng THỰC TẾ (Real Mode)       - Kết nối camera & sensors trên Jetson"
echo "================================================================"
read -p " Nhập lựa chọn của bạn (1 hoặc 2, mặc định là 1): " choice
choice=${choice:-1}

# Kích hoạt môi trường ảo Python
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "⚠️ Cảnh báo: Không tìm thấy thư mục môi trường ảo .venv!"
fi

if [ "$choice" -eq 1 ]; then
    echo "================================================================"
    echo "🔄 Đang khởi động luồng GIẢ LẬP (Simulation Mode)..."
    echo "================================================================"
    export SIMULATION_MODE=1
    python WEB_IOT/backend.py
elif [ "$choice" -eq 2 ]; then
    clear
    echo "================================================================"
    echo "⚡ CẤU HÌNH KẾT NỐI JETSON ORIN NANO"
    echo "================================================================"
    echo " Chọn địa chỉ IP kết nối tới Jetson:"
    echo "   1) Mạng Wi-Fi nội bộ (LAN): 192.168.1.240"
    echo "   2) Mạng ảo USB (USB Cable): 192.168.55.1"
    echo "   3) Mạng VPN từ xa (ZeroTier): 192.168.193.30"
    echo "================================================================"
    read -p " Nhập lựa chọn kết nối (1, 2 hoặc 3, mặc định là 1): " conn_choice
    conn_choice=${conn_choice:-1}
    
    if [ "$conn_choice" -eq 1 ]; then
        JETSON_IP="192.168.1.240"
    elif [ "$conn_choice" -eq 2 ]; then
        JETSON_IP="192.168.55.1"
    elif [ "$conn_choice" -eq 3 ]; then
        JETSON_IP="192.168.193.30"
    else
        JETSON_IP="192.168.1.240"
    fi
    
    export JETSON_IP=$JETSON_IP
    echo "📍 Địa chỉ IP Jetson được chọn: $JETSON_IP"
    
    # Tự động phát hiện IP của PC trên cùng subnet với Jetson
    SUBNET=$(echo "$JETSON_IP" | cut -d'.' -f1-3)
    PC_IP=$(ip addr show | grep -oP 'inet \K[0-9.]+' | grep "^$SUBNET\." | head -n 1)
    
    if [ -z "$PC_IP" ]; then
        # Fallback nếu không khớp subnet
        PC_IP="192.168.55.100"
    fi
    export PC_IP=$PC_IP
    echo "📍 Địa chỉ IP tự động phát hiện của PC: $PC_IP"
    
    echo "================================================================"
    echo "⚡ Đang khởi động luồng THỰC TẾ (Real Mode) với Jetson @ $JETSON_IP..."
    echo "================================================================"
    
    # Hỏi người dùng có muốn tự động bật Edge Server Jetson Backend qua SSH không
    read -p " Bạn có muốn tự động khởi động Edge Server trên Jetson qua SSH? (y/n, mặc định y): " run_jetson
    run_jetson=${run_jetson:-y}
    
    if [ "$run_jetson" = "y" ] || [ "$run_jetson" = "Y" ]; then
        echo "🔄 Đang kết nối và khởi động Jetson Edge Server ở tiến trình ngầm..."
        # Dừng bất kỳ tiến trình cũ nào nếu có để tránh xung đột cổng
        sshpass -p jetson ssh -o StrictHostKeyChecking=no jetson@$JETSON_IP "pkill -f main_jetson.py || true" >/dev/null 2>&1
        # Chạy main_jetson.py ngầm trên Jetson, truyền PC_IP và lưu log tại ~/jetson_project/main_jetson.log
        sshpass -p jetson ssh -o StrictHostKeyChecking=no jetson@$JETSON_IP "nohup bash -c 'export PYTHONPATH=~/jetson_project && export PC_IP=$PC_IP && python3 -u ~/jetson_project/backend/main_jetson.py' > ~/jetson_project/main_jetson.log 2>&1 &"
        echo "🟢 Jetson Edge Server đã được kích hoạt chạy ngầm."
        echo "   👉 Xem log Jetson bằng cách chạy lệnh SSH: tail -f ~/jetson_project/main_jetson.log"
    fi
    
    export SIMULATION_MODE=0
    python WEB_IOT/backend.py
else
    echo "❌ Lựa chọn không hợp lệ. Thoát..."
    exit 1
fi
