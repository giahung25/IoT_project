# 📚 Nhật Ký Dự Án & Quản Lý Sự Cố — Edge AI & IoT

> **Mục đích:** Lưu trữ toàn bộ lịch sử phiên làm việc, các vấn đề gặp phải, nguyên nhân kỹ thuật, câu lệnh đã dùng và kết quả xử lý nhằm giúp các phiên làm việc của AI Agent tiếp theo nắm bắt tình hình tức thì.

---

## 🗂️ Cấu Trúc Nhật Ký

Thư mục nhật ký dự án bao gồm các tệp tin sau:

| Tệp tin | Nội dung chính | Trạng thái |
| :--- | :--- | :---: |
| 📄 [AGENTS.md](file:///home/GiaHung/Projects/IoT_project/AGENTS.md) | Quy tắc bắt buộc cho AI Agent (Đọc log trước, Ghi log sau) | 🟢 Active |
| 📄 [session_history.md](file:///home/GiaHung/Projects/IoT_project/project_logs/session_history.md) | Lịch sử theo mốc thời gian của từng phiên làm việc (Session Logs) | 🟢 Active |
| 📄 [issues_and_fixes.md](file:///home/GiaHung/Projects/IoT_project/project_logs/issues_and_fixes.md) | Nhật ký sự cố kỹ thuật, nguyên nhân, lệnh đã chạy & giải pháp | 🟢 Active |

---

## ⚡ Tóm Tắt Trạng Thái Hệ Thống Hiện Tại (Cập nhật: 31/07/2026)

* **Thiết bị biên (Jetson Orin Nano):**
  * IP USB Direct: `192.168.55.1` (SSH user: `jetson`, đã cấu hình ssh key / batchmode).
  * USB Webcam: Đã nhận dạng `/dev/video0` (`USB2.0 FHD UVC WebCam`).
  * Edge AI Backend: Tiến trình `backend.main_jetson` đang chạy ngầm (PID: `3974`).
  * Vision Model: `moondream:latest` trên Ollama (Port `11434`).
* **Đám Mây (Firebase Cloud):**
  * Firebase RTDB: `https://agrishroom-edge-default-rtdb.asia-southeast1.firebasedatabase.app/`
  * Trạng thái đồng bộ: 🟢 Hoạt động thời gian thực (Luồng `send_to_firebase` từ Jetson).
* **Web Dashboard (Local Flask):**
  * Nằm tại: `WEB_IOT/backend.py` (Port `5000`).
  * Khởi chạy qua script: `./run_dashboard.sh`.
