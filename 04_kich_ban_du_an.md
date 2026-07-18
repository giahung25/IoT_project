# 🎬 Kịch Bản Demo — Hệ Thống Edge AI & IoT Giám Sát Sinh Trưởng Nấm

> **Ngày lập:** 11/07/2026
> **Thời lượng demo:** 8–12 phút
> **Mục đích:** Trình diễn đầy đủ các chức năng của hệ thống trước hội đồng / khán giả

---

## Tổng Quan Kịch Bản

Buổi demo mô phỏng **một ngày vận hành** của trang trại nấm thông minh, được chia thành **5 cảnh** (scene). Mỗi cảnh thể hiện một trạng thái khác nhau của hệ thống, từ khởi động → giám sát bình thường → xử lý sự cố → AI phân tích → cảnh báo thu hoạch.

```mermaid
graph LR
    S1["🎬 Cảnh 1<br/>Khởi động"] --> S2["📊 Cảnh 2<br/>Giám sát"]
    S2 --> S3["💧 Cảnh 3<br/>Tự động bơm"]
    S3 --> S4["🧠 Cảnh 4<br/>AI phân tích"]
    S4 --> S5["🔔 Cảnh 5<br/>Thu hoạch"]

    style S1 fill:#4CAF50,color:#fff
    style S2 fill:#2196F3,color:#fff
    style S3 fill:#FF9800,color:#fff
    style S4 fill:#9C27B0,color:#fff
    style S5 fill:#F44336,color:#fff
```

---

## Chuẩn Bị Trước Demo

### Checklist Thiết Bị

- [ ] Jetson Orin Nano đã bật, đăng nhập xong
- [ ] MQTT Broker (Mosquitto) đang chạy
- [ ] Ollama đã start và load model Vision LLM
- [ ] ESP32 đã cắm nguồn, đèn Power sáng
- [ ] Webcam USB cắm vào Jetson, hướng xuống luống nấm mô phỏng
- [ ] Breadboard đã đấu nối đầy đủ: DHT11, Relay, LED xanh, LED đỏ, Còi
- [ ] Dashboard Web mở sẵn trên trình duyệt PC (Flask server đã chạy trên PC tại `http://<pc-ip>:5000`)
- [ ] Chuẩn bị 2 mẫu nấm mô phỏng: 1 mẫu **nhỏ** và 1 mẫu **lớn**

### Chuẩn Bị Phần Mềm

```bash
# Trên Jetson, mở 2 terminal:

# Terminal 1: Start MQTT Broker
sudo systemctl start mosquitto

# Terminal 2: Start Backend (thu thập + AI + gửi data tới PC)
cd ~/jetson_project/backend
python main_jetson.py

# Trên PC, mở 1 terminal:

# Start Web Dashboard
cd ~/WEB_IOT
python backend.py
```

### Chuẩn Bị Mẫu Nấm

- **Mẫu A (Nấm nhỏ):** Nấm còn non, kích thước nhỏ → dùng cho Cảnh 2, 3
- **Mẫu B (Nấm lớn):** Nấm trưởng thành, tán rộng → dùng cho Cảnh 4, 5
- *(Có thể dùng nấm thật hoặc mô hình nấm bằng nhựa/giấy)*

---

## Cảnh 1: Khởi Động Hệ Thống 🎬

> **Thời lượng:** 2 phút
> **Mục đích:** Giới thiệu tổng quan và khởi động hệ thống

### Lời Dẫn

> *"Kính chào quý thầy cô và các bạn. Hôm nay, nhóm chúng em xin trình bày dự án **Hệ thống Edge AI & IoT Giám sát Sinh trưởng Nấm**. Đây là một sa bàn thu nhỏ mô phỏng giải pháp nông nghiệp thông minh, kết hợp giữa IoT và trí tuệ nhân tạo tại biên."*

### Hành Động

| Bước | Người Demo | Hành Động                                                   | Kết Quả Mong Đợi                   |
| ------ | ------------ | -------------------------------------------------------------- | -------------------------------------- |
| 1.1    | Diễn giả   | Chỉ vào sa bàn, giới thiệu từng thành phần phần cứng | Khán giả nắm được layout         |
| 1.2    | Diễn giả   | Chỉ vào sơ đồ kiến trúc (trên slide/poster)            | Hiểu luồng dữ liệu 4 lớp          |
| 1.3    | Kỹ thuật   | Bật nguồn ESP32 (cắm USB)                                   | LED Power trên ESP32 sáng            |
| 1.4    | Kỹ thuật   | Chạy backend trên Jetson                                     | Terminal hiện "System started..."     |
| 1.5    | Diễn giả   | Mở Dashboard trên trình duyệt                              | Trang web hiển thị giao diện chính |

### Kết Quả Trên Dashboard

- ✅ Trạng thái kết nối: **Online**
- ✅ Nhiệt độ: Hiển thị giá trị (ví dụ: 28°C)
- ✅ Độ ẩm: Hiển thị giá trị (ví dụ: 75%)
- ✅ Trạng thái bơm: **OFF**
- ✅ Trạng thái thu hoạch: **OFF**
- ✅ Ảnh camera: Hiển thị ảnh luống nấm (mẫu A — nấm nhỏ)

### Lời Dẫn Chuyển Cảnh

> *"Như các bạn thấy, hệ thống đã khởi động thành công. Dashboard hiển thị đầy đủ dữ liệu cảm biến real-time. Hiện tại, nhiệt độ là 28 độ C, độ ẩm 75% — môi trường hoàn toàn bình thường cho nấm phát triển. Bây giờ, chúng ta sẽ theo dõi hệ thống hoạt động trong điều kiện bình thường."*

---

## Cảnh 2: Giám Sát Bình Thường 📊

> **Thời lượng:** 1.5 phút
> **Mục đích:** Thể hiện khả năng giám sát liên tục và hiển thị real-time

### Lời Dẫn

> *"Trong chế độ giám sát bình thường, ESP32 liên tục đọc dữ liệu từ cảm biến DHT11 mỗi 5 giây và gửi về Jetson qua giao thức MQTT. Đồng thời, camera chụp ảnh luống nấm mỗi 30 giây để AI phân tích."*

### Hành Động

| Bước | Hành Động                           | Kết Quả Mong Đợi                            |
| ------ | -------------------------------------- | ----------------------------------------------- |
| 2.1    | Để hệ thống tự chạy 30–60 giây | Dữ liệu cập nhật liên tục trên Dashboard |
| 2.2    | Chỉ vào biểu đồ lịch sử         | Đường line chart vẽ thêm các điểm mới  |
| 2.3    | Chỉ vào bảng log                    | Các dòng log mới xuất hiện                 |
| 2.4    | Chỉ vào ảnh camera                  | Ảnh nấm nhỏ (mẫu A) được cập nhật      |

### Trạng Thái Hệ Thống

| Thông Số             | Giá Trị | Nhận Định             |
| ---------------------- | --------- | ------------------------ |
| Nhiệt độ            | ~28°C    | ✅ Bình thường        |
| Độ ẩm               | ~75%      | ✅ Đủ ẩm (≥ 70%)     |
| AI: Kích thước nấm | `small` | ✅ Chưa cần thu hoạch |
| Bơm sương           | OFF       | ✅ Không cần bơm      |
| Cảnh báo thu hoạch  | OFF       | ✅ Chưa cần cảnh báo |

### Lời Dẫn Chuyển Cảnh

> *"Mọi thứ đang trong trạng thái ổn định. Nhưng điều gì xảy ra khi môi trường thay đổi? Chúng ta sẽ mô phỏng tình huống **độ ẩm giảm thấp** — một vấn đề thường gặp trong trồng nấm."*

---

## Cảnh 3: Tự Động Bật Bơm Sương 💧

> **Thời lượng:** 2.5 phút
> **Mục đích:** Thể hiện khả năng phản ứng tự động với thay đổi môi trường
> **Điểm nhấn:** Đây là kịch bản quan trọng nhất — thể hiện vòng khép kín IoT

### Lời Dẫn

> *"Bây giờ, chúng ta sẽ mô phỏng tình huống **độ ẩm giảm xuống dưới ngưỡng 70%**. Trong thực tế, điều này xảy ra khi thời tiết khô hanh hoặc hệ thống thông gió quá mạnh."*

### Hành Động — Kích Hoạt Sự Kiện

> [!IMPORTANT]
> **Cách mô phỏng độ ẩm thấp:** Có 2 phương án:
>
> - **Phương án A (Tự nhiên):** Dùng máy sấy tóc thổi nhẹ vào cảm biến DHT11 → nhiệt tăng, ẩm giảm
> - **Phương án B (Phần mềm):** Dùng `mosquitto_pub` gửi dữ liệu giả lập trực tiếp:
>   ```bash
>   mosquitto_pub -t "sensor/data" -m '{"temperature": 30, "humidity": 55, "timestamp": "2026-07-15T10:35:00"}'
>   ```

| Bước | Hành Động                                   | Kết Quả Mong Đợi                          |
| ------ | ---------------------------------------------- | --------------------------------------------- |
| 3.1    | Kích hoạt sự kiện ẩm thấp (PA A hoặc B) | Dashboard hiển thị humidity < 70%           |
| 3.2    | Chờ 5–10 giây                               | Decision Engine phát hiện ngưỡng          |
| 3.3    | Quan sát Dashboard                            | Trạng thái bơm chuyển:**OFF → ON** |
| 3.4    | Quan sát sa bàn                              | **LED Xanh sáng** 🟢                   |
| 3.5    | Chỉ vào bảng log                            | Log ghi: "Humidity low (55%), pump activated" |

### Trạng Thái Hệ Thống

| Thông Số            | Trước | Sau           | Thay Đổi           |
| --------------------- | ------- | ------------- | -------------------- |
| Độ ẩm              | 75%     | **55%** | ⚠️ Dưới ngưỡng |
| Bơm sương          | OFF     | **ON**  | 🟢 LED Xanh sáng    |
| Cảnh báo thu hoạch | OFF     | OFF           | Không đổi         |

### Lời Dẫn

> *"Như các bạn thấy, ngay khi độ ẩm giảm xuống 55% — dưới ngưỡng an toàn 70% — hệ thống đã tự động bật bơm sương. Trên sa bàn, LED xanh sáng lên mô phỏng máy bơm hoạt động. Trên Dashboard, trạng thái cũng được cập nhật real-time. Toàn bộ quá trình diễn ra tự động, không cần can thiệp của con người."*

### Khôi Phục

> *"Khi độ ẩm trở lại bình thường..."*

| Bước | Hành Động                           | Kết Quả                                   |
| ------ | -------------------------------------- | ------------------------------------------- |
| 3.6    | Gỡ máy sấy / Gửi dữ liệu ẩm cao | Humidity > 70%                              |
| 3.7    | Chờ chu kỳ tiếp theo                | Bơm tự động**OFF**, LED xanh tắt |

---

## Cảnh 4: AI Phân Tích Hình Ảnh Nấm 🧠

> **Thời lượng:** 3 phút
> **Mục đích:** Thể hiện khả năng Edge AI — chạy Vision LLM tại biên
> **Điểm nhấn:** Đây là điểm khác biệt cốt lõi so với IoT thông thường

### Lời Dẫn

> *"Ngoài việc giám sát môi trường, hệ thống còn có khả năng **phân tích hình ảnh bằng AI**. Mô hình Vision LLM chạy trực tiếp trên Jetson Orin Nano — hoàn toàn offline, không cần kết nối internet hay dịch vụ đám mây. Đây chính là ý nghĩa của 'Edge AI' — trí tuệ nhân tạo tại biên."*

### Hành Động — Demo AI với Nấm Nhỏ

| Bước | Hành Động                                     | Kết Quả Mong Đợi                                      |
| ------ | ------------------------------------------------ | --------------------------------------------------------- |
| 4.1    | Đặt**Mẫu A (nấm nhỏ)** trước camera | Camera chụp ảnh nấm nhỏ                               |
| 4.2    | Chờ chu kỳ phân tích (≤ 30 giây)           | Backend gửi ảnh tới Ollama                             |
| 4.3    | Quan sát terminal Jetson                        | Log: "AI analysis: size = small"                          |
| 4.4    | Quan sát Dashboard                              | AI Status:**"small"**, Harvest Alert: **OFF** |

### Lời Dẫn

> *"AI đã phân tích ảnh và nhận định nấm đang ở giai đoạn 'nhỏ', chưa đến lúc thu hoạch. Bây giờ, chúng ta sẽ thay thế bằng mẫu nấm lớn hơn để xem hệ thống phản ứng như thế nào."*

### Hành Động — Demo AI với Nấm Lớn (Chuyển Cảnh 5)

| Bước | Hành Động                                                  | Kết Quả Mong Đợi             |
| ------ | ------------------------------------------------------------- | -------------------------------- |
| 4.5    | **Thay Mẫu A bằng Mẫu B (nấm lớn)** trước camera | Camera chụp ảnh nấm lớn      |
| 4.6    | Chờ chu kỳ phân tích                                      | Backend gửi ảnh tới Ollama    |
| 4.7    | Quan sát terminal                                            | Log: "AI analysis: size = large" |
| 4.8    | Quan sát Dashboard                                           | AI Status:**"large"**      |

### Giải Thích Kỹ Thuật (Nếu Có Thời Gian)

> *"Về mặt kỹ thuật, backend Python chụp ảnh từ Webcam bằng OpenCV, encode sang Base64, rồi gửi tới Ollama API chạy trên localhost. Model Vision LLM — ở đây là LLaVA — phân tích ảnh và trả về kết quả dạng JSON. Toàn bộ inference diễn ra trên GPU NVIDIA của Jetson, thời gian xử lý khoảng 5–10 giây."*

---

## Cảnh 5: Cảnh Báo Thu Hoạch 🔔

> **Thời lượng:** 2 phút
> **Mục đích:** Thể hiện khả năng ra quyết định và cảnh báo
> **Điểm nhấn:** Khoảnh khắc "wow" — LED đỏ sáng + Còi kêu

### Lời Dẫn

> *"Và đây... khi AI xác nhận nấm đã đủ lớn..."*

### Hành Động

| Bước | Hành Động                                     | Kết Quả Mong Đợi                                    |
| ------ | ------------------------------------------------ | ------------------------------------------------------- |
| 5.1    | *(Tiếp nối Cảnh 4)* Decision Engine xử lý | Rule R4 kích hoạt: size = large → harvest_alert = ON |
| 5.2    | Quan sát sa bàn                                | **LED Đỏ sáng** 🔴 + **Còi kêu** 🔊    |
| 5.3    | Quan sát Dashboard                              | Harvest Alert:**ON**, nền đỏ nhấp nháy       |
| 5.4    | Chỉ vào bảng log                              | Log: "Mushroom size is LARGE. Harvest alert activated!" |

### Trạng Thái Hệ Thống

| Thông Số            | Giá Trị               | Biểu Hiện Vật Lý             |
| --------------------- | ----------------------- | -------------------------------- |
| AI: Kích thước     | `large`               | —                               |
| Cảnh báo thu hoạch | **ON**            | 🔴 LED Đỏ sáng + 🔊 Còi kêu |
| Bơm sương          | OFF (hoặc ON tùy ẩm) | 🟢 LED Xanh (tùy)               |

### Lời Dẫn

> *"Hệ thống đã phát hiện nấm đạt kích thước thu hoạch và tự động kích hoạt cảnh báo. Trên sa bàn, LED đỏ sáng và còi kêu để thông báo cho người nông dân. Trên Dashboard, trạng thái cũng hiển thị rõ ràng. Toàn bộ quá trình — từ chụp ảnh, phân tích AI, ra quyết định, đến cảnh báo — diễn ra hoàn toàn tự động và offline."*

---

## Kết Thúc Demo 🏁

> **Thời lượng:** 1 phút

### Lời Dẫn Kết

> *"Tổng kết lại, hệ thống của chúng em đã thể hiện đầy đủ 4 lớp của mô hình IoT:*
>
> 1. ***Sensing** — Cảm biến DHT11 đo nhiệt độ, độ ẩm; Camera chụp ảnh nấm.*
> 2. ***Connectivity** — ESP32 giao tiếp qua Wi-Fi và giao thức MQTT.*
> 3. ***Processing** — Jetson Orin Nano chạy Vision LLM phân tích ảnh và Decision Engine ra quyết định.*
> 4. ***Actuation** — Tự động bật bơm sương khi ẩm thấp, cảnh báo khi nấm đủ lớn.*
>
> *Điểm khác biệt cốt lõi là toàn bộ xử lý AI diễn ra **tại biên (Edge)**, không phụ thuộc internet, đảm bảo tính riêng tư dữ liệu và độ trễ thấp.*
>
> *Xin cảm ơn quý thầy cô và các bạn đã lắng nghe. Nhóm em sẵn sàng trả lời câu hỏi."*

---

## Phụ Lục: Câu Hỏi Thường Gặp & Cách Trả Lời

### Q1: Tại sao chọn Vision LLM thay vì YOLO?

> **Trả lời:** YOLO yêu cầu dữ liệu huấn luyện riêng (labeled dataset) và chỉ nhận diện các class đã học. Vision LLM (như LLaVA) có khả năng zero-shot — phân tích ảnh dựa trên ngôn ngữ tự nhiên, không cần huấn luyện lại, phù hợp cho prototype nhanh. Trong hệ thống production, có thể kết hợp cả hai.

### Q2: Hệ thống có thể mở rộng không?

> **Trả lời:** Có. Kiến trúc MQTT cho phép thêm nhiều Node IoT (ESP32) ở các luống nấm khác nhau. Mỗi Node publish lên một topic riêng. Backend trên Jetson subscribe nhiều topic và xử lý tập trung.

### Q3: Tại sao không dùng cloud?

> **Trả lời:** Trong nông nghiệp, nhiều trang trại ở vùng sâu vùng xa không có internet ổn định. Edge AI đảm bảo hệ thống hoạt động 24/7 ngay cả khi offline. Ngoài ra, xử lý tại biên giảm độ trễ (latency) và bảo vệ quyền riêng tư dữ liệu.

### Q4: DHT11 có chính xác không?

> **Trả lời:** DHT11 có sai số ±2°C và ±5%RH, phù hợp cho mục đích demo. Trong hệ thống thực tế, chúng em khuyến nghị nâng cấp lên DHT22 (±0.5°C, ±2%RH) hoặc BME280.

### Q5: Thời gian inference AI có chấp nhận được không?

> **Trả lời:** Trên Jetson Orin Nano, thời gian inference khoảng 5–10 giây/ảnh. Với chu kỳ kiểm tra 30 giây, hoàn toàn đủ nhanh cho bài toán giám sát nông nghiệp. Nấm không thay đổi kích thước trong vài giây.

---

## Phụ Lục: Kịch Bản Xử Lý Sự Cố Khi Demo

| Sự Cố                      | Nguyên Nhân                             | Xử Lý Nhanh                                                |
| ---------------------------- | ----------------------------------------- | ------------------------------------------------------------ |
| Dashboard không hiển thị  | Flask trên PC chưa chạy hoặc sai IP PC | Kiểm tra `python backend.py` trên PC, dùng `http://<pc-ip>:5000` |
| ESP32 không gửi dữ liệu  | Mất kết nối Wi-Fi                      | Reset ESP32 (nhấn nút EN), kiểm tra SSID/password         |
| AI không trả kết quả     | Ollama chưa start hoặc model chưa load | Chạy`ollama serve` và `ollama run llava`               |
| LED/Còi không hoạt động | Đấu nối sai hoặc Relay hỏng          | Kiểm tra dây nối, test Relay bằng lệnh GPIO thủ công  |
| Dữ liệu cảm biến = NaN   | DHT11 lỏng chân hoặc hỏng             | Kiểm tra kết nối, thay DHT11 dự phòng                   |

> [!TIP]
> **Luôn có phương án B:** Chuẩn bị sẵn `mosquitto_pub` để gửi dữ liệu giả lập nếu phần cứng gặp sự cố trong lúc demo. Khán giả sẽ không nhận ra sự khác biệt trên Dashboard.
