# 🔌 Hướng Dẫn Kết Nối Backend → Frontend Dashboard

> Đọc file này nếu bạn là người xây dựng backend (Flask / Jetson Orin Nano).  
> Frontend đã xong — bạn chỉ cần làm đúng 3 bước dưới đây.

---

## Bước 1 — Cài CORS cho Flask

```bash
pip install flask-cors
```

```python
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # ← Bắt buộc, không có cái này browser sẽ chặn
```

---

## Bước 2 — Tạo 2 endpoint API

### `GET /api/status` — Trạng thái hiện tại

```python
@app.route('/api/status')
def get_status():
    return {
        "temperature":    27.5,        # float — °C
        "humidity":       82.0,        # float — %
        "mushroom_size":  "small",     # string — "small" hoặc "large"
        "pump":           False,       # bool — relay bơm
        "harvest_alert":  False,       # bool — True thì banner đỏ bật
        "ai_confidence":  92,          # int — % độ chính xác AI
        "esp32_online":   True,        # bool — ESP32 có kết nối không
        "last_updated":   "2026-07-17T17:00:00Z"  # ISO 8601
    }
```

### `GET /api/history` — Lịch sử (dùng để vẽ biểu đồ)

```python
@app.route('/api/history')
def get_history():
    # Trả về mảng, mỗi phần tử là 1 lần đo
    # Tối đa 48 điểm (4 giờ gần nhất, mỗi 5 phút 1 điểm)
    return [
        {
            "timestamp":   "2026-07-17T12:00:00Z",  # ISO 8601
            "temperature": 26.5,                     # float
            "humidity":    80.1                      # float
        },
        # ... thêm các bản ghi tiếp theo
    ]
```

> **Lưu ý:** Sắp xếp từ **cũ → mới** (index 0 là cũ nhất).

---

## Bước 3 — Báo IP cho người làm frontend

Sau khi Flask chạy trên Jetson, lấy IP:

```bash
hostname -I
# Ví dụ: 192.168.1.110
```

Người làm frontend sẽ sửa **1 dòng** trong `js/dashboard.js`:

```js
const API_BASE = 'http://192.168.1.110:5000'; // ← IP của bạn
const USE_MOCK = false;                         // ← đổi thành false
```

---

## Ảnh Camera (tuỳ chọn)

Nếu muốn hiển thị ảnh nấm từ Webcam lên dashboard:

```python
# Flask serve ảnh tĩnh tự động nếu đặt đúng chỗ
# Lưu ảnh mới nhất vào:
IMAGE_PATH = "dashboard/static/images/latest.jpg"
```

Frontend sẽ tự tải lại ảnh mỗi 5 giây theo URL:
```
http://<IP_JETSON>:5000/static/images/latest.jpg
```

---

## Tóm tắt nhanh

| Việc cần làm | Chi tiết |
|---|---|
| Cài flask-cors | `pip install flask-cors` |
| Tạo `/api/status` | Trả JSON trạng thái hiện tại |
| Tạo `/api/history` | Trả mảng JSON lịch sử (cũ → mới) |
| Chạy Flask | `python app.py` (port 5000) |
| Báo IP cho frontend | Chạy `hostname -I` lấy IP |

---

*Dashboard Frontend: `dashboard/index.html` — mở bằng trình duyệt sau khi kết nối đúng IP.*
