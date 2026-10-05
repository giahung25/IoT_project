#include <DHT.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <BH1750.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <ESP32Servo.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// ==========================================
// CẤU HÌNH PHẦN CỨNG (PINS) — SA BÀN NẤM
// ==========================================
#define DHTPIN_22      4  // Cảm biến DHT22 trên chân GPIO4
#define DHTPIN_11      6  // Cảm biến DHT11 trên chân GPIO6
#define MQ135_PIN      5  // Cảm biến CO2 / Chất lượng không khí MQ-135 (ADC1_CH4)
#define I2C_SDA        8  // Chân I2C SDA cho BH1750
#define I2C_SCL        9  // Chân I2C SCL cho BH1750

#define SERVO_VENT_PIN 14 // Servo SG90 Cửa Gió (GPIO 14)
#define RELAY_PUMP     15 // LED 1 / Relay 1 — Bơm sương (GPIO 15)
#define RELAY_ALERT    16 // LED 2 / Relay 2 — Còi/Đèn cảnh báo (GPIO 16)
#define RELAY_LIGHT    17 // LED 3 / Relay 3 — Đèn quang hợp (GPIO 17)
#define RELAY_FAN      18 // LED 4 / Relay 4 — Quạt mát (GPIO 18)
#define LED_SAFE_PIN   7  // LED 5 — System Safe Indicator (GPIO 7)

// (Đã loại bỏ hoàn toàn phần màn hình OLED để chống treo bus I2C)

Servo ventServo;

// ==========================================
// ĐỊNH NGHĨA UUID CHO DỊCH VỤ BLE NUS (Nordic UART Service)
// ==========================================
#define SERVICE_UUID           "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
#define CHARACTERISTIC_UUID_RX "6E400002-B5A3-F393-E0A9-E50E24DCCA9E" // Nhận lệnh điều khiển từ Jetson
#define CHARACTERISTIC_UUID_TX "6E400003-B5A3-F393-E0A9-E50E24DCCA9E" // Gửi dữ liệu cảm biến tới Jetson

// Khai báo đối tượng cảm biến
DHT dht22(DHTPIN_22, DHT22);
DHT dht11(DHTPIN_11, DHT11);
BH1750 lightMeter(0x23);

bool bh1750_ok = false;
int current_co2 = 450;
int current_light = 120;

BLEServer *pServer = NULL;
BLECharacteristic *pTxCharacteristic = NULL;
bool deviceConnected = false;
bool oldDeviceConnected = false;

unsigned long lastMsg = 0;
float current_temp = 27.5;
float current_hum = 82.0;

// Xử lý sự kiện kết nối BLE
class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      deviceConnected = true;
      Serial.println("🔵 [BLE] Jetson Gateway CONNECTED!");
    };

    void onDisconnect(BLEServer* pServer) {
      deviceConnected = false;
      Serial.println("⚪ [BLE] Jetson Gateway DISCONNECTED!");
    }
};

void processCommandJson(const String& rxValue) {
  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, rxValue);

  if (error) {
    Serial.print("❌ [JSON Error]: ");
    Serial.println(error.f_str());
    return;
  }

  if (doc.containsKey("pump")) {
    bool pump_state = doc["pump"];
    digitalWrite(RELAY_PUMP, pump_state ? HIGH : LOW);
    Serial.print("💧 [Relay 1] Pump (G15) set to: ");
    Serial.println(pump_state ? "ON (BẬT)" : "OFF (TẮT)");
  }

  if (doc.containsKey("harvest_alert")) {
    bool alert_state = doc["harvest_alert"];
    digitalWrite(RELAY_ALERT, alert_state ? HIGH : LOW);
    Serial.print("🚨 [Relay 2] Harvest Alert (G16) set to: ");
    Serial.println(alert_state ? "ON (BÁO ĐỘNG)" : "OFF (AN TOÀN)");
  }

  if (doc.containsKey("grow_light")) {
    bool light_state = doc["grow_light"];
    digitalWrite(RELAY_LIGHT, light_state ? HIGH : LOW);
    Serial.print("💡 [Relay 3] Grow Light (G17) set to: ");
    Serial.println(light_state ? "ON (BẬT)" : "OFF (TẮT)");
  }

  if (doc.containsKey("cooling_fan")) {
    bool fan_state = doc["cooling_fan"];
    digitalWrite(RELAY_FAN, fan_state ? HIGH : LOW);
    Serial.print("💨 [Relay 4] Cooling Fan (G18) set to: ");
    Serial.println(fan_state ? "ON (BẬT)" : "OFF (TẮT)");
  }

  if (doc.containsKey("vent_gate")) {
    bool vent_state = doc["vent_gate"];
    ventServo.attach(SERVO_VENT_PIN);
    ventServo.write(vent_state ? 180 : 0);
    delay(500);
    ventServo.detach();
    Serial.print("🌀 [Servo] Vent Gate (G14) set to: ");
    Serial.println(vent_state ? "OPEN (180°)" : "CLOSED (0°)");
  }
}

// Xử lý khi nhận dữ liệu từ Jetson qua RX Characteristic (BLE)
class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
      String rxValue = pCharacteristic->getValue();
      Serial.print("📩 [BLE RX Command]: ");
      Serial.println(rxValue);
      processCommandJson(rxValue);
    }
};

void setup() {
  REG_CLR_BIT(RTC_CNTL_BROWN_OUT_REG, RTC_CNTL_BROWN_OUT_ENA); // Chống sụt áp Brownout
  Serial.begin(115200);
  delay(100);

  Serial.println("\n\n=======================================================");
  Serial.println("🍄 ESP32-S3 MUSHROOM IOT CONTROLLER (NO SCREEN VERSION) 🍄");
  Serial.println("=======================================================");

  // Khởi tạo các chân Relay & LED
  pinMode(RELAY_PUMP, OUTPUT);
  pinMode(RELAY_ALERT, OUTPUT);
  pinMode(RELAY_LIGHT, OUTPUT);
  pinMode(RELAY_FAN, OUTPUT);
  pinMode(LED_SAFE_PIN, OUTPUT);

  digitalWrite(RELAY_PUMP, LOW);
  digitalWrite(RELAY_ALERT, LOW);
  digitalWrite(RELAY_LIGHT, LOW);
  digitalWrite(RELAY_FAN, LOW);
  digitalWrite(LED_SAFE_PIN, HIGH); // LED 5 sáng cố định báo bo mạch OK

  pinMode(SERVO_VENT_PIN, OUTPUT);
  digitalWrite(SERVO_VENT_PIN, LOW);

  // Khởi động cảm biến DHT
  dht22.begin();
  dht11.begin();

  // Khởi tạo cảm biến ánh sáng BH1750 (I2C SDA: 8, SCL: 9)
  static TwoWire I2CBH = TwoWire(0);
  I2CBH.begin(I2C_SDA, I2C_SCL);
  if (lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE, 0x23, &I2CBH)) {
    bh1750_ok = true;
    Serial.println("✅ [BH1750] Cảm biến ánh sáng khởi tạo OK (SDA:8, SCL:9)");
  } else {
    Serial.println("⚠️ [BH1750] Chưa cắm hoặc không phản hồi (Sẽ dùng giá trị mô phỏng)");
  }

  // Khởi tạo BLE GATT Server
  BLEDevice::init("ESP32_MushroomNode");
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService *pService = pServer->createService(SERVICE_UUID);

  pTxCharacteristic = pService->createCharacteristic(
                        CHARACTERISTIC_UUID_TX,
                        BLECharacteristic::PROPERTY_NOTIFY
                      );
  pTxCharacteristic->addDescriptor(new BLE2902());

  BLECharacteristic *pRxCharacteristic = pService->createCharacteristic(
                                           CHARACTERISTIC_UUID_RX,
                                           BLECharacteristic::PROPERTY_WRITE
                                         );
  pRxCharacteristic->setCallbacks(new MyCallbacks());

  pService->start();

  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x06);
  pAdvertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();

  Serial.println("📡 [BLE Advertising] Đang phát sóng BLE: 'ESP32_MushroomNode'...");
  Serial.println("⚡ [System Ready] Sẵn sàng đọc cảm biến và nhận lệnh điều khiển!\n");
}

void loop() {
  // Tự động kết nối lại BLE khi ngắt
  if (!deviceConnected && oldDeviceConnected) {
    delay(500);
    pServer->startAdvertising();
    Serial.println("📡 [BLE Re-advertising] Đang phát lại quảng bá BLE...");
    oldDeviceConnected = deviceConnected;
  }
  if (deviceConnected && !oldDeviceConnected) {
    oldDeviceConnected = deviceConnected;
  }

  unsigned long now = millis();
  if (now - lastMsg > 3000 || lastMsg == 0) { // Cập nhật mỗi 3 giây
    lastMsg = now;

    float h22 = dht22.readHumidity();
    float t22 = dht22.readTemperature();
    float h11 = dht11.readHumidity();
    float t11 = dht11.readTemperature();

    float final_t = 27.5; // fallback
    float final_h = 82.0; // fallback
    String active_sensor = "Simulated";

    if (!isnan(h22) && !isnan(t22) && h22 > 0) {
      final_t = t22;
      final_h = h22;
      active_sensor = "DHT22 (G4)";
    } else if (!isnan(h11) && !isnan(t11) && h11 > 0) {
      final_t = t11;
      final_h = h11;
      active_sensor = "DHT11 (G6)";
    } else {
      active_sensor = "Fallback (27.5°C, 82%)";
    }

    current_temp = final_t;
    current_hum = final_h;

    // Đọc ánh sáng BH1750
    if (bh1750_ok) {
      float lux = lightMeter.readLightLevel();
      if (lux >= 0) current_light = (int)lux;
    }

    // Đọc CO2 MQ-135
    int rawAdc = analogRead(MQ135_PIN);
    current_co2 = map(rawAdc, 0, 4095, 400, 2000);

    // In thông số ra USB Serial
    Serial.print("🌱 [Telemetry] Src: ");
    Serial.print(active_sensor);
    Serial.print(" | T: ");
    Serial.print(final_t, 1);
    Serial.print("°C | RH: ");
    Serial.print(final_h, 1);
    Serial.print("% | CO2: ");
    Serial.print(current_co2);
    Serial.print(" ppm | Light: ");
    Serial.print(current_light);
    Serial.println(" Lux");

    // Gửi qua BLE Notify tới Jetson
    if (deviceConnected) {
      StaticJsonDocument<256> doc;
      doc["temperature"] = round(final_t * 10) / 10.0;
      doc["humidity"] = round(final_h * 10) / 10.0;
      doc["co2_ppm"] = current_co2;
      doc["light_lux"] = current_light;
      doc["esp32_online"] = true;
      doc["sensor_source"] = active_sensor;

      char buffer[256];
      serializeJson(doc, buffer);
      pTxCharacteristic->setValue((uint8_t*)buffer, strlen(buffer));
      pTxCharacteristic->notify();
      Serial.print("   📡 [BLE TX Sent]: ");
      Serial.println(buffer);
    }
  }

  // Đọc lệnh trực tiếp từ USB Serial
  if (Serial.available()) {
    String serialCmd = Serial.readStringUntil('\n');
    serialCmd.trim();
    if (serialCmd.length() > 0) {
      Serial.print("🔌 [Serial Direct RX]: ");
      Serial.println(serialCmd);
      processCommandJson(serialCmd);
    }
  }
}
