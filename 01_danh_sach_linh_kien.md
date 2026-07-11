# 📦 Danh Sách Linh Kiện — Dự Án Edge AI & IoT Giám Sát Sinh Trưởng Nấm

> **Ngày lập:** 11/07/2026  
> **Trạng thái:** Đang chuẩn bị vật tư

---

## 1. Tổng Quan

Bảng dưới đây liệt kê toàn bộ linh kiện phần cứng phục vụ lắp ráp sa bàn mô phỏng. Các mục được phân loại theo trạng thái **Đã có** và **Cần mua thêm** để dễ dàng theo dõi và đặt hàng.

---

## 2. Linh Kiện Đã Có ✅

| # | Tên Linh Kiện | SL | Mục Đích Sử Dụng | Ghi Chú |
|---|---|---|---|---|
| 1 | Máy tính nhúng **Jetson Orin Nano** | 1 | Chạy Linux, xử lý Vision LLM (Ollama), host Web Server & MQTT Broker | Trung tâm xử lý của toàn hệ thống |
| 2 | **Webcam USB** | 1 | Cắm trực tiếp vào Jetson, thu thập ảnh luống nấm ổn định | Phương án chính, chống nhiễu mạng |
| 3 | Mạch vi điều khiển **ESP32** | 1 | Đọc tín hiệu cảm biến, giao tiếp Wi-Fi, điều khiển relay | Node IoT chính |

---

## 3. Linh Kiện Cần Mua Thêm 🛒

| # | Tên Linh Kiện | SL | Đơn Giá (VNĐ) | Thành Tiền (VNĐ) | Mục Đích Sử Dụng | Link Tham Khảo |
|---|---|---|---|---|---|---|
| 1 | Mạch **ESP32-CAM** (kèm mạch nạp CH340/CP2102) | 1 | ~120.000 | ~120.000 | Camera không dây, tăng tính phân tán IoT | Shopee / Điện tử Nshop |
| 2 | Cảm biến **DHT11** (loại có board 3 chân) | 1 | ~15.000 | ~15.000 | Đo nhiệt độ (0–50°C) & độ ẩm (20–90% RH) | Shopee / Điện tử Nshop |
| 3 | Module **Relay 5V** (loại 2 kênh, opto-isolated) | 1 | ~25.000 | ~25.000 | Công tắc điện tử bật/tắt thiết bị theo lệnh từ Jetson | Shopee / Điện tử Nshop |
| 4 | **Đèn LED Xanh** 5mm (gói 10 con) | 1 gói | ~8.000 | ~8.000 | Mô phỏng trạng thái máy bơm sương | — |
| 5 | **Đèn LED Đỏ** 5mm (gói 10 con) | 1 gói | ~8.000 | ~8.000 | Mô phỏng cảnh báo thu hoạch | — |
| 6 | **Còi chip 5V** (Active Buzzer) | 1 | ~8.000 | ~8.000 | Phát âm thanh cảnh báo thu hoạch | — |
| 7 | **Điện trở 220Ω** (gói 20 con) | 1 gói | ~5.000 | ~5.000 | Hạn dòng cho LED | — |
| 8 | Dây cắm **Test Board** (Đực-Cái, 20 sợi) | 1 bộ | ~18.000 | ~18.000 | Kết nối GPIO giữa ESP32, Relay, Cảm biến | — |
| 9 | Dây cắm **Test Board** (Cái-Cái, 20 sợi) | 1 bộ | ~18.000 | ~18.000 | Kết nối linh hoạt giữa các module | — |
| 10 | **Breadboard** 830 lỗ | 1 | ~25.000 | ~25.000 | Cố định linh kiện trên sa bàn | — |
| 11 | Cáp **Micro USB** (cho ESP32) | 1 | ~15.000 | ~15.000 | Cấp nguồn & nạp code cho ESP32 | — |

---

## 4. Tổng Kết Chi Phí

| Hạng Mục | Số Tiền (VNĐ) |
|---|---|
| Linh kiện đã có | — (không phát sinh) |
| Linh kiện cần mua | **~265.000** |
| **Dự phòng (~15%)** | **~40.000** |
| **Tổng dự kiến** | **~305.000** |

> [!NOTE]
> Giá trên là ước tính tham khảo từ các shop linh kiện điện tử phổ biến (Nshop, ICDAYROI, Shopee). Giá thực tế có thể chênh lệch tùy nguồn mua và thời điểm.

---

## 5. Lưu Ý Khi Mua Hàng

- **DHT11**: Nên mua loại **có board mạch 3 chân** (VCC, DATA, GND) thay vì loại 4 chân rời, đấu nối đơn giản hơn và đã tích hợp sẵn điện trở pull-up.
- **Relay 5V**: Chọn loại **opto-isolated** (cách ly quang) để bảo vệ chân GPIO của ESP32.
- **ESP32-CAM**: Đảm bảo mua kèm **mạch nạp** (FTDI/CH340/CP2102) vì bản thân ESP32-CAM không có cổng USB nạp trực tiếp.
- **Breadboard**: Nên chọn loại **830 lỗ** trở lên để đủ không gian cắm linh kiện.
- **Dây nối**: Mua cả hai loại **Đực-Cái** và **Cái-Cái** để linh hoạt kết nối.

---

## 6. Checklist Kiểm Tra Trước Khi Lắp Ráp

- [ ] Jetson Orin Nano khởi động bình thường, đã cài JetPack
- [ ] Webcam USB nhận diện được trên Jetson (`ls /dev/video*`)
- [ ] ESP32 nạp code được qua Arduino IDE / PlatformIO
- [ ] ESP32-CAM nạp code được qua mạch nạp
- [ ] DHT11 đọc được dữ liệu nhiệt độ, độ ẩm
- [ ] Relay đóng/ngắt bình thường khi nhận tín hiệu HIGH/LOW
- [ ] LED sáng, Còi kêu khi cấp nguồn qua Relay
- [ ] Breadboard và dây nối đủ số lượng

