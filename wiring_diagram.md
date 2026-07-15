# 🔌 Sơ Đồ Nối Dây Chi Tiết ESP32 (Wiring Diagram)

Mô tả đấu nối phần cứng trên sa bàn cho mạch vi điều khiển ESP32, cảm biến DHT11, module Relay 2 kênh, đèn LED mô phỏng và còi cảnh báo.

---

## 📊 1. Bảng Đấu Nối Chân (Pinout Table)

| Linh Kiện | Chân Linh Kiện | Chân ESP32 | Loại Tín Hiệu | Mô Tả |
| :--- | :--- | :--- | :--- | :--- |
| **Cảm biến DHT11** | VCC | 3.3V | Nguồn | Cấp nguồn 3.3V cho cảm biến |
| | GND | GND | Nguồn | Cực âm chung |
| | DATA | GPIO 4 | Digital Input | Truyền dữ liệu nhiệt độ & độ ẩm |
| **Module Relay 2CH**| VCC | VIN (5V) | Nguồn | Cấp nguồn 5V nuôi cuộn hút relay |
| | GND | GND | Nguồn | Cực âm chung |
| | IN1 | GPIO 26 | Digital Output | Điều khiển kênh 1 (Bơm sương - LED Xanh) |
| | IN2 | GPIO 27 | Digital Output | Điều khiển kênh 2 (Cảnh báo - LED Đỏ + Còi) |
| **Kênh 1 (Relay CH1)**| COM1 | VIN (5V) | Nguồn | Cấp nguồn chung cho thiết bị chấp hành |
| | NO1 | Anode (LED Xanh) | Đầu ra | Nối với cực dương LED Xanh qua điện trở 220Ω |
| **Kênh 2 (Relay CH2)**| COM2 | VIN (5V) | Nguồn | Cấp nguồn chung cho thiết bị chấp hành |
| | NO2 | Anode (LED Đỏ) & VCC (Còi) | Đầu ra | Cực dương LED Đỏ (qua trở 220Ω) & Còi mắc song song |

*Chú ý:* 
- **Cực âm (Cathode/GND) của cả 2 đèn LED và Còi** phải nối chung trực tiếp về chân **GND** của ESP32.
- Chọn module Relay loại **có cách ly quang (opto-isolated)** để bảo vệ các chân GPIO của ESP32 tránh dòng ngược từ cuộn hút của Relay.

---

## 🎨 2. Sơ Đồ Khối Kết Nối (ASCII Schematic)

```text
               +-----------------------------------+
               |               ESP32               |
               |                                   |
               |   3.3V   GND   GPIO4   VIN   GND  |
               +----+------+-----+------+------+---+
                    |      |     |      |      |
  +--------------+  |      |     |      |      |
  | Cảm Biến     |  |      |     |      |      |
  | DHT11 (3-Pin)|--+      |     |      |      |
  |   VCC   (1)  +---------+     |      |      |
  |   GND   (2)  +---------------+      |      |
  |   DATA  (3)  +----------------------+      |
  +--------------+                             |
                                               |
  +--------------------------------+           |
  | Module Relay 2 Kênh            |           |
  |                                |           |
  |   VCC   GND   IN1   IN2        |           |
  +----+-----+-----+-----+---------+           |
       |     |     |     |                     |
       |     +-----+-----+---------------------+ (GND chung)
       +---------------------------------------+ (VIN 5V cấp cho Relay)
                   |     |
      +------------+     +-----------+
      | (IN1 - GPIO26)   | (IN2 - GPIO27)
      v                  v
+-----------+      +-----------+
| Relay CH1 |      | Relay CH2 |
|   (Bơm)   |      | (Cảnh Báo)|
+--+-----+--+      +--+-----+--+
   |     |            |     |
   |     |            |     +---------+
   |     |            |               |
   |     |            v               v
   |     |      +-----------+   +-----------+
   |     |      |  LED Đỏ   |   |   Còi     |
   |     |      | (Trở 220Ω)|   |   (5V)    |
   |     |      +-----+-----+   +-----+-----+
   |     |            |               |
   |     |            +-------+-------+
   |     |                    |
   |     +--------------------+----------------+ (Nối về GND ESP32)
   |                          |
   v                          v
+-----------+          +---------------+
| LED Xanh  |          | Cực âm chung  |
| (Trở 220Ω)|          | của Tải       |
+-----+-----+          +---------------+
      |                       ^
      +-----------------------+
```
