# -*- coding: utf-8 -*-

def process_rules(temp, humidity, mushroom_size):
    """
    Xử lý các quy tắc ra quyết định tự động:
    - R1: Nếu độ ẩm < 70% -> Bật máy bơm sương (pump = True)
    - R2: Nếu nhiệt độ > 35°C -> Bật máy bơm làm mát (pump = True)
    - R3: Nếu độ ẩm >= 70% và nhiệt độ <= 35°C -> Tắt máy bơm (pump = False)
    - R4: Nếu kích thước nấm = "large" -> Bật cảnh báo thu hoạch (harvest_alert = True)
    - R5: Nếu kích thước nấm != "large" -> Tắt cảnh báo thu hoạch (harvest_alert = False)
    """
    pump = False
    harvest_alert = False
    
    # R4 & R5: Trạng thái từ AI nhận diện kích thước nấm
    if mushroom_size == "large":
        harvest_alert = True
        
    # R1, R2, R3: Logic điều khiển dựa trên cảm biến môi trường
    if humidity < 70.0:
        pump = True
    elif temp > 35.0:
        pump = True
        
    return {
        "pump": pump,
        "harvest_alert": harvest_alert
    }
