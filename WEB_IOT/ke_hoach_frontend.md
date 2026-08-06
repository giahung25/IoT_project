# 🌱 Kế Hoạch Xây Dựng Frontend Dashboard
## Dự Án: Edge AI & IoT Giám Sát Sinh Trưởng Nấm

> **Nguồn dự án:** [giahung25/IoT_project](https://github.com/giahung25/IoT_project)  
> **Phạm vi:** Chỉ Frontend (HTML + CSS + JavaScript thuần)  
> **Mục tiêu:** Dashboard hiển thị dữ liệu giám sát nấm theo thời gian thực (mock data giai đoạn này)

---

## 📋 Tổng Quan Dự Án Gốc

Hệ thống IoT giám sát sinh trưởng nấm bao gồm:

| Thành phần | Mô tả |
|---|---|
| **ESP32** | Vi điều khiển đọc cảm biến DHT11 (nhiệt độ, độ ẩm), giao tiếp MQTT |
| **ESP32-CAM** | Camera IoT (tùy chọn) |
| **Webcam USB** | Camera chính gắn vào Jetson |
| **Jetson Orin Nano** | Edge Server: MQTT Broker, Vision LLM (Ollama/moondream), Python Backend, Flask API |
| **SQLite** | Lưu lịch sử dữ liệu cảm biến và log AI |
| **Dashboard Web** | Flask + Vanilla JS (port 5000) |

### Luồng dữ liệu thực tế (khi có backend)
```
DHT11 → ESP32 → MQTT → Jetson Backend → Flask API → Dashboard
                              ↓
                    Webcam → Ollama AI → Kết quả phân tích
```

### Dữ liệu cần hiển thị trên Dashboard
- 🌡️ **Nhiệt độ** (°C) — realtime từ `GET /api/status`
- 💧 **Độ ẩm** (%) — realtime từ `GET /api/status`
- 📷 **Hình ảnh nấm mới nhất** — `static/images/latest.jpg`
- 🧠 **Kết quả AI** — kích cỡ nấm: `small` / `large`
- 💡 **Trạng thái thiết bị**: Pump (bơm), Harvest Alert (cảnh báo thu hoạch)
- 📊 **Biểu đồ lịch sử** nhiệt độ & độ ẩm — từ `GET /api/history`
- ⏱️ **Thời gian cập nhật** cuối cùng

---

## 🗂️ Cấu Trúc Thư Mục Frontend

```
dashboard/
├── index.html              # Trang chính Dashboard
├── css/
│   └── style.css           # Toàn bộ styling (dark mode, glassmorphism)
├── js/
│   ├── dashboard.js        # Logic chính: polling API, cập nhật UI
│   ├── charts.js           # Vẽ biểu đồ lịch sử (Chart.js)
│   ├── gauges.js           # Vẽ đồng hồ nhiệt độ & độ ẩm
│   └── mock-data.js        # Dữ liệu giả lập (giai đoạn frontend-only)
└── assets/
    └── mushroom-placeholder.jpg  # Ảnh placeholder nấm
```

---

## 🎨 Bước 1 — Thiết Kế Hệ Thống Giao Diện (Design System)

**File:** `dashboard/css/style.css`

### 1.1 Bảng màu & Theme (Dark Mode)
```css
:root {
  /* Primary palette — Màu xanh lá nông nghiệp */
  --color-primary:     hsl(145, 63%, 42%);
  --color-primary-glow: hsl(145, 63%, 55%);

  /* Background layers */
  --bg-base:     hsl(220, 20%, 8%);
  --bg-surface:  hsl(220, 18%, 12%);
  --bg-card:     hsl(220, 16%, 16%);
  --bg-glass:    hsla(220, 18%, 20%, 0.6);

  /* Text */
  --text-primary:   hsl(0, 0%, 95%);
  --text-secondary: hsl(220, 10%, 65%);

  /* Status colors */
  --color-warning: hsl(38, 92%, 55%);
  --color-danger:  hsl(0, 80%, 55%);
  --color-success: hsl(145, 63%, 42%);
  --color-info:    hsl(210, 80%, 60%);

  /* Typography */
  --font-main: 'Inter', 'Outfit', sans-serif;
}
```

### 1.2 Layout Chính (CSS Grid)
```
┌─────────────────────────────────────────────────────┐
│              🌱 HEADER / NAVBAR                      │
├──────────────┬──────────────┬───────────────────────┤
│  🌡️ TEMP     │  💧 HUMIDITY │    🍄 AI STATUS        │
│   Gauge      │    Gauge     │   (size + alert)       │
├──────────────┴──────────────┴───────────────────────┤
│         📊 BIỂU ĐỒ LỊCH SỬ (Chart.js Line)          │
├──────────────────────────┬──────────────────────────┤
│    📷 CAMERA FEED / IMG   │  💡 THIẾT BỊ ĐIỀU KHIỂN  │
│    (ảnh nấm mới nhất)    │  (Pump, Alert indicator) │
└──────────────────────────┴──────────────────────────┘
```

### 1.3 Components Cần Thiết kế
| Component | Mô tả |
|---|---|
| `GaugeCard` | Đồng hồ đo dạng vòng tròn (SVG arc) cho nhiệt độ & độ ẩm |
| `StatusCard` | Card hiển thị kết quả AI (small/large) với badge màu |
| `DeviceStatus` | Indicator on/off cho Pump và Harvest Alert |
| `HistoryChart` | Biểu đồ đường nhiệt độ & độ ẩm theo thời gian |
| `CameraFeed` | Khung hiển thị ảnh nấm + overlay AI |
| `AlertBanner` | Banner nhấp nháy đỏ khi `harvest_alert == true` |
| `LastUpdated` | Timestamp cập nhật gần nhất |

---

## 🏗️ Bước 2 — Xây Dựng HTML Skeleton

**File:** `dashboard/index.html`

### 2.1 Cấu trúc HTML5 Semantic
```html
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>🌱 IoT Dashboard — Giám Sát Nấm</title>
  <meta name="description" content="Dashboard giám sát sinh trưởng nấm theo thời gian thực" />
  <!-- Google Fonts: Inter + Outfit -->
  <!-- Chart.js CDN -->
  <link rel="stylesheet" href="css/style.css" />
</head>
<body class="harvest-normal">  <!-- Class đổi thành harvest-alert khi cảnh báo -->

  <!-- HEADER -->
  <header id="main-header">...</header>

  <!-- ALERT BANNER (ẩn mặc định) -->
  <div id="alert-banner" class="hidden">⚠️ THU HOẠCH NGAY!</div>

  <!-- MAIN DASHBOARD GRID -->
  <main id="dashboard-grid">

    <!-- Hàng 1: Gauges + AI Status -->
    <section id="gauges-row">
      <div id="temp-gauge-card" class="card gauge-card">...</div>
      <div id="humidity-gauge-card" class="card gauge-card">...</div>
      <div id="ai-status-card" class="card">...</div>
    </section>

    <!-- Hàng 2: Biểu đồ lịch sử -->
    <section id="chart-row">
      <div id="history-chart-card" class="card">
        <canvas id="history-chart"></canvas>
      </div>
    </section>

    <!-- Hàng 3: Camera + Devices -->
    <section id="bottom-row">
      <div id="camera-card" class="card">...</div>
      <div id="devices-card" class="card">...</div>
    </section>

  </main>

  <script src="js/mock-data.js"></script>
  <script src="js/gauges.js"></script>
  <script src="js/charts.js"></script>
  <script src="js/dashboard.js"></script>
</body>
</html>
```

---

## ⚙️ Bước 3 — Viết JavaScript Logic

### 3.1 Mock Data (`js/mock-data.js`)
Trong giai đoạn chưa có backend, tạo dữ liệu giả để test UI:
```javascript
const MOCK_STATUS = {
  temperature: 27.5,
  humidity: 82.0,
  mushroom_size: "small",    // hoặc "large"
  pump: false,
  harvest_alert: false,
  last_updated: new Date().toISOString(),
  camera_image: "assets/mushroom-placeholder.jpg"
};

// Mock history (24 điểm dữ liệu của 2 giờ qua)
const MOCK_HISTORY = Array.from({ length: 24 }, (_, i) => ({
  timestamp: new Date(Date.now() - (23 - i) * 5 * 60 * 1000).toISOString(),
  temperature: 25 + Math.random() * 5,
  humidity: 75 + Math.random() * 15
}));
```

### 3.2 API Service (`js/dashboard.js`)
```javascript
// Cấu hình
const API_BASE = "http://localhost:5000"; // Đổi thành IP Jetson khi deploy
const POLL_INTERVAL = 5000; // 5 giây

// Hàm fetch status (dùng mock khi chưa có backend)
async function fetchStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/status`);
    return await res.json();
  } catch {
    return MOCK_STATUS; // Fallback mock data
  }
}

// Hàm fetch history
async function fetchHistory() {
  try {
    const res = await fetch(`${API_BASE}/api/history`);
    return await res.json();
  } catch {
    return MOCK_HISTORY;
  }
}

// Vòng lặp cập nhật UI
async function updateDashboard() {
  const status = await fetchStatus();
  updateGauges(status.temperature, status.humidity);
  updateAIStatus(status.mushroom_size);
  updateDevices(status.pump, status.harvest_alert);
  updateCamera(status.camera_image);
  updateTimestamp(status.last_updated);
  toggleHarvestAlert(status.harvest_alert);
}

// Polling mỗi 5 giây
updateDashboard();
setInterval(updateDashboard, POLL_INTERVAL);
```

### 3.3 SVG Gauge (`js/gauges.js`)
- Vẽ vòng cung SVG cho nhiệt độ (0–50°C) và độ ẩm (0–100%)
- Animate kim chỉ khi giá trị thay đổi
- Đổi màu vòng cung: Xanh (bình thường) → Vàng (cảnh báo) → Đỏ (nguy hiểm)

### 3.4 Chart.js (`js/charts.js`)
- Line chart dual-axis: nhiệt độ (°C) và độ ẩm (%)
- Smooth curves với gradient fill
- Responsive, tự resize theo màn hình
- Cập nhật realtime khi có data mới (thêm điểm, xóa điểm cũ)

---

## 🎭 Bước 4 — Styling & Animation

**File:** `dashboard/css/style.css`

### 4.1 Card Component (Glassmorphism)
```css
.card {
  background: var(--bg-glass);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid hsla(0, 0%, 100%, 0.08);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 8px 32px hsla(0, 0%, 0%, 0.3);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px hsla(0, 0%, 0%, 0.4);
}
```

### 4.2 Harvest Alert Animation
```css
@keyframes pulse-red {
  0%, 100% { background: var(--bg-base); }
  50%       { background: hsla(0, 70%, 15%, 0.8); }
}

body.harvest-alert {
  animation: pulse-red 1.5s ease-in-out infinite;
}

#alert-banner {
  background: var(--color-danger);
  color: white;
  text-align: center;
  padding: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  animation: flash 0.8s step-end infinite;
}

@keyframes flash {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.2; }
}
```

### 4.3 Device Indicator
```css
.device-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
  transition: background 0.3s ease;
}

.device-indicator.on {
  background: var(--color-success);
  box-shadow: 0 0 8px var(--color-success);
}

.device-indicator.off {
  background: var(--text-secondary);
}
```

### 4.4 Responsive Design
- **≥ 1200px:** Layout 3 cột (gauges), 1 cột (chart), 2 cột (camera + devices)
- **768px – 1199px:** Layout 2 cột
- **< 768px:** Layout 1 cột (mobile)

---

## 🧪 Bước 5 — Kiểm Thử Frontend

### 5.1 Test với Mock Data
- [ ] Chạy `index.html` trực tiếp bằng trình duyệt (không cần server)
- [ ] Kiểm tra gauge cập nhật giá trị đúng
- [ ] Kiểm tra chart render đúng 24 điểm lịch sử
- [ ] Kiểm tra alert banner và animation harvest alert hoạt động
- [ ] Kiểm tra responsive trên các kích thước màn hình

### 5.2 Thay đổi giá trị mock để test edge cases
```javascript
// Test harvest alert
MOCK_STATUS.harvest_alert = true;
MOCK_STATUS.mushroom_size = "large";

// Test cảnh báo nhiệt độ cao
MOCK_STATUS.temperature = 38.5;

// Test độ ẩm thấp
MOCK_STATUS.humidity = 55.0;
```

### 5.3 Test kết nối API thực (khi backend sẵn sàng)
- Chỉnh `API_BASE` thành IP của Jetson Orin Nano
- Xác nhận CORS được cấu hình trên Flask backend
- Test polling 5 giây với dữ liệu thực

---

## 🔌 Bước 6 — Tích Hợp với Backend (Khi Sẵn Sàng)

### 6.1 API Endpoints cần Flask cung cấp

| Endpoint | Method | Response |
|---|---|---|
| `/api/status` | GET | `{temperature, humidity, mushroom_size, pump, harvest_alert, last_updated}` |
| `/api/history` | GET | `[{timestamp, temperature, humidity}, ...]` |
| `/static/images/latest.jpg` | GET | File ảnh JPEG mới nhất từ Webcam |

### 6.2 Cấu hình CORS trên Flask
```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # Cho phép request từ mọi origin (dev mode)
```

### 6.3 Cập nhật `API_BASE`
```javascript
// Trong js/dashboard.js
const API_BASE = "http://192.168.1.110:5000"; // IP Jetson trên mạng LAN
```

### 6.4 Xử lý ảnh Camera
```javascript
// Cập nhật ảnh nấm mới nhất (thêm timestamp để bypass cache)
function updateCamera(imagePath) {
  const img = document.getElementById('mushroom-image');
  img.src = `${API_BASE}/static/images/latest.jpg?t=${Date.now()}`;
}
```

---

## 📁 Thứ Tự Thực Hiện

```
Bước 1: Tạo cấu trúc thư mục dashboard/
    ↓
Bước 2: Tạo style.css (Design System + Layout)
    ↓
Bước 3: Tạo index.html (HTML skeleton)
    ↓
Bước 4: Tạo mock-data.js (Dữ liệu giả lập)
    ↓
Bước 5: Tạo gauges.js (SVG Gauge component)
    ↓
Bước 6: Tạo charts.js (Chart.js line chart)
    ↓
Bước 7: Tạo dashboard.js (Polling logic + UI updater)
    ↓
Bước 8: Test toàn bộ với mock data
    ↓
Bước 9: (Sau khi có backend) Kết nối API thực
```

---

## 🛠️ Công Nghệ & Thư Viện

| Thư Viện | Phiên Bản | Mục Đích | CDN |
|---|---|---|---|
| **Chart.js** | 4.x | Biểu đồ lịch sử nhiệt độ/độ ẩm | `cdn.jsdelivr.net/npm/chart.js` |
| **Google Fonts** | — | Inter + Outfit (typography) | `fonts.googleapis.com` |
| **Vanilla CSS** | — | Toàn bộ styling (không framework) | Không cần |
| **Vanilla JS** | ES2020+ | Logic, Fetch API, DOM manipulation | Không cần |

> ⚠️ **Không dùng React, Vue, Angular** — giữ nguyên Vanilla JS + HTML thuần như thiết kế gốc của dự án để phù hợp với Flask serving static files.

---

## 📐 Mockup Bố Cục Dashboard

```
╔══════════════════════════════════════════════════════════════════╗
║  🌱 IoT Dashboard — Giám Sát Sinh Trưởng Nấm          [16:30] ║
╠══════════════════════════════════════════════════════════════════╣
║  ⚠️ [HIDDEN] CẢNH BÁO THU HOẠCH — BẤM ĐỂ XÁC NHẬN            ║
╠════════════╦════════════╦═══════════════════════════════════════╣
║ 🌡️ NHIỆT  ║ 💧 ĐỘ ẨM  ║  🍄 TRẠNG THÁI AI                    ║
║            ║            ║  Kích cỡ:   🟡 LARGE                 ║
║   ◉ 27.5  ║   ◉ 82.0  ║  Bơm:       🟢 ON                    ║
║    °C      ║     %      ║  Thu hoạch: 🔴 ALERT                 ║
╠════════════╩════════════╩═══════════════════════════════════════╣
║                 📊 Lịch Sử 2 Giờ Qua                          ║
║   35 ─────────────────────────────────────────────── 100%      ║
║   30 ── ·  · ────────·──────────────────·────────── 85%       ║
║   25 ─────── ·  · ────── ·  · ────────────·──────── 70%       ║
║   20 ─────────────────────────────────────────────── 55%       ║
╠══════════════════════════╦═══════════════════════════════════════╣
║   📷 CAMERA FEED          ║  💡 THIẾT BỊ                       ║
║  ┌────────────────────┐  ║   Relay 1 (Bơm):     ●  ON          ║
║  │  [Ảnh nấm mới nhất]│  ║   Relay 2 (Cảnh báo):○  OFF         ║
║  │  AI: small  ──────│  ║                                      ║
║  └────────────────────┘  ║   Cập nhật lần cuối:                ║
║                          ║   16:29:55 — 5s trước               ║
╚══════════════════════════╩═══════════════════════════════════════╝
```

---

## ✅ Checklist Hoàn Thành

### Frontend (Giai đoạn hiện tại)
- [ ] `style.css` — Design system, layout, dark mode
- [ ] `index.html` — Cấu trúc HTML đầy đủ
- [ ] `mock-data.js` — Mock data cho 2 trạng thái (bình thường & alert)
- [ ] `gauges.js` — SVG gauge cho nhiệt độ và độ ẩm
- [ ] `charts.js` — Biểu đồ lịch sử dual-line
- [ ] `dashboard.js` — Polling logic và cập nhật toàn bộ UI
- [ ] Responsive layout (mobile, tablet, desktop)
- [ ] Harvest Alert animation
- [ ] Test trên Chrome, Firefox, Edge

### Tích hợp Backend (Giai đoạn tiếp theo)
- [ ] Kết nối `/api/status` thực
- [ ] Kết nối `/api/history` thực
- [ ] Cập nhật ảnh camera thực
- [ ] Deploy lên Jetson Orin Nano (port 5000)
- [ ] Test trên mạng Wi-Fi LAN

---

*Tài liệu tạo bởi Antigravity AI — 17/07/2026*
