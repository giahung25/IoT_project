# -*- coding: utf-8 -*-
import sqlite3
import os
from datetime import datetime
from backend.config import DB_PATH

def get_connection():
    """Tạo kết nối tới SQLite DB."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Khởi tạo cấu trúc các bảng trong Database nếu chưa tồn tại."""
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        
    conn = get_connection()
    cursor = conn.cursor()
    
    # Bảng lưu thông số cảm biến (nhiệt độ, độ ẩm)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        temperature REAL NOT NULL,
        humidity REAL NOT NULL,
        timestamp TEXT NOT NULL
    )
    """)
    
    # Bảng lưu log phân tích hình ảnh của Vision AI
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_path TEXT NOT NULL,
        mushroom_size TEXT NOT NULL,
        confidence INTEGER NOT NULL,
        timestamp TEXT NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()
    print(f"[DB] Database initialized successfully at: {DB_PATH}")

def save_sensor_data(temperature, humidity):
    """Lưu dữ liệu cảm biến vào bảng sensor_logs."""
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    try:
        cursor.execute(
            "INSERT INTO sensor_logs (temperature, humidity, timestamp) VALUES (?, ?, ?)",
            (temperature, humidity, timestamp)
        )
        conn.commit()
    except Exception as e:
        print(f"[DB] Error saving sensor data: {e}")
    finally:
        conn.close()

def save_ai_log(image_path, mushroom_size, confidence):
    """Lưu kết quả phân tích nấm vào bảng ai_logs."""
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    try:
        cursor.execute(
            "INSERT INTO ai_logs (image_path, mushroom_size, confidence, timestamp) VALUES (?, ?, ?, ?)",
            (image_path, mushroom_size, confidence, timestamp)
        )
        conn.commit()
    except Exception as e:
        print(f"[DB] Error saving AI log: {e}")
    finally:
        conn.close()
