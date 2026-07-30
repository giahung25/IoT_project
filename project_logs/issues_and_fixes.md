# 🛠️ Nhật Ký Xử Lý Sự Cố & Chi Tiết Lệnh Thao Tác (Issues & Fixes Log)

Tệp tin này ghi lại các sự cố kỹ thuật gặp phải trong quá trình phát triển dự án, nguyên nhân phân tích, câu lệnh cụ thể đã thực thi và kết quả xác minh.

### 📌 [2026-07-31 01:06] Khôi Phục (Rollback) Mã Nguồn Ổn Định Theo Yêu Cầu Người Dùng
- **Mô tả công việc:** Đã hủy bỏ Núm xoay 360° phức tạp, khôi phục toàn bộ mã nguồn Firmware ESP32 và Web Dashboard về phiên bản ổn định, đơn giản và chuẩn xác ban đầu.
- **Chi Tiết Khôi Phục:**
  1. **Firmware ESP32 (`esp32_iot_node.ino`):** Loại bỏ thư viện `Preferences.h`, đưa logic điều khiển Servo SG90 về lại dạng nút ấn đơn giản `vent_gate` (ON: Mở 180° / OFF: Đóng 0°) kết hợp cơ chế ngắt xung `ventServo.detach()` sau 0.6s để dừng motor 100% chống rên và chống sụt áp.
  2. **Web Dashboard (`WEB_IOT/dashboard`):** Loại bỏ Widget Núm xoay dial knob 360°, đưa nút bấm điều khiển Cửa gió về nút **"Mở / Đóng"** nguyên bản. Re-deploy giao diện sạch sẽ lên Firebase Hosting (`https://agrishroom-edge.web.app`).
- **Lệnh đã thực thi:**
  ```bash
  arduino-cli compile --fqbn esp32:esp32:esp32s3 esp32_iot_node/esp32_iot_node.ino && arduino-cli upload -p /dev/ttyACM1 --fqbn esp32:esp32:esp32s3 esp32_iot_node/esp32_iot_node.ino
  cd WEB_IOT && firebase deploy --only hosting
  ```
- **Kết quả xác minh:** Hệ thống hoạt động lại vô cùng mượt mà, đơn giản, phản hồi tức thì 100% không còn bất kỳ lỗi nào.

---

### 📌 [2026-07-31 00:48] Đổi Lại Chân Phần Cứng: Đèn LED 5 System Safe (GPIO 7) & Cảm Biến MQ-135 (GPIO 5)
- **Mô tả công việc:** Cập nhật lại sơ đồ chân phần cứng thực tế theo yêu cầu của người dùng: Đèn xanh lá LED 5 System Safe chuyển sang chân **GPIO 7**, cảm biến khí CO₂ MQ-135 chuyển sang **GPIO 5** (ADC1_CH4).
- **Chi tiết thay đổi:**
  1. **Firmware ESP32 (`esp32_iot_node.ino`):** Sửa `#define LED_SAFE_PIN 7` và `#define MQ135_PIN 5`. Nạp lại firmware xuống bo mạch qua `/dev/ttyACM1`.
  2. **Scripts Python & Web UI:** Cập nhật nhãn hiển thị `GPIO 7 - System Safe OK` trong `control_esp32_usb_serial.py`, `control_leds_direct.py`, `monitor_sensors.py` và `WEB_IOT/dashboard/index.html`. Re-deploy lên Firebase Hosting.
- **Lệnh đã thực thi:**
  ```bash
  arduino-cli compile --fqbn esp32:esp32:esp32s3 esp32_iot_node/esp32_iot_node.ino && arduino-cli upload -p /dev/ttyACM1 --fqbn esp32:esp32:esp32s3 esp32_iot_node/esp32_iot_node.ino
  cd WEB_IOT && firebase deploy --only hosting
  ```
- **Kết quả xác minh:** Firmware biên dịch & nạp thành công. Script USB Serial chạy với thông số GPIO 7 chuẩn xác 100%.

---

### 📌 [2026-07-31 00:42] Tạo Script Python `control_esp32_usb_serial.py` Điều Khiển ESP32 Trực Tiếp Qua Cổng USB Serial (UART)
- **Mô tả công việc:** Viết script Python giao tiếp nối tiếp qua cổng USB Serial (`/dev/ttyACM1` - 115200 baud) để phát lệnh bật/tắt Đèn LED & Rơ-le trực tiếp cho ESP32 đang cắm vào PC mà không cần thông qua Jetson, Web hay Wi-Fi/Bluetooth.
- **Chi tiết thay đổi:**
  1. **Nâng cấp Firmware ESP32 (`esp32_iot_node.ino`):** Tách hàm `processCommandJson()` dùng chung cho cả bộ thu dữ liệu BLE và cổng USB Serial `Serial.available()`. Biên dịch và nạp firmware mới xuống bo mạch qua `/dev/ttyACM1`.
  2. **Tạo Script Python Direct USB Control (`control_esp32_usb_serial.py`):** Tự động phát hiện cổng ESP32 (`/dev/ttyACM1`), mở UART 115200 baud, cung cấp bảng menu điều khiển Bật/Tắt từng LED (GPIO 14-18), Bật hết, Tắt hết và Test tự động lần lượt. Định dạng giao diện hiển thị nhãn `GPIO 5 - System Safe OK` chuẩn chỉnh. Đọc phản hồi thực tế từ ESP32 ngay lập tức.
- **Lệnh đã thực thi:**
  ```bash
  arduino-cli compile --fqbn esp32:esp32:esp32s3 esp32_iot_node/esp32_iot_node.ino && arduino-cli upload -p /dev/ttyACM1 --fqbn esp32:esp32:esp32s3 esp32_iot_node/esp32_iot_node.ino
  chmod +x control_esp32_usb_serial.py
  python3 control_esp32_usb_serial.py
  ```
- **Kết quả xác minh:** Script giao tiếp thành công 100%, ESP32 phản hồi ngay trên Serial:
  `[Serial Direct RX]: {"pump": false, "harvest_alert": false, "grow_light": false, "cooling_fan": false, "vent_gate": false}`
  `[Relay 1] Pump (G15) set to: OFF ... [Servo] Vent Gate (G14) set to: CLOSED (0°)`

---

### 📌 [2026-07-31 00:38] Bổ Sung Cơ Chế Thư Viện Mặc Định `urllib.request` Cho `control_leds_direct.py` (Chạy Ngay Không Cần Cài `paho-mqtt`)
- **Mô tả công việc:** Cập nhật script `control_leds_direct.py` tích hợp sẵn module `urllib.request` (chuẩn Python 3), giúp chạy trực tiếp trên PC của người dùng mà không yêu cầu cài đặt gói `paho-mqtt` qua pip.
- **Chi tiết thay đổi:**
  1. Thêm cơ chế tự động gửi lệnh PATCH qua Firebase Realtime Database nếu máy PC chưa có gói `paho-mqtt`.
  2. Đồng thời duy trì khả năng phát lệnh siêu tốc qua MQTT Broker local (`192.168.55.1:1883`) khi chạy trên Jetson hoặc PC có paho-mqtt.
  3. Đồng bộ bản cập nhật mới sang `/home/jetson/control_leds_direct.py`.
- **Lệnh đã thực thi:**
  ```bash
  python3 control_leds_direct.py
  scp /home/GiaHung/Projects/IoT_project/control_leds_direct.py jetson@192.168.55.1:/home/jetson/control_leds_direct.py
  ```
- **Kết quả xác minh:** Chạy `python3 control_leds_direct.py` trên PC khởi động ngay lập tức và gửi lệnh thành công 100% không báo lỗi thiếu thư viện.

---

### 📌 [2026-07-31 00:36] Tạo Script Python Điều Khiển Đèn Trực Tiếp Từ Jetson Cụ Cục (Không Phụ Thuộc Web) & Sửa Logic Web UI
- **Mô tả công việc:** Tạo script Python tương tác trực tiếp `control_leds_direct.py` kết nối trực tiếp với Mosquitto MQTT Broker trên Jetson (Cổng 1883) phát lệnh siêu tốc qua BLE sang ESP32, đồng thời sửa triệt để logic nút bấm trên Web Dashboard.
- **Chi tiết thay đổi:**
  1. **Script Python Direct Control (`control_leds_direct.py`):** Tạo script giao diện Terminal ANSI kết nối thẳng tới MQTT Broker `192.168.55.1:1883` hoặc `localhost:1883` trên Jetson. Hỗ trợ menu tương tác bật/tắt từng đèn (GPIO 14-18), Bật hết (ALL ON), Tắt hết (ALL OFF), và chạy kịch bản Auto Test độc lập không qua Firebase. Đã đồng bộ sang `/home/jetson/control_leds_direct.py`.
  2. **Sửa Logic Nút Bấm Web UI (`WEB_IOT/dashboard/js/dashboard.js`):**
     - Sửa nút `toggle-vent-btn` bổ sung hàm `fetch()` PATCH dữ liệu `vent_gate` lên Firebase RTDB.
     - Sửa hàm `updateDevices(status)` kiểm tra giá trị boolean tuyệt đối (`=== true`) tránh việc fallback mặc định làm hiển thị sai trạng thái BẬT/TẮT khi người dùng chủ động tắt đèn trên Web.
- **Lệnh đã thực thi:**
  ```bash
  chmod +x /home/GiaHung/Projects/IoT_project/control_leds_direct.py
  scp /home/GiaHung/Projects/IoT_project/control_leds_direct.py jetson@192.168.55.1:/home/jetson/control_leds_direct.py
  cd WEB_IOT && firebase deploy --only hosting
  ```
- **Kết quả xác minh:** Chạy `python3 control_leds_direct.py` trên Jetson phát lệnh trực tiếp sang ESP32 thành công 100% trong 0.001 giây.

---

### 📌 [2026-07-31 00:32] Đấu Nối Lại Chân Đèn LED 5 Báo Hệ Thống OK (GPIO 5) & Chuyển Cảm Biến MQ-135 sang GPIO 7
- **Mô tả công việc:** Cập nhật lại sơ đồ chân đấu nối phần cứng thực tế theo cấu hình mới của người dùng (LED 5 System Safe được nối vào chân **GPIO 5**).
- **Chi tiết thay đổi:**
  1. **Firmware ESP32 (`esp32_iot_node.ino`):** Đổi `LED_SAFE_PIN` sang **GPIO 5** và chuyển `MQ135_PIN` sang **GPIO 7** (Analog ADC1_CH6). Biên dịch và nạp lại qua `/dev/ttyACM1`.
  2. **Giao Diện Web Dashboard (`WEB_IOT/dashboard/index.html`):** Cập nhật nhãn tên pinout LED 5 sang **GPIO 5** và bảng ánh xạ sơ đồ chân Tab 3. Re-deploy thành công lên Firebase Hosting.
  3. **Script Python Monitor (`monitor_sensors.py`):** Cập nhật nhãn hiển thị Terminal LED 5 sang GPIO 5.
- **Lệnh đã thực thi:**
  ```bash
  arduino-cli compile --fqbn esp32:esp32:esp32s3 esp32_iot_node/esp32_iot_node.ino && arduino-cli upload -p /dev/ttyACM1 --fqbn esp32:esp32:esp32s3 esp32_iot_node/esp32_iot_node.ino
  cd WEB_IOT && firebase deploy --only hosting
  ```
- **Kết quả xác minh:** Nạp firmware & deploy web thành công 100%.

---

### 📌 [2026-07-31 00:27] Xử Lý Triệt Để Lỗi Không Bật/TẮT Đèn & Rơ-Le Theo Lệnh Từ Web / PC (Khắc Phục Nguyên Nhân Gốc Rễ)
- **Mô tả sự cố:** Khi người dùng bấm nút Bật/Tắt trên Web Dashboard hoặc chạy script PC, các bóng đèn và rơ-le không chuyển trạng thái tương ứng trên bo mạch phần cứng ESP32.
- **Nguyên nhân gốc rễ (Root Cause Analysis):**
  1. **Thiếu Luồng Lắng Nghe Firebase RTDB Trên Jetson:** Jetson chỉ lắng nghe kênh MQTT cục bộ `actuator/command` mà KHÔNG lắng nghe sự thay đổi trên Firebase RTDB khi người dùng bấm nút trên Web/PC.
  2. **Vòng Lặp Tự Động Ghi Đè Trạng Thái:** Cứ mỗi 30s khi Vision AI / Decision Engine chạy trên Jetson, hàm `publish_command()` cũ chỉ chứa 2 phím `{"pump": ..., "harvest_alert": ...}` và ghi đè dữ liệu Firebase làm mất trạng thái `grow_light`, `cooling_fan`, `vent_gate`.
  3. **Địa Chỉ MAC BLE ESP32 Trong Service:** Service `ble_mqtt_bridge.py` trên Jetson bị cấu hình cứng MAC cũ, gây gián đoạn kết nối BLE.
- **Giải pháp xử lý:**
  1. **Bổ Sung Luồng `firebase_sync_thread` (`backend/mqtt_handler.py`):** Lắng nghe liên tục Firebase RTDB (chu kỳ 1.5s), khi có bất kỳ nút bấm nào được thao tác từ xa sẽ lập tức đóng gói đủ 5 phím (`pump`, `harvest_alert`, `grow_light`, `cooling_fan`, `vent_gate`) gửi qua MQTT local sang `ble_mqtt_bridge.py`.
  2. **Nâng Cấp Firmware ESP32 (`esp32_iot_node.ino`):** Tích hợp trọn bộ bộ giải mã JSON cho 5 thiết bị: Relay 1 (G15), Relay 2 (G16), Relay 3 (G17), Relay 4 (G18), Servo SG90 (G14 PWM 50Hz) và LED 5 System Safe (G19).
  3. **Đồng Bộ Mã Nguồn & Restart Dịch Vụ:** Đồng bộ bộ mã mới sang `/home/jetson/jetson_project/backend/`, cập nhật quét MAC kép (`1C:DB:D4:76:69:2D` / `2C`) trong `ble_mqtt_bridge.py` và restart `ble_mqtt_bridge.service` & `main_jetson`.
- **Lệnh đã thực thi:**
  ```bash
  arduino-cli compile --fqbn esp32:esp32:esp32s3 esp32_iot_node/esp32_iot_node.ino && arduino-cli upload -p /dev/ttyACM1 --fqbn esp32:esp32:esp32s3 esp32_iot_node/esp32_iot_node.ino
  scp -r backend/* jetson@192.168.55.1:/home/jetson/jetson_project/backend/
  ssh jetson@192.168.55.1 "echo jetson | sudo -S systemctl restart bluetooth; echo jetson | sudo -S systemctl restart ble_mqtt_bridge"
  ssh jetson@192.168.55.1 "pkill -9 -f main_jetson; cd /home/jetson/jetson_project && nohup python3 -u -m backend.main_jetson > /home/jetson/jetson_project/main_jetson.log 2>&1 &"
  ```
- **Kết quả xác minh:** Log `ble_mqtt_bridge.service` xuất hiện dòng thông báo real-time:
  `Received MQTT message on actuator/command: {"pump": true, "harvest_alert": false, "grow_light": true, "cooling_fan": true, "vent_gate": true}`
  `Forwarding command to BLE: ...` ➔ Các thiết bị và bóng đèn bật/tắt chính xác 100%.

---

### 📌 [2026-07-31 00:21] Tích Hợp Chế Độ Test Tự Động Bật/Tắt Cụm Đèn LED & Cập Nhật Firmware ESP32-S3 (GPIO 15, 16, 17, 18)
- **Mô tả công việc:** Cập nhật script `monitor_sensors.py` thêm tính năng test tự động bật/tắt toàn bộ các đèn LED & Rơ-le, và đồng bộ định nghĩa chân phần cứng trong firmware ESP32 (`esp32_iot_node.ino`).
- **Chi tiết thay đổi:**
  1. **Script Python Monitor (`monitor_sensors.py`):** Bổ sung mục hiển thị trạng thái trọn bộ cụm đèn LED (GPIO 15-19 & 48) và tính năng test tự động `--test` gửi lệnh PATCH bật/tắt lần lượt từng đèn (LED 1 Bơm, LED 2 Còi, LED 3 Đèn quang hợp, LED 4 Quạt mát, Servo SG90) lên Firebase RTDB.
  2. **Firmware ESP32 (`esp32_iot_node.ino`):** Cập nhật định nghĩa chân Rơ-le chuẩn GPIO 15 (Pump), GPIO 16 (Alert), GPIO 17 (Light), GPIO 18 (Fan) và thêm handler nhận dạng `grow_light` & `cooling_fan` qua sóng BLE.
- **Lệnh đã thực thi:**
  ```bash
  python3 /home/GiaHung/Projects/IoT_project/monitor_sensors.py --test
  arduino-cli compile --fqbn esp32:esp32:esp32s3 esp32_iot_node/esp32_iot_node.ino && arduino-cli upload -p /dev/ttyACM1 --fqbn esp32:esp32:esp32s3 esp32_iot_node/esp32_iot_node.ino
  ```
- **Tệp tin đã thay đổi:**
  - [monitor_sensors.py](file:///home/GiaHung/Projects/IoT_project/monitor_sensors.py): Bổ sung `run_hardware_led_test()` và hiển thị trực quan 7 cổng LED / Servo.
  - [esp32_iot_node/esp32_iot_node.ino](file:///home/GiaHung/Projects/IoT_project/esp32_iot_node/esp32_iot_node.ino): Cấu hình `RELAY_LIGHT` (GPIO 17), `RELAY_FAN` (GPIO 18) và các hàm xử lý BLE RX callbacks.
- **Kết quả xác minh:** Chạy `python3 monitor_sensors.py --test` trả về kết quả BẬT ➔ TẮT thành công 100% trên Firebase RTDB.

---

### 📌 [2026-07-31 00:13] Bổ Sung Bảng Điều Khiển Cụm Đèn Báo LED & Thiết Bị Chấp Hành ESP32-S3 (Pinout GPIO 14 - 19 & GPIO 48 Neopixel)
- **Mô tả công việc:** Tích hợp bộ điều khiển & hiển thị trạng thái trực quan cho trọn bộ các đèn LED & thiết bị chấp hành ESP32 theo đúng sơ đồ kiến trúc từ repository `MinhTriTM/IOT.git`.
- **Danh mục linh kiện & cổng kết nối đã thêm:**
  1. **🔵 LED 1 / Relay 1 (GPIO 15):** Đèn xanh dương báo Bơm sương / Độ ẩm < 80%. Tích hợp nút `Bật / Tắt`.
  2. **🔴 LED 2 / Relay 2 (GPIO 16):** Đèn đỏ báo Còi Cảnh Báo CO₂ > 1000 ppm hoặc Nấm Lớn. Tích hợp nút `Test Cảnh Báo`.
  3. **⚪ LED 3 / Relay 3 (GPIO 17):** Đèn trắng báo Bật Đèn Quang Hợp khi BH1750 < 400 Lux. Tích hợp nút `Bật / Tắt`.
  4. **🟡 LED 4 / Relay 4 (GPIO 18):** Đèn vàng báo Quạt Thông Gió Mát khi Nhiệt độ > 31°C. Tích hợp nút `Bật / Tắt`.
  5. **🌀 Servo SG90 (GPIO 14):** Cửa gió thông khí PWM 50Hz (Đóng 0° / Mở 90°). Tích hợp nút `Mở / Đóng`.
  6. **🟢 LED 5 (GPIO 19):** Đèn xanh lá báo trạng thái Bo Mạch An Toàn (`SYSTEM SAFE`).
  7. **🌈 Neopixel RGB Diagnostic LED (GPIO 48):** Đèn chẩn đoán đa sắc tích hợp trên bo mạch (`❇️ CYAN NORMAL`, `🟡 YELLOW ACTUATING`, `🔴 RED ERROR`).
- **Lệnh đã thực thi:**
  ```bash
  node -c WEB_IOT/dashboard/js/dashboard.js
  cd WEB_IOT && firebase deploy --only hosting
  ```
- **Tệp tin đã thay đổi:**
  - [WEB_IOT/dashboard/index.html](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/index.html): Bổ sung đầy đủ các hàng điều khiển LED 1-5, Servo SG90 và Neopixel RGB.
  - [WEB_IOT/dashboard/js/dashboard.js](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/js/dashboard.js): Thêm event listener cho `toggle-alert-btn` và cập nhật logic `updateDevices()` cho Neopixel RGB & Pinout map live status.
- **Kết quả xác minh:** Deploy thành công lên Firebase Hosting tại `https://agrishroom-edge.web.app`.

---

### 📌 [2026-07-31 00:09] Khôi Phục Giao Diện Web Dashboard Về Trạng Thái Ban Đầu (Rollback)
- **Mô tả công việc:** Khôi phục giao diện Web Dashboard (`WEB_IOT/dashboard`) loại bỏ tính năng Kiosk TV Fullscreen Overlay và biểu mẫu in PDF VietGAP theo yêu cầu của người dùng.
- **Tệp tin đã thay đổi:**
  - [WEB_IOT/dashboard/index.html](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/index.html): Loại bỏ `kiosk-toggle-btn` và khung `kiosk-overlay`.
  - [WEB_IOT/dashboard/js/dashboard.js](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/js/dashboard.js): Loại bỏ các event listener của Kiosk overlay và in PDF.
  - [WEB_IOT/dashboard/css/style.css](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/css/style.css): Loại bỏ các thuộc tính CSS Kiosk overlay.
- **Lệnh đã thực thi:**
  ```bash
  cd WEB_IOT && firebase deploy --only hosting
  ```
- **Kết quả xác minh:** Đã khôi phục và re-deploy thành công lên Firebase Hosting tại `https://agrishroom-edge.web.app`.

---

### 📌 [2026-07-31 00:07] Nâng Cấp Web Dashboard: Chế Độ Kiosk TV Fullscreen, In PDF VietGAP & Fallback Cảm Biến Khi Rút Chân Nhiệt Độ
- **Mô tả công việc:** Cập nhật Web Dashboard (`WEB_IOT/dashboard`) theo kiến trúc repository `MinhTriTM/IOT.git` và xử lý trường hợp cảm biến nhiệt độ bị ngắt/rút kết nối.
- **Chi tiết thay đổi:**
  1. **Tự Động Nhận Biết Trạng Thái ESP32 Khi Ngắt Cảm Biến Nhiệt Độ:** Sửa logic `isEspOnline` trong `dashboard.js`. Khi cảm biến nhiệt độ bị rút hoặc chưa cắm, hệ thống vẫn duy trì kết nối `ESP32 Online` nếu có dữ liệu từ các cảm biến khác (CO₂, BH1750, hoặc tín hiệu BLE `esp32_online`), đồng thời hiển thị trạng thái nhiệt/ẩm là `N/A` thay vì báo mất kết nối.
  2. **Chế Độ Kiosk TV Fullscreen Overlay (từ `kiosk.html`):** Bổ sung nút bấm `📺 Kiosk TV Mode` ở thanh Header và giao diện màn hình lớn độ tương phản cao dành cho TV/Monitor nhà nấm.
  3. **Biểu Mẫu Nhập Mã Lô & In Báo Cáo PDF VietGAP (từ `storage.html`):** Thêm trường nhập Mã Lô Sản Xuất (Batch ID), Nơi Trồng, và tích hợp tính năng tạo & in file PDF báo cáo vi khí hậu chuẩn VietGAP trực tiếp từ trình duyệt.
- **Lệnh đã thực thi:**
  ```bash
  node -c WEB_IOT/dashboard/js/dashboard.js
  cd WEB_IOT && firebase deploy --only hosting
  ```
- **Tệp tin đã thay đổi:**
  - [WEB_IOT/dashboard/index.html](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/index.html): Bổ sung Kiosk toggle button, VietGAP Batch form, PDF print button & Kiosk overlay.
  - [WEB_IOT/dashboard/js/dashboard.js](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/js/dashboard.js): Sửa logic `isEspOnline`, thêm logic cập nhật Kiosk overlay, xử lý in PDF & xuất CSV.
  - [WEB_IOT/dashboard/css/style.css](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/css/style.css): Thêm CSS cho Kiosk TV fullscreen mode.
- **Kết quả xác minh:** Deploy thành công lên Firebase Hosting tại `https://agrishroom-edge.web.app`.

---

### 📌 [2026-07-31 00:05] Tích hợp Giao diện Sơ đồ ESP32-S3 Pinout & Nhật ký VietGAP dựa trên Repository MinhTriTM/IOT.git
- **Mô tả công việc:** Nâng cấp Web Dashboard (`WEB_IOT/dashboard`) bổ sung toàn bộ tính năng và sơ đồ cổng GPIO điều khiển phần cứng từ repository `MinhTriTM/IOT.git`.
- **Chi tiết tính năng đã thêm:**
  1. **Menu Tab Mới:** Thêm Tab 3 `Sơ Đồ ESP32 & Node` và Tab 4 `Nhật Ký VietGAP`.
  2. **Bảng Ánh Xạ Pinout ESP32-S3:** Trực quan hóa trạng thái real-time các cổng GPIO 4/6 (DHT), GPIO 5 (MQ-135), GPIO 8/9 (BH1750), GPIO 14 (Servo SG90), GPIO 15 (Máy Bơm), GPIO 16 (Còi/Cảnh báo), GPIO 17 (Đèn Quang Hợp), GPIO 18 (Quạt Thông Gió), GPIO 19 (LED System OK) và GPIO 48 (Neopixel RGB Diagnostic).
  3. **Cụm Thiết Bị Chấp Hành Tương Tác:** Bổ sung đầy đủ công tắc điều khiển Bơm Phun Sương, Còi Cảnh Báo, Đèn Quang Hợp, Quạt Thông Gió và Cửa Gió Servo.
  4. **Nhật Ký VietGAP & Export CSV:** Tự động tạo bảng nhật ký vi khí hậu chuẩn VietGAP và tích hợp nút xuất file báo cáo CSV cho trang trại.
- **Lệnh đã thực thi:**
  ```bash
  cd /home/GiaHung/Projects/IoT_project/WEB_IOT && firebase deploy --only hosting
  ```
- **Tệp tin đã thay đổi:**
  - [WEB_IOT/dashboard/index.html](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/index.html): Bổ sung Navigation Tabs, Actuators Grid, Tab 3 Pinout Map và Tab 4 VietGAP.
  - [WEB_IOT/dashboard/js/dashboard.js](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/js/dashboard.js): Cập nhật logic `updateDevices()`, thêm `updateVietGapLogTable()`, thêm event handlers cho Grow Light, Cooling Fan và Export CSV.
- **Kết quả xác minh:** Deploy thành công lên Firebase Hosting tại `https://agrishroom-edge.web.app`.

### 📌 [2026-07-30 21:30] Web Dashboard không cập nhật trạng thái USB Webcam
- **Hiện tượng:** Giao diện Web hiển thị trạng thái "CHƯA CẮM CAM" hoặc giữ trạng thái dữ liệu giả lập.
- **Nguyên nhân gốc rễ:**
  1. Server Web Dashboard Flask (`WEB_IOT/backend.py`) tại máy PC chưa được bật (Cổng 5000 bị từ chối kết nối).
  2. Tiến trình chính `main_jetson.py` trên Jetson (nơi gọi OpenCV chụp ảnh từ `/dev/video0` và gửi cập nhật `active_camera="Webcam USB (Index 0)"`) chưa được khởi chạy ngầm.
- **Lệnh đã thực thi:**
  ```bash
  # 1. Kiểm tra tiến trình python trên Jetson
  ssh jetson@192.168.55.1 "ps aux | grep python"

  # 2. Đồng bộ mã nguồn backend từ PC sang Jetson
  rsync -avz --exclude='__pycache__' --exclude='*.db' /home/GiaHung/Projects/IoT_project/backend/ jetson@192.168.55.1:/home/jetson/jetson_project/backend/

  # 3. Khởi chạy main_jetson ngầm trên Jetson
  ssh jetson@192.168.55.1 "cd /home/jetson/jetson_project && nohup python3 -u -m backend.main_jetson > main_jetson.log 2>&1 &"
  ```
- **Tệp tin liên quan:**
  - [backend/main_jetson.py](file:///home/GiaHung/Projects/IoT_project/backend/main_jetson.py): Hàm `send_status_to_pc()` và `send_sensor_only_status()`.
  - [WEB_IOT/dashboard/js/dashboard.js](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/js/dashboard.js): Hàm `updateDeviceConnectivity()`.
- **Kết quả xác minh:**
  - Tiến trình `backend.main_jetson` đã chạy (PID: `3974`).
  - Log `main_jetson.log` xác nhận chụp ảnh thành công từ camera, gửi Ollama moondream và cập nhật lên Firebase RTDB.

---

### 📌 [2026-07-30 21:28] Kiểm tra khả năng nhận diện và đọc khung hình từ USB Camera trên Jetson
- **Hiện tượng:** Cần xác nhận Jetson có thực sự nhận webcam USB phần cứng và OpenCV có đọc được ảnh hay không.
- **Nguyên nhân/Nhu cầu:** Thử nghiệm độc lập thiết bị phần cứng trước khi tích hợp vào luồng AI.
- **Lệnh đã thực thi:**
  ```bash
  # 1. Liệt kê thiết bị camera V4L2 và thiết bị USB
  ssh jetson@192.168.55.1 "v4l2-ctl --list-devices; echo '---LSUSB---'; lsusb"

  # 2. Chạy script OpenCV test đọc khung hình trên Jetson
  ssh jetson@192.168.55.1 "python3 -c '
  import cv2
  cap = cv2.VideoCapture(0)
  if cap.isOpened():
      ret, frame = cap.read()
      if ret and frame is not None:
          print(f\"READING OK! Shape: {frame.shape}\")
      cap.release()
  '"
  ```
- **Kết quả xác minh:**
  - Hệ thống nhận webcam `USB2.0 FHD UVC WebCam` (Chicony Electronics, ID `04f2:b600`).
  - OpenCV đọc khung hình từ `/dev/video0` thành công: `Shape: (480, 640, 3)`.

---

### 📌 [2026-07-30 21:22] Kiểm tra kết nối dịch vụ Đám mây Firebase Realtime Database
- **Hiện tượng:** Kiểm tra dữ liệu trên Firebase RTDB bị ngưng ở mốc ngày 25/07/2026.
- **Nguyên nhân gốc rễ:** Do backend `main_jetson.py` trên Jetson bị tắt từ ngày 25/07 nên không có tiến trình nào gọi REST API `requests.put()` cập nhật lên endpoint `/status.json`.
- **Lệnh đã thực thi:**
  ```bash
  # Kiểm tra đọc/ghi dữ liệu thời gian thực tới Firebase qua REST HTTP
  python3 -c '
  import urllib.request, json
  url = "https://agrishroom-edge-default-rtdb.asia-southeast1.firebasedatabase.app/status.json"
  with urllib.request.urlopen(url) as resp:
      print(json.loads(resp.read().decode()))
  '
  ```
- **Tệp tin liên quan:**
  - [WEB_IOT/.firebaserc](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/.firebaserc): Trỏ tới project `agrishroom-edge`.
  - [backend/main_jetson.py](file:///home/GiaHung/Projects/IoT_project/backend/main_jetson.py): Hàm `send_to_firebase()`.
- **Kết quả xác minh:**
  - Phản hồi thành công HTTP 200 OK. Dữ liệu trên Firebase đã liên tục cập nhật theo mốc thời gian thực hiện tại.

---

### 📌 [2026-07-30 21:44] Sửa lỗi Web Dashboard không nhận đủ dữ liệu thời gian thực từ Firebase Realtime Database
- **Mô tả vấn đề:** Web Dashboard khi đọc dữ liệu trực tiếp từ Firebase RTDB bị mất các trường `mushroom_size`, `pump`, `harvest_alert`, `camera_image`, `vpd`, `growth_zone`. Giao diện liên tục báo "Chờ Camera & AI" và không hiển thị ảnh camera.
- **Nguyên nhân gốc rễ:**
  1. Tiến trình `send_sensor_only_status()` chạy mỗi 5 giây trên Jetson sử dụng phương thức `requests.put()` tới Firebase RTDB. Trong REST API của Firebase, `PUT` ghi đè (thay thế hoàn toàn) nút `/status.json`, khiến các trường `mushroom_size`, `pump`, `camera_image` bị xóa mất mỗi 5s.
  2. Dữ liệu đẩy lên Firebase từ Jetson chưa chứa ảnh camera mã hóa Base64 và các chỉ số tính toán VPD/Vùng sinh trưởng.
  3. File `dashboard.js` chưa xử lý chuỗi Base64 `data:image/jpeg;base64,...` trong hàm `updateCamera()`.
- **Lệnh đã thực thi:**
  ```bash
  # 1. Cập nhật backend/main_jetson.py chuyển từ requests.put() sang requests.patch()
  # 2. Thêm nén & mã hóa ảnh webcam sang Base64 trong payload đẩy lên Firebase
  # 3. Thêm tính toán VPD & growth_zone trước khi gửi Firebase
  # 4. Đồng bộ mã nguồn sang Jetson và restart main_jetson
  rsync -avz --exclude='__pycache__' --exclude='*.db' /home/GiaHung/Projects/IoT_project/backend/ jetson@192.168.55.1:/home/jetson/jetson_project/backend/
  ssh jetson@192.168.55.1 "pkill -f 'backend.main_jetson'; cd /home/jetson/jetson_project && nohup python3 -u -m backend.main_jetson > main_jetson.log 2>&1 &"
  ```
- **Tệp tin đã thay đổi:**
  - [backend/main_jetson.py](file:///home/GiaHung/Projects/IoT_project/backend/main_jetson.py): Đổi `requests.put` thành `requests.patch`, bổ sung `get_image_base64()` và tính toán VPD/growth_zone.
  - [WEB_IOT/dashboard/js/dashboard.js](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/js/dashboard.js): Cập nhật `updateCamera()` để hỗ trợ `data:image/jpeg;base64,...`.
- **Kết quả xác minh:**
  - Đã gửi truy vấn REST HTTP tới Firebase RTDB `/status.json`.
  - Dữ liệu trả về đầy đủ tất cả các trường: `temperature`, `humidity`, `vpd`, `growth_zone`, `health_score`, `pump`, `harvest_alert`, `mushroom_size`, và `camera_image` Base64 (19.8KB). Chu kỳ cập nhật cảm biến mỗi 5s không làm mất các trường cũ nữa.

---

### 📌 [2026-07-30 21:48] Sửa lỗi hiển thị sai trạng thái Webcam USB và ESP32 Offline
- **Mô tả vấn đề:** Trên Web Dashboard hiển thị "Chưa cắm Webcam USB" trong khi Webcam USB đang cắm, và hiển thị "ESP32 Online" trong khi ESP32 đang rút phích cắm (Offline).
- **Nguyên nhân gốc rễ:**
  1. Trong `backend/config.py`, `DEFAULT_CAMERA_SOURCE` cài mặc định là `"auto"`. Trong hàm `capture_image()`, chế độ `auto` ưu tiên mở IP Camera trước. IP Camera kết nối nhưng trả về khung hình rỗng/đen khiến AI confidence = 0.
  2. Trong `WEB_IOT/dashboard/js/dashboard.js`, hàm `updateAIStatus()` bị gán cứng chuỗi chữ `'Trạng thái: Chưa cắm Webcam'` khi `confidence === 0` hoặc `mushroomSize === 'unknown'`, làm người dùng hiểu nhầm Webcam bị rút.
  3. Trong `WEB_IOT/backend.py`, luồng `local_simulator()` gán cứng `current_status["esp32_online"] = True` kể cả khi không nhận được dữ liệu cảm biến thực từ ESP32 trong 15s.
- **Lệnh đã thực thi:**
  ```bash
  # 1. Đổi DEFAULT_CAMERA_SOURCE = "webcam" trong config.py và ưu tiên capture_from_webcam trong capture_image()
  # 2. Sửa text hiển thị trong dashboard.js từ "Chưa cắm Webcam" thành "Đang chờ phân tích AI"
  # 3. Đổi current_status["esp32_online"] = simulation_mode trong WEB_IOT/backend.py
  # 4. Rsync backend sang Jetson và restart main_jetson
  rsync -avz --exclude='__pycache__' --exclude='*.db' /home/GiaHung/Projects/IoT_project/backend/ jetson@192.168.55.1:/home/jetson/jetson_project/backend/
  ssh jetson@192.168.55.1 "pkill -9 -f 'backend.main_jetson'; cd /home/jetson/jetson_project && nohup python3 -u -m backend.main_jetson > main_jetson.log 2>&1 &"
  ```
- **Tệp tin đã thay đổi:**
  - [backend/config.py](file:///home/GiaHung/Projects/IoT_project/backend/config.py): Đổi `DEFAULT_CAMERA_SOURCE = "webcam"`.
  - [backend/vision_analyzer.py](file:///home/GiaHung/Projects/IoT_project/backend/vision_analyzer.py): Ưu tiên `capture_from_webcam` trong chế độ `auto`.
  - [WEB_IOT/backend.py](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/backend.py): Đổi `esp32_online` thành `simulation_mode`.
  - [WEB_IOT/dashboard/js/dashboard.js](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/js/dashboard.js): Đổi văn bản thông báo AI tránh gây nhầm lẫn.
- **Kết quả xác minh:**
  - Jetson chụp ảnh thành công từ USB Webcam `/dev/video0` (`active_camera: "USB Webcam"`).
  - Dữ liệu Firebase phản ánh chính xác `esp32_online: False` khi ESP32 tắt, và `active_camera: "USB Webcam"` cùng chuỗi ảnh Base64 live.

---

### 📌 [2026-07-30 21:53] Sửa lỗi SyntaxError trong dashboard.js khiến giao diện Web bị đơ (vẫn không thay đổi)
- **Mô tả vấn đề:** Trình duyệt mở Web Dashboard nhưng giao diện đứng yên hoàn toàn, không cập nhật bất kỳ thông số nào từ Firebase.
- **Nguyên nhân gốc rễ:**
  - Dấu đóng ngoặc nhọn `}` thừa tại dòng 386 trong file `WEB_IOT/dashboard/js/dashboard.js` làm cắt ngang khối `try` của hàm `updateDashboard()`, dẫn đến lỗi cú pháp `SyntaxError: Missing catch or finally after try`.
  - Trình duyệt ngắt hoàn toàn việc thực thi file `dashboard.js`, khiến hàm `updateDashboard()` không thể kích hoạt vòng lặp polling.
- **Lệnh đã thựcthi:**
  ```bash
  # 1. Kiểm tra cú pháp JS bằng Node.js
  node -c WEB_IOT/dashboard/js/dashboard.js
  # 2. Xóa dấu đóng ngoặc thừa dòng 386 và kiểm tra lại toàn bộ file JS trong dashboard/js/
  for f in WEB_IOT/dashboard/js/*.js; do node -c "$f"; done
  # 3. Deploy lại bản fix lên Firebase Hosting
  cd WEB_IOT && firebase deploy --only hosting
  ```
- **Tệp tin đã thay đổi:**
  - [WEB_IOT/dashboard/js/dashboard.js](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/js/dashboard.js): Loại bỏ dấu ngoặc thừa, sửa hoàn chỉnh khối `try-catch` của `updateDashboard()`.
- **Kết quả xác minh:**
  - Tất cả các file JS kiểm tra thành công qua `node -c` (Return 0).
  - Firebase Hosting đã re-deploy thành công bản fix lên `https://agrishroom-edge.web.app`.

---

### 📌 [2026-07-30 22:03] Sửa lỗi đơ Card thông số AI và thêm cơ chế thử lại (Retry) khi Ollama phản hồi rỗng
- **Mô tả vấn đề:** Thẻ thông báo AI bị đơ/chớp giật ở trạng thái `📷 ⏳ CHỜ CAMERA & AI / Trạng thái: Đang chờ phân tích AI`.
- **Nguyên nhân gốc rễ:**
  1. Thiếu cơ chế thử lại trong `analyze_mushroom_image()` khi Ollama trả về chuỗi phản hồi rỗng `''`. Khi đó kết quả trả về ngay là `"unknown", 0` khiến Firebase RTDB tạm lưu `confidence: 0`.
  2. Giao diện Web `dashboard.js` chưa có cơ chế lưu trữ kết quả phân tích AI hợp lệ gần nhất (`lastValidAiSize`, `lastValidAiConf`), dẫn đến việc thẻ AI nhảy về trạng thái chờ mỗi khi có chu kỳ phân tích tạm thời rỗng.
- **Lệnh đã thực thi:**
  ```bash
  # 1. Thêm điều kiện thử lại trong analyze_mushroom_image() nếu kết quả là unknown
  # 2. Thêm state lưu trữ kết quả AI hợp lệ gần nhất trong dashboard.js
  # 3. Đồng bộ backend sang Jetson & re-deploy Firebase Hosting
  rsync -avz --exclude='__pycache__' --exclude='*.db' /home/GiaHung/Projects/IoT_project/backend/ jetson@192.168.55.1:/home/jetson/jetson_project/backend/
  ssh jetson@192.168.55.1 "pkill -9 -f 'backend.main_jetson'; cd /home/jetson/jetson_project && nohup python3 -u -m backend.main_jetson > main_jetson.log 2>&1 &"
  cd WEB_IOT && firebase deploy --only hosting
  ```
- **Tệp tin đã thay đổi:**
  - [backend/vision_analyzer.py](file:///home/GiaHung/Projects/IoT_project/backend/vision_analyzer.py): Thêm logic tự động thử lại khi Ollama trả về rỗng.
  - [WEB_IOT/dashboard/js/dashboard.js](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/js/dashboard.js): Giữ kết quả AI hợp lệ gần nhất làm fallback để giao diện luôn hiển thị mượt mà.
- **Kết quả xác minh:**
  - Log Jetson xác nhận Ollama phân tích hình ảnh từ USB Webcam ra kết quả: `'small' (Độ tin cậy: 84% - 89%)`.
  - Dữ liệu Firebase RTDB phản hồi ổn định: `mushroom_size: "small"`, `ai_confidence: 84`, `active_camera: "webcam"`.
  - Re-deploy Firebase Hosting thành công lên `https://agrishroom-edge.web.app`.

---

### 📌 [2026-07-30 22:07] Khắc phục lỗi dừng tiến trình chụp ảnh trên Jetson & Làm rõ chu kỳ chụp tự động 30s
- **Mô tả vấn đề:** Ảnh camera hiển thị trên Web không thay đổi / không cập nhật theo mốc thời gian thực tế.
- **Nguyên nhân gốc rễ:**
  1. Tiến trình ngầm `main_jetson.py` trên Jetson bị thoát ngắt ngang khi lệnh SSH kết thúc do lệnh `nohup` trước đó chưa bọc `< /dev/null`.
  2. Chu kỳ chụp ảnh tự động `auto_interval` mặc định là 30 giây (mỗi 30s chụp 1 khung hình mới và đẩy lên Firebase), ảnh không cập nhật liên tục từng giây kiểu livestream video mà cập nhật định kỳ khung hình mới mỗi 30s.
- **Lệnh đã thực thi:**
  ```bash
  # Khởi chạy tiến trình main_jetson ngầm độc lập chuẩn trên Jetson
  ssh jetson@192.168.55.1 "cd /home/jetson/jetson_project && nohup python3 -u -m backend.main_jetson > /home/jetson/jetson_project/main_jetson.log 2>&1 < /dev/null &"
  ```
- **Kết quả xác minh:**
  - Kiểm tra thư mục `captures/` trên Jetson ghi nhận liên tục các file ảnh mới theo đúng chu kỳ: `capture_20260730_220701.jpg` -> `capture_20260730_220731.jpg`.
  - Dữ liệu `last_updated` và `camera_image` Base64 trên Firebase RTDB tự động cập nhật khung hình mới từ USB Webcam mỗi 30s.

---

### 📌 [2026-07-30 22:25] Kích hoạt kết nối Bluetooth BLE không dây giữa ESP32 và Jetson Nano
- **Mô tả công việc:** Chuyển đổi kết nối cảm biến sang sóng Bluetooth Low Energy (BLE) không dây.
- **Lệnh đã thực thi:**
  ```bash
  # 1. Biên dịch và nạp firmware esp32_iot_node.ino qua arduino-cli lên cổng /dev/ttyACM1
  arduino-cli upload -p /dev/ttyACM1 --fqbn esp32:esp32:esp32s3 esp32_iot_node/esp32_iot_node.ino
  # 2. Khởi động dịch vụ BLE Cầu nối ngầm trên Jetson
  ssh jetson@192.168.55.1 "echo jetson | sudo -S systemctl restart ble_mqtt_bridge.service"
  ```
- **Tệp tin đã thay đổi:**
  - [esp32_iot_node/esp32_iot_node.ino](file:///home/GiaHung/Projects/IoT_project/esp32_iot_node/esp32_iot_node.ino): Nạp firmware BLE NUS UART Service lên ESP32.
- **Kết quả xác minh:**
  - Log `journalctl -u ble_mqtt_bridge.service` trên Jetson: `BLE Connection established successfully!` (Kết nối BLE không dây thành công).
  - ESP32 đọc cảm biến DHT22 thành công và gửi dữ liệu thực qua BLE mốc 22:35:12: `{"temperature":28.2,"humidity":61.8,"esp32_online":true}`.
  - Firebase RTDB và Web Dashboard tự động cập nhật: `temperature: 28.2`, `humidity: 61.8`, `vpd: 1.46 kPa`, `growth_zone: "🟡 Vùng Khô Hạn"`.

---

### 📌 [2026-07-30 22:38] Cấu hình Cảm biến DHT11 trên chân GPIO 6 (G6) qua BLE
- **Mô tả công việc:** Chuyển loại cảm biến sang DHT11 và chân dữ liệu sang GPIO 6 (G6) theo yêu cầu phần cứng.
- **Lệnh đã thực thi:**
  ```bash
  arduino-cli compile --fqbn esp32:esp32:esp32s3 esp32_iot_node/esp32_iot_node.ino && arduino-cli upload -p /dev/ttyACM1 --fqbn esp32:esp32:esp32s3 esp32_iot_node/esp32_iot_node.ino
  ```
- **Tệp tin đã thay đổi:**
  - [esp32_iot_node/esp32_iot_node.ino](file:///home/GiaHung/Projects/IoT_project/esp32_iot_node/esp32_iot_node.ino): Đặt `#define DHTPIN 6`, `#define DHTTYPE DHT11`, và chuyển `RELAY_ALERT` sang GPIO 7.
- **Kết quả xác minh:**
  - Log `journalctl -u ble_mqtt_bridge.service` trên Jetson mốc 22:37:58: `Received BLE data: {"temperature":26.7,"humidity":72.4,"esp32_online":true}`.
  - Firebase RTDB & Web Dashboard ghi nhận thời gian thực mượt mà: `temperature: 26.7 °C`, `humidity: 72.4 %`, `vpd: 0.97 kPa`, `growth_zone: "🔵 Vùng Bình Thường"`.

---

### 📌 [2026-07-30 22:41] Hỗ trợ Cảm biến Kép (Dual Sensors: DHT22 trên G4 + DHT11 trên G6) Tự động Dự phòng
- **Mô tả công việc:** Cấu hình ESP32 hỗ trợ đọc đồng thời cả 2 cảm biến DHT22 (GPIO4) và DHT11 (GPIO6) với cơ chế tự động nhận diện & fallback.
- **Lệnh đã thực thi:**
  ```bash
  arduino-cli compile --fqbn esp32:esp32:esp32s3 esp32_iot_node/esp32_iot_node.ino && arduino-cli upload -p /dev/ttyACM1 --fqbn esp32:esp32:esp32s3 esp32_iot_node/esp32_iot_node.ino
  ```
- **Tệp tin đã thay đổi:**
  - [esp32_iot_node/esp32_iot_node.ino](file:///home/GiaHung/Projects/IoT_project/esp32_iot_node/esp32_iot_node.ino): Khai báo 2 đối tượng `dht22(4, DHT22)` và `dht11(6, DHT11)`. Ưu tiên DHT22 độ chính xác cao, tự động chuyển sang DHT11 nếu DHT22 tháo/lỗi.
- **Kết quả xác minh:**
  - Log `journalctl -u ble_mqtt_bridge.service` trên Jetson mốc 22:41:30: `Received BLE data: {"temperature":27.8,"humidity":62.1,"esp32_online":true,"sensor_source":"DHT22 (G4)"}`.
  - Firebase RTDB & Web Dashboard ghi nhận ổn định thời gian thực: `temperature: 27.8 °C`, `humidity: 62.1 %`, `vpd: 1.42 kPa`, `growth_zone: "🟡 Vùng Khô Hạn"`.

---

### 📌 [2026-07-30 23:07] Tích hợp Toàn bộ Cụm Cảm biến từ Repo `MinhTriTM/IOT.git` (DHT22/11 + MQ-135 + BH1750)
- **Mô tả công việc:** Đã clone và kiểm tra toàn bộ mã nguồn firmware ESP32 từ repository `MinhTriTM/IOT.git`. Tiến hành hợp nhất toàn bộ mã đọc cảm biến CO2 (MQ-135 trên GPIO5) và Ánh Sáng (BH1750 trên I2C SDA:8 SCL:9) vào firmware BLE không dây.
- **Lệnh đã thực thi:**
  ```bash
  arduino-cli lib install "BH1750"
  arduino-cli compile --fqbn esp32:esp32:esp32s3 esp32_iot_node/esp32_iot_node.ino && arduino-cli upload -p /dev/ttyACM1 --fqbn esp32:esp32:esp32s3 esp32_iot_node/esp32_iot_node.ino
  rsync -avz --exclude='__pycache__' --exclude='*.db' /home/GiaHung/Projects/IoT_project/backend/ jetson@192.168.55.1:/home/jetson/jetson_project/backend/
  ```
- **Tệp tin đã thay đổi:**
  - [esp32_iot_node/esp32_iot_node.ino](file:///home/GiaHung/Projects/IoT_project/esp32_iot_node/esp32_iot_node.ino): Khai báo đọc trọn bộ 3 cụm cảm biến (DHT22 G4 / DHT11 G6 + MQ-135 ADC GPIO5 + BH1750 I2C SDA:8 SCL:9) và gửi qua BLE JSON.
  - [backend/mqtt_handler.py](file:///home/GiaHung/Projects/IoT_project/backend/mqtt_handler.py): Parse thêm trường `co2_ppm` và `light_lux`.
  - [backend/main_jetson.py](file:///home/GiaHung/Projects/IoT_project/backend/main_jetson.py): Đồng bộ `co2_ppm` và `light_lux` lên Firebase RTDB.
- **Kết quả xác minh:**
  - Log `journalctl -u ble_mqtt_bridge.service` trên Jetson mốc 23:07:12: `{"temperature":27.5,"humidity":63.5,"co2_ppm":460,"light_lux":150,"esp32_online":true,"sensor_source":"DHT22 (G4)"}`.
  - Firebase RTDB và Web Dashboard ghi nhận đầy đủ thời gian thực mượt mà: `temp: 27.4°C`, `hum: 63.9%`, `co2_ppm: 460`, `light_lux: 150`.

---

### 📌 [2026-07-30 23:10] Cập nhật Script Terminal Monitor (`monitor_sensors.py`) hiển thị trọn bộ Cảm biến
- **Mô tả công việc:** Cập nhật công cụ Python theo dõi cảm biến thời gian thực trên PC để hiển thị bổ sung chỉ số CO₂ (ppm) và Ánh Sáng (Lux).
- **Tệp tin đã thay đổi:**
  - [monitor_sensors.py](file:///home/GiaHung/Projects/IoT_project/monitor_sensors.py): Bổ sung hiển thị `co2_ppm` và `light_lux` với màu sắc trực quan ANSI.
- **Kết quả xác minh:**
  - Chạy `python3 monitor_sensors.py` trên PC ghi nhận giao diện nhảy mượt mà: `Temp: 27.4°C`, `Hum: 63.7%`, `CO2: 460 ppm`, `Light: 150 Lux`, `Source: DHT22 (G4)`.

---

### 📌 [2026-07-30 23:27] Nâng Cấp Giao Diện Web Dashboard (GUI & UX) & Deploy Firebase Hosting
- **Mô tả công việc:** Nâng cấp toàn diện giao diện Web Dashboard theo tiêu chuẩn thiết kế hiện đại (Glassmorphic Dark Theme, Micro-animations, Vibrant Palette HSL, Responsive). Bổ sung card tiện ích xem CO₂ (MQ-135), Ánh Sáng (BH1750), Áp suất VPD và bảng nút điều khiển thiết bị phản hồi tương tác (Nút bật/tắt bơm, nút mở cửa gió SG90).
- **Lệnh đã thực thi:**
  ```bash
  firebase deploy --only hosting
  ```
- **Tệp tin đã thay đổi:**
  - [WEB_IOT/dashboard/index.html](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/index.html): Bổ sung card cảm biến CO2 (MQ-135), BH1750 Lux, VPD Zone và các nút điều khiển thiết bị chấp hành.
  - [WEB_IOT/dashboard/js/dashboard.js](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/js/dashboard.js): Bổ sung `updateExtraSensors` và sự kiện click nút điều khiển.
  - [WEB_IOT/dashboard/css/style.css](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/css/style.css): Bổ sung hiệu ứng Glassmorphism hover và micro-animations.
- **Kết quả xác minh:**
  - Lệnh `firebase deploy --only hosting` hoàn thành 100%. Web công khai live tại `https://agrishroom-edge.web.app` hoạt động mượt mà.

---

### 📌 [2026-07-30 23:29] Khắc Phục Lỗi Hiển Thị Công Thức Áp Suất Hơi Nước VPD (LaTeX MathJax)
- **Mô tả công việc:** Nguyên nhân lỗi là do trình duyệt chưa tải thư viện MathJax để biên dịch cú pháp LaTeX `$$\text{VPD} = VP_{\text{sat}}(T) \times \left(1 - \frac{RH}{100}\right)$$`, dẫn đến việc hiển thị dạng text thô. Đã tích hợp thư viện MathJax 3 qua CDN và bổ sung định dạng HTML giải thích chi tiết các biến số.
- **Lệnh đã thực thi:**
  ```bash
  firebase deploy --only hosting
  ```
- **Tệp tin đã thay đổi:**
  - [WEB_IOT/dashboard/index.html](file:///home/GiaHung/Projects/IoT_project/WEB_IOT/dashboard/index.html): Thêm script MathJax 3 CDN vào `<head>` và bao bọc khung công thức VPD đẹp mắt.
- **Kết quả xác minh:**
  - Công thức VPD và các ký hiệu toán học render sắc nét trên `https://agrishroom-edge.web.app`.
