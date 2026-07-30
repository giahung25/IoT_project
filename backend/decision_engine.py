# -*- coding: utf-8 -*-
import math

def calculate_vpd(temp, humidity):
    """
    Tính toán áp suất hơi nước thâm hụt VPD (Vapor Pressure Deficit) đơn vị kPa.
    Formula:
      VP_sat = 0.61078 * exp((17.27 * T) / (T + 237.3))
      VPD = VP_sat * (1 - RH / 100)
    """
    if temp is None or humidity is None:
        return 0.5, 0.9, 0.45

    t = float(temp)
    rh = float(humidity)

    vp_sat = 0.61078 * math.exp((17.27 * t) / (t + 237.3))
    vp_act = vp_sat * (rh / 100.0)
    vpd = vp_sat - vp_act

    return round(vpd, 2), round(vp_sat, 2), round(vp_act, 2)


def evaluate_growth_zone(temp, humidity, vpd):
    """
    Đánh giá vùng sinh trưởng sinh học & điểm sức khỏe môi trường (Environment Health Score - EHS).
    """
    t = float(temp or 27.0)
    rh = float(humidity or 75.0)

    # 1. Xác định Vùng Sinh Trưởng
    if 25.0 <= t <= 30.0 and 80.0 <= rh <= 90.0 and 0.3 <= vpd <= 0.8:
        zone_code = "optimal"
        zone_name = "🟢 Vùng Tối Ưu (Optimal)"
        zone_desc = "Tỷ lệ tăng trưởng tối đa. Nấm hô hấp & hấp thụ dưỡng chất xuất sắc."
        ehs = 98
    elif rh < 70.0 or vpd > 1.0:
        zone_code = "dehydration"
        zone_name = "🟡 Vùng Khô Hạn (Dehydration)"
        zone_desc = "Cảnh báo thoát hơi nước quá nhanh. Nguy cơ quéo mép tai nấm, teo mầm."
        ehs = 65
    elif t > 32.0:
        zone_code = "heat_stress"
        zone_name = "🟠 Vùng Sốc Nhiệt (Heat Stress)"
        zone_desc = "Nhiệt độ cao gây mất nước và suy yếu hệ tơ nấm."
        ehs = 55
    elif rh > 92.0 and t >= 28.0:
        zone_code = "mold_risk"
        zone_name = "🔴 Nguy Cơ Nấm Mốc (Mold Risk)"
        zone_desc = "Bão hòa ẩm kéo dài. Nguy cơ bùng phát mốc xanh Trichoderma."
        ehs = 40
    else:
        zone_code = "normal"
        zone_name = "🔵 Vùng Bình Thường (Normal)"
        zone_desc = "Môi trường ổn định, nấm phát triển nhịp nhàng."
        ehs = 85

    return {
        "zone_code": zone_code,
        "zone_name": zone_name,
        "zone_desc": zone_desc,
        "health_score": ehs
    }


def process_rules(temp, humidity, mushroom_size, co2_ppm=400, light_lux=500):
    """
    Xử lý các quy tắc ra quyết định tự động:
    - R1: Nếu độ ẩm < 70% hoặc Temp > 35°C -> Bật bơm sương (pump = True)
    - R2: Nếu kích thước nấm = "large" hoặc CO2 > 1000 ppm -> Bật cảnh báo (harvest_alert = True)
    - R3: Nếu ánh sáng BH1750 < 400 Lux -> Bật đèn quang hợp (grow_light = True)
    - R4: Nếu nhiệt độ > 31°C -> Bật quạt mát (cooling_fan = True)
    - R5: Nếu CO2 > 1000 ppm hoặc Temp > 31°C -> Mở cửa gió (vent_gate = True)
    """
    pump = False
    harvest_alert = False
    grow_light = False
    cooling_fan = False
    vent_gate = False

    vpd, vp_sat, vp_act = calculate_vpd(temp, humidity)
    zone_info = evaluate_growth_zone(temp, humidity, vpd)

    # R2: Trạng thái cảnh báo từ AI hoặc CO2 cao
    if mushroom_size == "large" or (co2_ppm and co2_ppm > 1000):
        harvest_alert = True

    # R1: Bơm sương
    if humidity and humidity < 70.0 or (temp and temp > 35.0):
        pump = True

    # R3: Đèn quang hợp (Lux < 400)
    if light_lux is not None and light_lux < 400:
        grow_light = True

    # R4: Quạt làm mát (Temp > 31°C)
    if temp and temp > 31.0:
        cooling_fan = True

    # R5: Cửa gió thông khí PWM (CO2 > 1000 ppm hoặc Temp > 31°C)
    if (co2_ppm and co2_ppm > 1000) or (temp and temp > 31.0):
        vent_gate = True

    return {
        "pump": pump,
        "harvest_alert": harvest_alert,
        "grow_light": grow_light,
        "cooling_fan": cooling_fan,
        "vent_gate": vent_gate,
        "vpd": vpd,
        "vp_sat": vp_sat,
        "vp_act": vp_act,
        "growth_zone": zone_info["zone_name"],
        "zone_code": zone_info["zone_code"],
        "zone_desc": zone_info["zone_desc"],
        "health_score": zone_info["health_score"]
    }
