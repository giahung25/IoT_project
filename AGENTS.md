# 🤖 QUY TẮC BẮT BUỘC CHO TẤT CẢ AI AGENT (ANTIGRAVITY / CLAUDE / GEMINI)

> **DỰ ÁN:** Edge AI & IoT Giám sát Sinh trưởng Nấm  
> **ÁP DỤNG:** Tất cả các AI Agent làm việc trong Workspace này.

---

## 🚨 ĐIỀU KHOẢN TỐI CAO: BẮT BUỘC ĐỌC LOG TRƯỚC KHI LÀM VIỆC

Mỗi khi bắt đầu một phiên làm việc mới (session) hoặc khi nhận yêu cầu từ người dùng, AI Agent **BẮT BUỘC** phải đọc các tệp nhật ký dự án tại thư mục [project_logs/](file:///home/GiaHung/Projects/IoT_project/project_logs/) trước khi đưa ra bất kỳ chẩn đoán, sửa đổi mã nguồn hoặc thực thi lệnh nào.

### 📋 Các tệp cần đọc theo thứ tự:
1. 📄 [project_logs/index.md](file:///home/GiaHung/Projects/IoT_project/project_logs/index.md): Tổng quan cấu trúc nhật ký và trạng thái hiện tại.
2. 📄 [project_logs/session_history.md](file:///home/GiaHung/Projects/IoT_project/project_logs/session_history.md): Lịch sử các phiên làm việc trước đó và ghi chú bàn giao.
3. 📄 [project_logs/issues_and_fixes.md](file:///home/GiaHung/Projects/IoT_project/project_logs/issues_and_fixes.md): Lịch sử các sự cố đã gặp, lệnh đã chạy và giải pháp đã thực thi.

---

## 📝 QUY TẮC GHI LOG SAU KHI THỰC HIỆN CÔNG VIỆC

Sau khi khắc phục sự cố, thêm tính năng hoặc thay đổi cấu hình dự án, AI Agent **BẮT BUỘC** phải cập nhật nhật ký vào thư mục `project_logs/` theo mẫu chuẩn:

### 1. Thông thông tin cần ghi log:
* **Vấn đề gặp phải (Issue):** Mô tả hiện tượng, triệu chứng hoặc lỗi phát sinh.
* **Nguyên nhân gốc rễ (Root Cause):** Phân tích nguyên nhân kỹ thuật thực tế dựa trên log.
* **Lệnh đã thực thi (Commands Run):** Liệt kê chính xác các câu lệnh shell đã dùng để kiểm tra/sửa đổi.
* **Tệp tin đã chỉnh sửa (Files Modified):** Nêu rõ đường dẫn các file đã tạo hoặc sửa đổi.
* **Kết quả & Xác minh (Verification):** Bằng chứng thực tế cho thấy lỗi đã được xử lý (HTTP code, log output).

### 2. Định dạng mẫu ghi log trong `issues_and_fixes.md`:
```markdown
### 📌 [YYYY-MM-DD HH:MM] Tên vấn đề/Sự cố
- **Mô tả vấn đề:** ...
- **Nguyên nhân:** ...
- **Lệnh đã dùng:**
  ```bash
  command_1
  command_2
  ```
- **Tệp tin đã thay đổi:**
  - `path/to/file1.py`: Mô tả thay đổi
- **Kết quả xác minh:** ...
```

---

## ⚙️ CÁC NGUYÊN TẮC KỸ THUẬT CỐT LÕI
1. **Không đoán mò:** Không giả định IP, cổng dịch vụ hay đường dẫn file nếu chưa kiểm tra lệnh thực tế.
2. **Kiểm tra trước khi báo thành công:** Luôn chạy lệnh kiểm tra (curl, status, test frame, ping) xác nhận kết quả trước khi báo cáo cho người dùng.
3. **Bảo tồn mã nguồn:** Không xóa bỏ các đoạn code/comment không liên quan. Đồng bộ thay đổi từ PC sang Jetson khi có chỉnh sửa trong module `backend/`.
