"""
🔥 Firebase Sync Module — Đồng bộ dữ liệu IoT & Control với Firebase Realtime Database
"""

import os
import json
import time
import threading

try:
    import firebase_admin
    from firebase_admin import credentials, db
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("[Firebase Sync] ⚠️ Chưa cài đặt 'firebase-admin'. Hãy chạy: pip install firebase-admin")

_firebase_initialized = False
_db_ref_status = None
_db_ref_history = None
_db_ref_controls = None

def init_firebase(key_path="firebase_key.json", database_url=None):
    """
    Khởi tạo Firebase Admin SDK.
    :param key_path: Đường dẫn tới file service account JSON (VD: firebase_key.json)
    :param database_url: URL Realtime Database (VD: https://your-app-default-rtdb.firebaseio.com/)
    """
    global _firebase_initialized, _db_ref_status, _db_ref_history, _db_ref_controls

    if not FIREBASE_AVAILABLE:
        print("[Firebase Sync] ❌ Không thể khởi tạo vì thiếu firebase-admin package.")
        return False

    if not os.path.exists(key_path):
        print(f"[Firebase Sync] ⚠️ Không tìm thấy file key: '{key_path}'. Vui lòng tải Service Account key từ Firebase Console.")
        return False

    if not database_url:
        # Đọc từ biến môi trường hoặc dùng mặc định
        database_url = os.environ.get("FIREBASE_DB_URL")

    if not database_url:
        print("[Firebase Sync] ⚠️ Chưa cấu hình FIREBASE_DB_URL.")
        return False

    try:
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': database_url
        })
        
        _db_ref_status = db.reference('status')
        _db_ref_history = db.reference('history')
        _db_ref_controls = db.reference('controls')

        _firebase_initialized = True
        print(f"[Firebase Sync] 🟢 Đã kết nối thành công tới Firebase RTDB: {database_url}")
        return True
    except Exception as e:
        print(f"[Firebase Sync] ❌ Lỗi kết nối Firebase: {e}")
        return False

def push_status(status_dict):
    """Đẩy trạng thái hiện tại (nhiệt độ, độ ẩm, pump, AI,...) lên node /status"""
    if not _firebase_initialized or not _db_ref_status:
        return
    try:
        _db_ref_status.set(status_dict)
    except Exception as e:
        print(f"[Firebase Sync] ❌ Lỗi push status: {e}")

def push_history(history_list):
    """Đẩy mảng lịch sử lên node /history"""
    if not _firebase_initialized or not _db_ref_history:
        return
    try:
        _db_ref_history.set(history_list)
    except Exception as e:
        print(f"[Firebase Sync] ❌ Lỗi push history: {e}")

def start_control_listener(on_control_received):
    """
    Lắng nghe lệnh điều khiển từ Web Client trên node /controls
    :param on_control_received: Hàm callback nhận payload dict khi web gửi lệnh
    """
    if not _firebase_initialized or not _db_ref_controls:
        return

    def _listener(event):
        if event.data is not None:
            print(f"[Firebase Sync] 📥 Nhận lệnh từ Web Client (/controls): {event.data}")
            if callable(on_control_received):
                on_control_received(event.data)

    try:
        _db_ref_controls.listen(_listener)
        print("[Firebase Sync] 👂 Đã bật luồng lắng nghe lệnh từ xa (/controls)")
    except Exception as e:
        print(f"[Firebase Sync] ❌ Lỗi khởi tạo listener: {e}")
