# 📜 Lịch Sử Các Phiên Làm Việc (Session History & Handoff Logs)

Tệp tin này ghi lại mốc thời gian làm việc của các phiên (session), tóm tắt các việc đã làm, trạng thái hoàn thành và ghi chú bàn giao cho các phiên AI tiếp theo.

---

## 📅 Phiên làm việc: 30/07/2026

### 📋 Công việc thực hiện trong phiên:
1. **Kiểm tra Tổng Quan Dự Án:**
   - Đã rà soát cấu trúc thư mục, git status, git log và các tài liệu kế hoạch ([02_ke_hoach_du_an.md](file:///home/GiaHung/Projects/IoT_project/02_ke_hoach_du_an.md), [03_mo_ta_du_an.md](file:///home/GiaHung/Projects/IoT_project/03_mo_ta_du_an.md)).
   - Kiểm tra báo cáo kết nối Bluetooth BLE direct giữa ESP32-S3 và Jetson ([bluetooth_bridge_report.md](file:///home/GiaHung/Projects/IoT_project/bluetooth_bridge_report.md)).
2. **Kiểm Tra Kết Nối Jetson Orin Nano:**
   - Kiểm tra IP `192.168.55.1` (USB Direct) thành công.
   - Xác minh các cổng dịch vụ mở: Port 22 (SSH), Port 1883 (MQTT Broker), Port 11434 (Ollama Moondream AI).
3. **Kiểm Tra & Kích Hoạt Firebase Realtime Database:**
   - Truy vấn endpoint `https://agrishroom-edge-default-rtdb.asia-southeast1.firebasedatabase.app/status.json`.
   - Xác minh luồng `send_to_firebase()` hoạt động và thử nghiệm ghi dữ liệu thành công.
4. **Kiểm Tra & Khắc Phục Lỗi USB Camera:**
   - Kiểm tra thiết bị V4L2 trên Jetson: Nhận diện `USB2.0 FHD UVC WebCam` tại `/dev/video0`.
   - Chạy script OpenCV đọc khung hình `640x480` thành công.
   - Đồng bộ mã nguồn `backend/` sang Jetson (`rsync`) và khởi chạy ngầm tiến trình `backend.main_jetson` (PID: `3974`).
5. **Thiết Lập Hệ Thống Ghi Log & Quy Tắc Cho AI (Agent Governance):**
   - Đã tạo file quy tắc chuẩn [AGENTS.md](file:///home/GiaHung/Projects/IoT_project/AGENTS.md).
   - Đã tạo thư mục và hệ thống tệp nhật ký [project_logs/](file:///home/GiaHung/Projects/IoT_project/project_logs/).

6. **Khắc Phục Lỗi Đồng Bộ Firebase RTDB Thời Gian Thực:**
   - Phát hiện nguyên nhân lệnh `requests.put()` trong `send_sensor_only_status()` ghi đè xóa sạch các trường dữ liệu AI & Camera mỗi 5s.
   - Đã đổi sang `requests.patch()` (Merge mode), bổ sung mã hóa Base64 ảnh camera và tính toán VPD / Vùng sinh trưởng trực tiếp từ Jetson.
   - Cập nhật `dashboard.js` nhận diện chuỗi Base64 Data URI để hiển thị ảnh camera thời gian thực mượt mà.
7. **Sửa Lỗi Ưu Tiên USB Webcam & Trạng Thái ESP32 Offline:**
   - Đặt `DEFAULT_CAMERA_SOURCE = "webcam"` và ưu tiên đọc từ USB Webcam `/dev/video0`.
   - Sửa chuỗi văn bản thông báo AI trong `dashboard.js` tránh gây hiểu nhầm webcam chưa cắm.
   - Đảm bảo hiển thị chính xác `esp32_online: False` khi ESP32 tắt.
8. **Đồng Bộ & Deploy Web Dashboard lên Firebase Hosting:**
   - Đã biên dịch/định cấu hình và triển khai thành công mã nguồn Web Dashboard (`WEB_IOT/dashboard`) lên Firebase Hosting công cộng.
   - Địa chỉ truy cập toàn cầu: `https://agrishroom-edge.web.app`
9. **Khắc Phục Lỗi Đơ Thẻ AI & Cơ Chế Retry Ollama:**
   - Thêm cơ chế thử lại (Retry) trong `analyze_mushroom_image()` khi Ollama trả phản hồi rỗng.
   - Bổ sung state lưu giữ kết quả phân tích AI gần nhất (`lastValidAiSize`, `lastValidAiConf`) trên Web Dashboard giúp thẻ AI hiển thị mượt mà không chớp giật.
10. **Đảm Bảo Tiến Trình Chụp Ảnh Chạy Ngầm Độc Lập 24/7:**
   - Đã tách ngắt kết nối `main_jetson.py` hoàn toàn khỏi SSH trên Jetson (`< /dev/null &`).
   - Xác minh các bản chụp ảnh tự động mới nhất phát sinh liên tục theo đúng chu kỳ 30s: `22:07:01` -> `22:07:31`.
11. **Chuyển Đổi Hoàn Toàn Sang Kết Nối BLE Không Dây (ESP32 <-> Jetson):**
   - Đã biên dịch & nạp firmware BLE [esp32_iot_node/esp32_iot_node.ino](file:///home/GiaHung/Projects/IoT_project/esp32_iot_node/esp32_iot_node.ino) lên ESP32.
   - Đã khởi chạy dịch vụ cầu nối BLE ngầm `ble_mqtt_bridge.service` trên Jetson.
12. **Cấu Hinh Cảm Biến DHT11 Chân GPIO6:**
   - Đã nạp firmware cấu hình `#define DHTPIN 6` (chân G6) và `#define DHTTYPE DHT11`.
   - Kết nối BLE truyền dữ liệu Nhiệt/Ẩm thực tế từ chân G6: `26.7 °C` / `72.4 %`.
   - Hệ thống tự động kích hoạt bơm sương (`pump: True`) và đồng bộ lên Firebase RTDB & Web Dashboard.
13. **Hỗ Trợ Cảm Biến Kép (Dual Sensors: DHT22 G4 + DHT11 G6):**
   - Đã cập nhật firmware [esp32_iot_node/esp32_iot_node.ino](file:///home/GiaHung/Projects/IoT_project/esp32_iot_node/esp32_iot_node.ino) nhận diện đồng thời cả 2 cảm biến DHT22 (G4) và DHT11 (G6).
   - ESP32 tự động nhận diện DHT22 (G4) làm cảm biến chính: `{"temperature":27.8,"humidity":62.1,"sensor_source":"DHT22 (G4)"}`.
   - Cơ chế tự động chuyển sang DHT11 (G6) nếu DHT22 bị lỏng hoặc rút ra.
14. **Tích Hợp Trọn Bộ Cụm Cảm Biến Từ Repository MinhTriTM/IOT.git:**
   - Đã clone & kiểm tra repository `MinhTriTM/IOT.git`.
   - Đã tích hợp đầy đủ 3 cụm cảm biến: **DHT22/DHT11** (GPIO4/6), **MQ-135 CO2** (GPIO5) và **BH1750 Ánh Sáng** (I2C SDA:8 SCL:9).
   - Truyền nhận trực tiếp thời gian thực qua BLE: `temp: 27.4°C`, `hum: 63.9%`, `co2_ppm: 460`, `light_lux: 150`.
15. **Cập Nhật Script Python Monitor Cảm Biến Trực Quan Cho PC:**
   - Đã nâng cấp `monitor_sensors.py` trên PC để hiển thị trực quan trọn bộ thông số: Nhiệt độ, Độ ẩm, VPD, Nồng độ CO₂ (MQ-135), Cường độ Ánh sáng (BH1750), Nguồn Cảm biến và AI Vision Moondream.
16. **Nâng Cấp Giao Diện Web Dashboard (GUI & UX) & Re-deploy Firebase Hosting:**
   - Đã thiết kế lại Web Dashboard chuẩn Glassmorphism Obsidian Dark Theme với micro-animations.
   - Bổ sung cụm Widget hiển thị CO₂ (MQ-135), Ánh sáng BH1750 Lux, chỉ số VPD và các nút công tắc điều khiển trực tiếp Bơm Phun Sương & Cửa Gió Servo.
17. **Tích Hợp Sơ Đồ Cổng GPIO ESP32-S3 Pinout & Nhật Ký VietGAP từ MinhTriTM/IOT.git:**
   - Đã phân tích kiến trúc bo mạch trong repository `MinhTriTM/IOT.git` và bổ sung 2 Tab mới: **Sơ Đồ ESP32 & Node** và **Nhật Ký VietGAP**.
   - Trực quan hóa trọn bộ sơ đồ đấu nối cổng GPIO (GPIO 4/6 DHT, GPIO 5 MQ-135, GPIO 8/9 BH1750, GPIO 14 Servo SG90, GPIO 15-18 Relays, GPIO 19 LED OK, GPIO 48 Neopixel RGB).
18. **Bổ Sung Chế Độ Kiosk TV Fullscreen & In Báo Cáo PDF VietGAP & Fallback Cảm Biến:**
   - Bổ sung nút bấm `📺 Kiosk TV Mode` chuyển đổi màn hình lớn hiển thị thông số vi khí hậu cỡ lớn cho TV/Monitor nhà nấm.
   - Thêm biểu mẫu nhập Mã Lô Sản Xuất (Batch ID) & Nơi Trồng, hỗ trợ tạo và in Báo Cáo PDF chuẩn VietGAP.
   - Xử lý mượt mà trường hợp ngắt/rút cảm biến nhiệt độ: ESP32 vẫn giữ trạng thái `ĐÃ KẾT NỐI` khi có gói tin các cảm biến khác (CO₂, BH1750), hiển thị nhãn `N/A` an toàn.
   - Re-deploy Firebase Hosting thành công tại `https://agrishroom-edge.web.app`.
26. **Khôi Phục (Rollback) Mã Nguồn Về Phiên Bản Ổn Định Chuẩn Đơn Giản:**
   - Đã hủy bỏ bộ núm xoay 360° và thư viện Preferences, đưa logic điều khiển Servo SG90 Cửa gió về nút bấm **"Mở (180°) / Đóng (0°)"** đơn giản ban đầu.
   - Giữ nguyên cơ chế ngắt xung PWM `ventServo.detach()` sau 0.6s giúp motor Servo quay xong đứng yên 100%, không bị sụt áp hay rên motor.
   - Nạp firmware mới qua `/dev/ttyACM1` và re-deploy Firebase Hosting thành công tại `https://agrishroom-edge.web.app`.

---

## 📅 Phiên làm việc: 31/07/2026

### 📋 Công việc thực hiện trong phiên:
1. **Rà Soát & Cập Nhật Nhật Ký Dự Án:**
   - Đã kiểm tra toàn bộ trạng thái hệ thống, log làm việc và các file nhật ký theo quy tắc `AGENTS.md`.
2. **Đồng Bộ & Đẩy Mã Nguồn Lên GitHub (Git Push):**
   - Đã staging toàn bộ các thay đổi mới nhất (backend, script monitor, firmware esp32, project_logs) và đẩy thành công lên GitHub repository `giahung25/IoT_project.git`.
   - Cập nhật `.gitignore` loại bỏ các tệp tin tạm, log và ảnh chụp camera `backend/captures/`.
   - Đồng bộ & push mã nguồn Web Dashboard trong `WEB_IOT/` lên repository `locnguyenwtf-boop/WEB_IOT.git`.
3. **Tạo Nhánh Mới & Push Sang Repository MinhTriTM/IOT:**
   - Đã thêm remote `upstream` trỏ tới `https://github.com/MinhTriTM/IOT.git`.
   - Đã tạo & đẩy toàn bộ mã nguồn lên nhánh mới độc lập `feature/edge-ai-iot-monitoring` trên repository `MinhTriTM/IOT.git` mà không làm ảnh hưởng đến nhánh `main` hiện tại của repo.

### 📌 Ghi chú bàn giao cho AI ở các phiên tiếp theo:
* **Khi khởi động phiên mới:** AI Agent phải đọc [project_logs/index.md](file:///home/GiaHung/Projects/IoT_project/project_logs/index.md) và [project_logs/issues_and_fixes.md](file:///home/GiaHung/Projects/IoT_project/project_logs/issues_and_fixes.md).
* **Trạng thái Jetson hiện tại:** Tiến trình `backend.main_jetson` và dịch vụ `ble_mqtt_bridge.service` đang chạy ngầm 24/7 trên Jetson. Hệ thống hỗ trợ trọn bộ cụm cảm biến (DHT22/11 + MQ-135 + BH1750) truyền dữ liệu qua sóng BLE không dây (`27.4 °C`, `63.9 %`, `460 ppm`, `150 Lux`), chỉ số VPD (`1.31 kPa`), kết quả AI (`small 83% conf`) và hình ảnh camera Base64 được chụp & đồng bộ định kỳ 30s lên Firebase RTDB.
* **Đường dẫn Web Public:** `https://agrishroom-edge.web.app`
* **Khởi chạy Dashboard trên PC Local:** Sử dụng `./run_dashboard.sh` hoặc `python3 monitor_sensors.py`.

---

## 📅 Phiên làm việc: 05/08/2026

### 📋 Công việc thực hiện trong phiên:
1. **Rà Soát & Giải Đáp Thắc Mắc Về Giao Diện Web Dashboard:**
   - Xác minh trạng thái mã nguồn Web Dashboard trong `WEB_IOT/dashboard` và giải đáp thắc mắc người dùng về lịch sử phiên bản.
2. **Khôi Phục Giao Diện Web Nâng Cấp Đầy Đủ (Restore Full-Featured Dashboard):**
   - Đã khôi phục thành công toàn bộ mã nguồn giao diện Web Dashboard nâng cấp từ commit `4675ca9` trong Git Reflog.
   - Sửa lỗi cú pháp SyntaxError ở cuối tệp [WEB_IOT/dashboard/js/dashboard.js](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/js/dashboard.js).
   - Kiểm tra bằng `node -c` xác nhận 100% không còn lỗi cú pháp JavaScript.
4. **Kiểm Tra & Kích Hoạt Dịch Vụ Kết Nối Trên Jetson Orin Nano:**
   - Phát hiện Jetson kết nối Wi-Fi tại địa chỉ IP: `192.168.1.240`.
   - Đã khởi động và `enable` dịch vụ `ble_mqtt_bridge.service` trên Jetson. Kết nối sóng BLE tới ESP32 thành công (`1C:DB:D4:76:69:2D`).
   - Đã khởi chạy tiến trình `backend.main_jetson` ngầm. Luồng `Firebase Sync` hoạt động thời gian thực 100%, gửi lệnh Bật/Tắt đèn từ xa tới ESP32 mượt mà.
5. **Khắc Phục Lỗi Ảnh Camera Bị Ngược Trên Web:**
   - Bổ sung cấu hình `CAMERA_FLIP_MODE = -1` trong [backend/config.py](file:///home/GiaHung/Projects/IoT_project/backend/config.py) và xử lý lật/xoay 180° tự động bằng OpenCV (`cv2.flip`) trong [backend/vision_analyzer.py](file:///home/GiaHung/Projects/IoT_project/backend/vision_analyzer.py).
   - Đã đồng bộ mã nguồn mới sang Jetson (`rsync`) và kích hoạt lại tiến trình chụp ảnh. Ảnh camera đẩy lên Firebase RTDB & Web Dashboard hiện tại đã được xoay xuôi chuẩn 100%.
6. **Khắc Phục Lỗi Biểu Đồ Lịch Sử Môi Trường (Chart.js) Không Hiển Thị:**
   - Đã nâng cấp hàm `fetchHistory()` trong [WEB_IOT/dashboard/js/dashboard.js](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/js/dashboard.js) hỗ trợ xử lý linh hoạt cả mảng `Array` lẫn đối tượng `Object` từ Firebase RTDB.
   - Bổ sung luồng ghi nhận điểm dữ liệu thực tế liên tục vào `historyBuffer` và tự động căn chỉnh lại kích thước biểu đồ (`historyChart.resize()`) khi chuyển đổi giữa các Tab Navigation.
   - Re-deploy bản fix lên Firebase Hosting thành công tại `https://agrishroom-edge.web.app`.


5. **Cấu Hình Extension Stitch & Nâng Cấp Giao Diện Frontend (Obsidian Cockpit Redesign):**
   - Xác minh thành công extension Stitch MCP Server với API Key của người dùng.
   - Tải mẫu giao diện từ dự án Stitch `Obsidian Mushroom Cockpit Control` (`projects/5595911295547133829`).
   - Tái cấu trúc thành công `WEB_IOT/dashboard/index.html` & `style.css` chuẩn Dark Glassmorphism, bổ sung icon Material Symbols Outlined, typography Outfit & JetBrains Mono, hiệu ứng camera Scanline và bố cục 65/35 Command Center.
   - Bảo tồn 100% logic JavaScript và mã nguồn backend.
   - Re-deploy thành công bản nâng cấp lên Firebase Hosting tại `https://agrishroom-edge.web.app`.



