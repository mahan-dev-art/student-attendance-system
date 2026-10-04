#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <MFRC522.h>
#include "PersianOLED.h"

// ===== USER CONFIGURATION =====
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* SERVER_URL = "https://fierce-alcove-9186.de.deplexo.com/api/attendance";
const char* API_KEY = "change-this-api-key";

// OLED: I2C SSD1306 128x64, usually address 0x3C; SDA=21, SCL=22.
constexpr uint8_t OLED_SDA_PIN = 21;
constexpr uint8_t OLED_SCL_PIN = 22;
constexpr uint8_t OLED_ADDRESS = 0x3C;
constexpr int OLED_WIDTH = 128;
constexpr int OLED_HEIGHT = 64;
Adafruit_SSD1306 display(OLED_WIDTH, OLED_HEIGHT, &Wire, -1);
bool displayReady = false;

// MFRC522: SS=5, RST=27. RST is 27 to avoid conflict with OLED I2C SCL on GPIO22.
constexpr uint8_t RFID_SS_PIN = 5;
constexpr uint8_t RFID_RST_PIN = 27;
MFRC522 rfid(RFID_SS_PIN, RFID_RST_PIN);
unsigned long lastScanMs = 0;
const unsigned long SCAN_COOLDOWN_MS = 2500;

void drawCheckmark(int x, int y, int scale) {
  display.drawLine(x, y + 5 * scale, x + 4 * scale, y + 9 * scale, SSD1306_WHITE);
  display.drawLine(x + 4 * scale, y + 9 * scale, x + 12 * scale, y, SSD1306_WHITE);
  display.drawLine(x, y + 6 * scale, x + 4 * scale, y + 10 * scale, SSD1306_WHITE);
  display.drawLine(x + 4 * scale, y + 10 * scale, x + 12 * scale, y + 1 * scale, SSD1306_WHITE);
}

void drawCross(int x, int y, int scale) {
  display.drawLine(x, y, x + 10 * scale, y + 10 * scale, SSD1306_WHITE);
  display.drawLine(x + 10 * scale, y, x, y + 10 * scale, SSD1306_WHITE);
  display.drawLine(x + 1, y, x + 10 * scale, y + 9 * scale, SSD1306_WHITE);
  display.drawLine(x + 10 * scale, y + 1, x + 1, y + 10 * scale, SSD1306_WHITE);
}

void showMessage(const String& title, const String& detail, bool success, bool showIcon = true) {
  if (!displayReady) {
    Serial.printf("OLED: %s - %s\n", title.c_str(), detail.c_str());
    return;
  }
  const uint8_t* screen = OLED_SCAN;
  if (title == "CONNECTING") screen = OLED_CONNECTING;
  else if (title == "ONLINE") screen = OLED_ONLINE;
  else if (title == "SCAN CARD") screen = OLED_SCAN;
  else if (title == "CHECKING") screen = OLED_CHECKING;
  else if (title == "NO WI-FI") screen = OLED_WIFI;
  else if (title == "SERVER ERR") screen = OLED_SERVER;
  else if (title == "BAD REPLY") screen = OLED_BADREPLY;
  else if (title == "UNKNOWN") screen = OLED_UNKNOWN;
  else if (title == "ALREADY OK") screen = OLED_ALREADY;
  else if (title == "SUCCESS") screen = OLED_SUCCESS;
  else if (title == "API ERROR") screen = OLED_API;
  else if (title == "STARTING") screen = OLED_STARTING;
  display.clearDisplay();
  display.drawBitmap(0, 0, screen, OLED_WIDTH, OLED_HEIGHT, SSD1306_WHITE);
  display.display();
}

void connectWiFi() {
  showMessage("CONNECTING", "Wi-Fi network", true, false);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print('.');
  }
  Serial.println();
  Serial.print("IP: "); Serial.println(WiFi.localIP());
  showMessage("ONLINE", WiFi.localIP().toString(), true, true);
  delay(900);
  showMessage("SCAN CARD", "Tap RFID card", true, false);
}

String uidToString(MFRC522::Uid* uid) {
  String value;
  for (byte i = 0; i < uid->size; i++) {
    if (uid->uidByte[i] < 0x10) value += "0";
    value += String(uid->uidByte[i], HEX);
  }
  value.toUpperCase();
  return value;
}

void sendAttendance(const String& uid) {
  showMessage("CHECKING", "Card: " + uid, true, false);
  if (WiFi.status() != WL_CONNECTED) {
    showMessage("NO WI-FI", "Reconnecting...", false);
    connectWiFi();
  }

  HTTPClient http;
  http.setTimeout(8000);
  if (!http.begin(SERVER_URL)) {
    showMessage("SERVER ERR", "Invalid server URL", false);
    return;
  }
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);

  JsonDocument request;
  request["rfid_uid"] = uid;
  String body;
  serializeJson(request, body);
  int status = http.POST(body);
  String response = http.getString();
  Serial.printf("HTTP %d: %s\n", status, response.c_str());

  if (status == 401 || status == 403) {
    showMessage("API ERROR", "Check API key", false);
    http.end();
    delay(1800);
    showMessage("SCAN CARD", "Tap RFID card", true, false);
    return;
  }

  if (status <= 0) {
    showMessage("SERVER ERR", "Cannot reach server", false);
    http.end();
    delay(1800);
    showMessage("SCAN CARD", "Tap RFID card", true, false);
    return;
  }

  JsonDocument doc;
  DeserializationError error = deserializeJson(doc, response);
  if (error) {
    showMessage("BAD REPLY", "Invalid server JSON", false);
    http.end();
    delay(1800);
    showMessage("SCAN CARD", "Tap RFID card", true, false);
    return;
  }

  bool success = doc["success"] | false;
  String message = doc["message"] | "Request failed";
  if (!success) {
    showMessage("UNKNOWN", "Card not registered", false);
  } else {
    bool duplicate = doc["student"]["duplicate"] | false;
    String studentName = doc["student"]["name"] | "Student";
    if (duplicate) {
      showMessage("ALREADY OK", studentName, true);
    } else {
      showMessage("SUCCESS", studentName, true);
    }
  }

  http.end();
  delay(2200);
  showMessage("SCAN CARD", "Tap RFID card", true, false);
}

void setup() {
  Serial.begin(115200);
  Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN);
  displayReady = display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDRESS);
  if (displayReady) {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.drawBitmap(0, 0, OLED_STARTING, OLED_WIDTH, OLED_HEIGHT, SSD1306_WHITE);
    display.display();
  } else {
    Serial.println("SSD1306 OLED not detected. Check I2C wiring/address.");
  }

  SPI.begin();
  rfid.PCD_Init();
  connectWiFi();
}

void loop() {
  if (millis() - lastScanMs < SCAN_COOLDOWN_MS) return;
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) return;

  String uid = uidToString(&rfid.uid);
  Serial.print("RFID: "); Serial.println(uid);
  sendAttendance(uid);
  lastScanMs = millis();
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
}
