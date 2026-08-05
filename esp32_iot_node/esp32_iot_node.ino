#include <DHT.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <BH1750.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <ESP32Servo.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// ==========================================
// CẤU HÌNH PHẦN CỨNG (PINS)
// ==========================================
#define DHTPIN_22 4    // Cảm biến DHT22 trên chân GPIO4
#define DHTPIN_11 6    // Cảm biến DHT11 trên chân GPIO6
#define MQ135_PIN      5  // Cảm biến CO2 / Chất lượng không khí MQ-135 (ADC1_CH4)
#define I2C_SDA        8  // Chân I2C SDA cho BH1750
#define I2C_SCL        9  // Chân I2C SCL cho BH1750

#define SERVO_VENT_PIN 14 // Servo SG90 Cửa Gió (GPIO 14)
#define RELAY_PUMP     15 // LED 1 / Relay 1 — Bơm sương (GPIO 15)
#define RELAY_ALERT    16 // LED 2 / Relay 2 — Còi/Đèn cảnh báo (GPIO 16)
#define RELAY_LIGHT    17 // LED 3 / Relay 3 — Đèn quang hợp (GPIO 17)
#define RELAY_FAN      18 // LED 4 / Relay 4 — Quạt mát (GPIO 18)
#define LED_SAFE_PIN   7  // LED 5 — System Safe Indicator (GPIO 7)

// Chân I2C tự chọn cho màn hình OLED (G1 và G2 không xung đột với USB)
#define OLED_SDA 1
#define OLED_SCL 2
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

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
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

bool bh1750_ok = false;
int current_co2 = 400;
int current_light = 0;

BLEServer *pServer = NULL;
BLECharacteristic *pTxCharacteristic = NULL;
bool deviceConnected = false;
bool oldDeviceConnected = false;

unsigned long lastMsg = 0;
float current_temp = 0.0;
float current_hum = 0.0;
bool oled_ok = false;

// Cập nhật thông tin hiển thị lên màn hình OLED
void updateDisplay(const String& statusMsg = "") {
  if (!oled_ok) return;
  display.clearDisplay();
  
  // Vẽ tiêu đề
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("--- MUSHROOM IOT ---");
  
  // Hiển thị Nhiệt độ
  display.setCursor(0, 16);
  display.print("Temp: ");
  if (isnan(current_temp) || current_temp == 0.0) {
    display.print("--.-");
  } else {
    display.print(current_temp, 1);
  }
  display.println(" C");

  // Hiển thị Độ ẩm
  display.setCursor(0, 32);
  display.print("Humid: ");
  if (isnan(current_hum) || current_hum == 0.0) {
    display.print("--.-");
  } else {
    display.print(current_hum, 1);
  }
  display.println(" %");

  // Hiển thị trạng thái kết nối
  display.setCursor(0, 52);
  display.setTextSize(1);
  if (statusMsg != "") {
    display.print(statusMsg);
  } else {
    display.print("BLE: ");
    display.print(deviceConnected ? "CONNECTED" : "DISCONNECTED");
  }
  
  display.display();
}

// Xử lý sự kiện kết nối BLE
class MyServerCallbacks: public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
      deviceConnected = true;
      Serial.println("[BLE] Device connected!");
      updateDisplay();
    };

    void onDisconnect(BLEServer* pServer) {
      deviceConnected = false;
      Serial.println("[BLE] Device disconnected!");
      updateDisplay();
    }
};

void processCommandJson(const String& rxValue) {
  if (rxValue.length() == 0) return;

  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, rxValue);

  if (error) return;

  if (doc.containsKey("pump")) {
    bool pump_state = doc["pump"];
    digitalWrite(RELAY_PUMP, pump_state ? HIGH : LOW);
    Serial.print("[Relay 1] Pump (G15) set to: ");
    Serial.println(pump_state ? "ON" : "OFF");
  }

  if (doc.containsKey("harvest_alert")) {
    bool alert_state = doc["harvest_alert"];
    digitalWrite(RELAY_ALERT, alert_state ? HIGH : LOW);
    Serial.print("[Relay 2] Alert (G16) set to: ");
    Serial.println(alert_state ? "ON" : "OFF");
  }

  if (doc.containsKey("grow_light")) {
    bool light_state = doc["grow_light"];
    digitalWrite(RELAY_LIGHT, light_state ? HIGH : LOW);
    Serial.print("[Relay 3] Light (G17) set to: ");
    Serial.println(light_state ? "ON" : "OFF");
  }

  if (doc.containsKey("cooling_fan")) {
    bool fan_state = doc["cooling_fan"];
    digitalWrite(RELAY_FAN, fan_state ? HIGH : LOW);
    Serial.print("[Relay 4] Fan (G18) set to: ");
    Serial.println(fan_state ? "ON" : "OFF");
  }

  if (doc.containsKey("vent_gate")) {
    bool vent_state = doc["vent_gate"];
    if (!ventServo.attached()) {
      ventServo.setPeriodHertz(50);
      ventServo.attach(SERVO_VENT_PIN, 500, 2400);
    }
    ventServo.write(vent_state ? 180 : 0);
    delay(600);          // Đợi 0.6 giây để Servo xoay đến vị trí 180° / 0°
    ventServo.detach();  // Ngắt xung PWM để DỪNG quay hoàn toàn
    Serial.print("[Servo] Vent Gate (G14) set to: ");
    Serial.println(vent_state ? "OPEN (180°)" : "CLOSED (0°)");
  }
}

// Xử lý khi nhận dữ liệu từ Jetson qua RX Characteristic (BLE)
class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
      String rxValue = pCharacteristic->getValue();
      processCommandJson(rxValue);
    }
};

void setup() {
  REG_CLR_BIT(RTC_CNTL_BROWN_OUT_REG, RTC_CNTL_BROWN_OUT_ENA); // Tắt hoàn toàn giám sát sụt áp Brownout trên ESP32-S3
  Serial.begin(115200);
  
  pinMode(RELAY_PUMP, OUTPUT);
  pinMode(RELAY_ALERT, OUTPUT);
  pinMode(RELAY_LIGHT, OUTPUT);
  pinMode(RELAY_FAN, OUTPUT);
  pinMode(LED_SAFE_PIN, OUTPUT);

  digitalWrite(RELAY_PUMP, LOW);
  digitalWrite(RELAY_ALERT, LOW);
  digitalWrite(RELAY_LIGHT, LOW);
  digitalWrite(RELAY_FAN, LOW);
  digitalWrite(LED_SAFE_PIN, HIGH); // LED 5 System Safe luôn sáng khi bo mạch OK

  // Chân Servo SG90 (GPIO 14) khởi tạo LOW an toàn, không kích xung PWM khi bật nguồn để chống sụt áp
  pinMode(SERVO_VENT_PIN, OUTPUT);
  digitalWrite(SERVO_VENT_PIN, LOW);


  // Kiểm tra xem chân I2C có cắm màn hình OLED hay không
  pinMode(OLED_SDA, INPUT_PULLUP);
  pinMode(OLED_SCL, INPUT_PULLUP);
  delay(10);
  
  pinMode(OLED_SDA, INPUT);
  pinMode(OLED_SCL, INPUT);
  delay(10);
  
  if (digitalRead(OLED_SDA) == LOW || digitalRead(OLED_SCL) == LOW) {
    Serial.println("Canh bao: Khong phat hien man hinh OLED! Bo qua khoi tao.");
    oled_ok = false;
  } else {
    Wire.begin(OLED_SDA, OLED_SCL);
    if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
      Serial.println(F("Khong khoi tao duoc SSD1306 OLED"));
      oled_ok = false;
    } else {
      oled_ok = true;
      display.clearDisplay();
      display.display();
      Serial.println("Khoi tao man hinh OLED thanh cong!");
      updateDisplay("BLE Initializing...");
    }
  }

  dht22.begin();
  dht11.begin();

  // Khởi tạo BH1750 (I2C SDA: 8, SCL: 9)
  static TwoWire I2CBH = TwoWire(1);
  I2CBH.begin(I2C_SDA, I2C_SCL);
  if (lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE, 0x23, &I2CBH)) {
    bh1750_ok = true;
    Serial.println("[BH1750] Initialized OK (SDA:8, SCL:9)");
  } else {
    Serial.println("[BH1750] Init failed or not connected");
  }

  // Cấu hình BLE
  BLEDevice::init("ESP32_MushroomNode");
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // Tạo BLE Service NUS
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Tạo TX Characteristic (Gửi dữ liệu)
  pTxCharacteristic = pService->createCharacteristic(
                        CHARACTERISTIC_UUID_TX,
                        BLECharacteristic::PROPERTY_NOTIFY
                      );
  pTxCharacteristic->addDescriptor(new BLE2902());

  // Tạo RX Characteristic (Nhận dữ liệu)
  BLECharacteristic *pRxCharacteristic = pService->createCharacteristic(
                                           CHARACTERISTIC_UUID_RX,
                                           BLECharacteristic::PROPERTY_WRITE
                                         );
  pRxCharacteristic->setCallbacks(new MyCallbacks());

  // Bắt đầu Service
  pService->start();

  // Bắt đầu phát quảng bá BLE
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x06);  // Cấu hình tối ưu iOS/Android
  pAdvertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();
  Serial.println("BLE UART Service khoi dong, dang phat quang ba...");
  
  updateDisplay();
}

void loop() {
  // Tự động phát lại quảng bá khi có thiết bị ngắt kết nối
  if (!deviceConnected && oldDeviceConnected) {
      delay(500); // Đợi ổn định stack BLE
      BLEDevice::startAdvertising(); // Phát quảng bá lại
      Serial.println("[BLE] Restart advertising...");
      oldDeviceConnected = deviceConnected;
  }
  // Khi thiết bị mới kết nối
  if (deviceConnected && !oldDeviceConnected) {
      oldDeviceConnected = deviceConnected;
  }

  unsigned long now = millis();
  // Đọc cảm biến và gửi qua BLE mỗi 5 giây
  if (now - lastMsg > 5000 || lastMsg == 0) {
    lastMsg = now;

    float h22 = dht22.readHumidity();
    float t22 = dht22.readTemperature();
    float h11 = dht11.readHumidity();
    float t11 = dht11.readTemperature();

    float final_t = NAN;
    float final_h = NAN;
    String active_sensor = "NONE";

    // Ưu tiên DHT22 (chính xác hơn). Nếu DHT22 không đọc được, tự động chuyển sang DHT11!
    if (!isnan(h22) && !isnan(t22)) {
      final_t = t22;
      final_h = h22;
      active_sensor = "DHT22 (G4)";
    } else if (!isnan(h11) && !isnan(t11)) {
      final_t = t11;
      final_h = h11;
      active_sensor = "DHT11 (G6)";
    }

    if (isnan(final_h) || isnan(final_t)) {
      Serial.println("Loi! Ca 2 cam bien (DHT22 & DHT11) deu khong doc duoc.");
      current_temp = NAN;
      current_hum = NAN;
      updateDisplay("Sensor Error!");
      
      if (deviceConnected) {
        StaticJsonDocument<200> errDoc;
        errDoc["error"] = "DUAL_SENSOR_READ_FAILED";
        errDoc["esp32_online"] = true;
        char errBuffer[128];
        serializeJson(errDoc, errBuffer);
        pTxCharacteristic->setValue((uint8_t*)errBuffer, strlen(errBuffer));
        pTxCharacteristic->notify();
      }
      return;
    }

    current_temp = final_t;
    current_hum = final_h;

    // ── Đọc Cảm Biến Ánh Sáng BH1750 (Lux) ──
    if (bh1750_ok) {
      float lux = lightMeter.readLightLevel();
      if (lux >= 0) current_light = (int)lux;
    }

    // ── Đọc Cảm Biến CO2 MQ-135 (ADC 12-bit -> ppm) ──
    int rawAdc = analogRead(MQ135_PIN);
    current_co2 = map(rawAdc, 0, 4095, 400, 2000);

    updateDisplay();

    Serial.print("[Active: ");
    Serial.print(active_sensor);
    Serial.print("] Temp: ");
    Serial.print(final_t);
    Serial.print("°C | Hum: ");
    Serial.print(final_h);
    Serial.print("% | CO2: ");
    Serial.print(current_co2);
    Serial.print("ppm | Light: ");
    Serial.print(current_light);
    Serial.println("Lux");

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
      Serial.print("[BLE TX]: Sent: ");
      Serial.println(buffer);
    }
  }

  // Đọc lệnh trực tiếp từ USB Serial (UART) khi cắm vào PC
  if (Serial.available()) {
    String serialCmd = Serial.readStringUntil('\n');
    serialCmd.trim();
    if (serialCmd.length() > 0) {
      Serial.print("[Serial Direct RX]: ");
      Serial.println(serialCmd);
      processCommandJson(serialCmd);
    }
  }
}
