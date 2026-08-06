# 🔥 Hướng Dẫn Tích Hợp Firebase (Hosting & Realtime Database / Firestore)

> **Mục tiêu:** Đưa ứng dụng Web IoT Giám sát Sinh trưởng Nấm lên đám mây Firebase để:
> 1. **Firebase Hosting:** Truy cập Dashboard từ bất kỳ đâu qua Internet (URL HTTPS miễn phí `.web.app`).
> 2. **Firebase Realtime Database / Firestore:** Đồng bộ dữ liệu nhiệt độ, độ ẩm, AI nấm và nhận lệnh điều khiển Bơm/Cảnh báo từ xa theo thời gian thực mà không cần NAT port/IP tĩnh.

---

## 🏗️ Kiến Trúc Tổng Quan

```text
┌─────────────────────────────────────────┐
│     Phần Cứng & AI Backend              │
│ (ESP32 Cảm biến ──► Jetson / Python)    │
└──────────────────┬──────────────────────┘
                   │  (Push sensor/AI data & Listen control)
                   ▼
┌─────────────────────────────────────────┐
│     Firebase Realtime Database          │
│ - status: {temp, hum, pump, size,...}   │
│ - history: [ {temp, hum, time}, ... ]   │
│ - control: {pump: true/false, ...}      │
└──────────────────▲──────────────────────┘
                   │  (Real-time Sync)
                   ▼
┌─────────────────────────────────────────┐
│     Firebase Hosting Dashboard          │
│ (https://<project-id>.web.app)          │
└─────────────────────────────────────────┘
```

---

## 🚀 BƯỚC 1: Tạo Dự Án trên Firebase Console

1. Truy cập [Firebase Console](https://console.firebase.google.com/) và đăng nhập bằng tài khoản Google.
2. Bấm **"Add project"** (Thêm dự án) và nhập tên dự án (ví dụ: `nam-iot-monitor`).
3. Tắt Google Analytics (không bắt buộc) ➔ Bấm **Create project**.

---

## ⚡ BƯỚC 2: Bật Firebase Realtime Database

1. Trong menu bên trái, chọn **Build ➔ Realtime Database**.
2. Bấm **Create Database** ➔ Chọn Location (ví dụ: `asia-southeast1` hoặc `us-central1`).
3. Chọn Security Rules: Chọn **Start in test mode** (để test dễ dàng trước khi khóa security).
4. Lưu lại **Database URL** (Dạng: `https://<project-id>-default-rtdb.firebaseio.com/`).

---

## 🔑 BƯỚC 3: Tạo Service Account Key cho Backend Python

1. Trong Firebase Console, bấm vào biểu tượng ⚙️ **Project Settings** ➔ chọn thẻ **Service accounts**.
2. Chọn **Python** ➔ Bấm **Generate new private key**.
3. File JSON secret sẽ được tải về. Đổi tên file thành `firebase_key.json` và lưu vào thư mục `WEB_IOT/`.

> ⚠️ **Lưu ý Security:** Thêm `firebase_key.json` vào `.gitignore` để không bị lộ private key khi push Git.

---

## 🐍 BƯỚC 4: Chạy Luồng Đồng Bộ Firebase từ Python Backend

Cài đặt thư viện Python:
```bash
pip install firebase-admin
```

Chạy file đồng bộ Firebase ngầm cùng backend:
```python
# WEB_IOT/firebase_sync.py
import firebase_admin
from firebase_admin import credentials, db
import time
import requests

# Khởi tạo Firebase Admin SDK
cred = credentials.Certificate('firebase_key.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://<project-id>-default-rtdb.firebaseio.com/'
})

ref_status = db.reference('status')
ref_history = db.reference('history')
ref_control = db.reference('control')

print("🔥 Firebase Sync Module is running...")
```

---

## 🌐 BƯỚC 5: Triển Khai Web Dashboard Lên Firebase Hosting

### 1. Cài đặt Firebase CLI (nếu chưa có):
```bash
npm install -g firebase-tools
```

### 2. Đăng nhập Firebase từ Terminal:
```bash
firebase login
```

### 3. Khởi tạo dự án trong thư mục `WEB_IOT`:
```bash
cd /home/GiaHung/Projects/IoT_project/WEB_IOT
firebase init hosting
```
- Select project: Chọn **Use an existing project** ➔ Chọn tên project bạn đã tạo ở Bước 1.
- What do you want to use as your public directory? Nhập: `dashboard`
- Configure as a single-page app (rewrite all urls to /index.html)? Chọn: `Yes`
- Set up automatic builds and deploys with GitHub? Chọn: `No` (hoặc `Yes` nếu muốn CI/CD).

### 4. Deploy ứng dụng lên Đám mây:
```bash
firebase deploy --only hosting
```

Sau khi hoàn tất, Firebase CLI sẽ trả về URL công khai:
👉 `Hosting URL: https://<project-id>.web.app`

---

## 📊 Tóm Tắt Quy Trình Hoạt Động

| Thành phần | Vai trò | Công nghệ |
| --- | --- | --- |
| **ESP32 & Jetson** | Đọc cảm biến DHT11, chạy Vision AI phân tích nấm | MicroPython / C++ & Python (Ollama/OpenCV) |
| **Python Sync Service** | Đẩy `status` & `history` lên Firebase DB, nghe lệnh `control` | `firebase-admin` (Python) |
| **Firebase Realtime DB** | Lưu trữ đám mây trung gian, sync real-time qua WebSocket | Firebase Realtime Database |
| **Web Dashboard** | Giao diện gauge, biểu đồ VPD, nút bấm điều khiển online | HTML5, JS (Firebase Web SDK), CSS3 |

---
