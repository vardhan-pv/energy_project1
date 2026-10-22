#include <WiFi.h>
#include <WiFiManager.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <PZEM004Tv30.h>
#include <DHT.h>
#include <Wire.h>
#include <hd44780.h>
#include <hd44780ioClass/hd44780_I2Cexp.h>

// ----------------------------- Site configuration ----------------------------
// Change the host whenever Flask runs on another laptop/network. It must match
// the port printed by api_server.py (default 5000, fallback 5001).
static const char *BACKEND_BASE_URL = "http://10.106.86.45:5000";
static const char *DEVICE_ID = "SET_DEVICE_ID";       // from register_physical_esp32.py
static const char *DEVICE_SECRET = "SET_DEVICE_SECRET"; // keep private; never commit real credentials
static const char *APPLIANCE_ID = "SET_APPLIANCE_ID";  // from register_physical_esp32.py
static const char *HOUSE_ID = "SET_HOUSE_ID";
static const char *APPLIANCE_NAME = "IREOS Controlled Load";

#define DHT_PIN 4
#define DHT_TYPE DHT22
#define RELAY_PIN 26
#define WIFI_RESET_PIN 27
#define PZEM_RX_PIN 16
#define PZEM_TX_PIN 17
#define RELAY_ACTIVE_LOW true
#define LOCAL_OVERLOAD_CUTOFF_W 500.0f
#define WIFI_RESET_HOLD_MS 5000UL
#define TELEMETRY_INTERVAL_MS 5000UL
#define CONTROL_POLL_INTERVAL_MS 5000UL
#define LCD_PAGE_INTERVAL_MS 2500UL
#define HTTP_TIMEOUT_MS 2500
#define CONFIG_AP_SSID "IREOS_SETUP"
#define CONFIG_AP_PASSWORD "ireos1234"

// Relay OFF is the safe electrical state (active-low module: pin HIGH).
static const uint8_t RELAY_OFF_LEVEL = RELAY_ACTIVE_LOW ? HIGH : LOW;
static const uint8_t RELAY_ON_LEVEL = RELAY_ACTIVE_LOW ? LOW : HIGH;

HardwareSerial pzemSerial(2);
PZEM004Tv30 pzem(pzemSerial, PZEM_RX_PIN, PZEM_TX_PIN);
DHT dht(DHT_PIN, DHT_TYPE);
hd44780_I2Cexp lcd;
WiFiManager wifiManager;

struct SensorReadings {
  float voltage = NAN;
  float current = NAN;
  float powerW = NAN;
  float energyKwh = NAN;
  float frequencyHz = NAN;
  float powerFactor = NAN;
  float temperatureC = NAN;
  float humidityPct = NAN;
  bool pzemConnected = false;
  bool dhtConnected = false;
  uint32_t sampledAt = 0;
};

SensorReadings readings;
bool relayOn = false;
String backendStatus = "OFFLINE";
String lastDecision = "Awaiting control loop";
String lastDecisionSource = "none";
int lastDecisionCode = -1;
int lcdPage = 0;
uint32_t lastTelemetryAt = 0;
uint32_t lastControlPollAt = 0;
uint32_t lastLcdPageAt = 0;
uint32_t lastSerialAt = 0;
uint32_t wifiResetPressedAt = 0;
bool wifiPortalStarted = false;

void setRelay(bool on, const char *reason) {
  relayOn = on;
  digitalWrite(RELAY_PIN, on ? RELAY_ON_LEVEL : RELAY_OFF_LEVEL);
  Serial.printf("[RELAY] %s (%s)\n", on ? "ON" : "OFF", reason);
}

void printValue(const char *label, float value, const char *unit, uint8_t precision = 2) {
  Serial.printf("%-16s", label);
  if (isnan(value)) Serial.println("N/A");
  else Serial.printf("%.*f %s\n", precision, value, unit);
}

void collectSensors() {
  readings.voltage = pzem.voltage();
  readings.current = pzem.current();
  readings.powerW = pzem.power();
  readings.energyKwh = pzem.energy();
  readings.frequencyHz = pzem.frequency();
  readings.powerFactor = pzem.pf();
  readings.pzemConnected = !isnan(readings.voltage) && !isnan(readings.powerW);

  readings.temperatureC = dht.readTemperature();
  readings.humidityPct = dht.readHumidity();
  readings.dhtConnected = !isnan(readings.temperatureC) && !isnan(readings.humidityPct);
  readings.sampledAt = millis();

  // Keep actual zero readings. Missing sensor values remain JSON null; never invent load.
  if (readings.pzemConnected && readings.powerW >= LOCAL_OVERLOAD_CUTOFF_W) {
    Serial.printf("[SAFETY] Overload %.2f W >= %.2f W; opening relay\n",
                  readings.powerW, LOCAL_OVERLOAD_CUTOFF_W);
    setRelay(false, "local overload cutoff");
  }
}

void checkWifiResetButton() {
  if (digitalRead(WIFI_RESET_PIN) != LOW) {
    wifiResetPressedAt = 0;
    return;
  }
  if (wifiResetPressedAt == 0) wifiResetPressedAt = millis();
  if (millis() - wifiResetPressedAt >= WIFI_RESET_HOLD_MS) {
    Serial.println("[WiFi] Reset held for 5 seconds; clearing saved credentials and restarting");
    wifiManager.resetSettings();
    delay(200);
    ESP.restart();
  }
}

void ensureWifi() {
  if (!wifiPortalStarted) {
    Serial.println("[WiFi] Connecting with saved credentials; setup AP on failure");
    WiFi.mode(WIFI_STA);
    wifiManager.setConfigPortalBlocking(false);
    wifiManager.setConnectTimeout(20);
    wifiManager.setWiFiAutoReconnect(true);
    wifiPortalStarted = true;
    wifiManager.autoConnect(CONFIG_AP_SSID, CONFIG_AP_PASSWORD);
  }
  wifiManager.process();
  if (WiFi.status() == WL_CONNECTED && backendStatus != "ONLINE") {
    Serial.printf("[WiFi] Connected; IP=%s\n", WiFi.localIP().toString().c_str());
  }
}

String telemetryJson() {
  StaticJsonDocument<512> doc;
  doc["device_id"] = DEVICE_ID;
  doc["house_id"] = HOUSE_ID;
  doc["appliance_id"] = APPLIANCE_ID;
  doc["appliance"] = APPLIANCE_NAME;
  doc["voltage"] = readings.voltage;
  doc["current"] = readings.current;
  doc["power_w"] = readings.powerW;
  doc["energy_kwh"] = readings.energyKwh;
  doc["frequency"] = readings.frequencyHz;
  doc["pf"] = readings.powerFactor;
  doc["temperature"] = readings.temperatureC;
  doc["humidity"] = readings.humidityPct;
  doc["relay_state"] = relayOn;
  doc["status"] = relayOn ? "ON" : "OFF";
  if (lastDecisionCode >= 0) {
    doc["latest_rl_action_code"] = lastDecisionCode;
    doc["latest_rl_action"] = lastDecision;
  }
  doc["source"] = "esp32";

  String body;
  serializeJson(doc, body);
  return body;
}

void handleControlResponse(const String &response) {
  StaticJsonDocument<2048> doc;
  if (deserializeJson(doc, response)) {
    Serial.println("[CONTROL] Invalid JSON response");
    return;
  }
  JsonArrayConst items = doc.as<JsonArrayConst>();
  if (items.isNull()) {
    Serial.println("[CONTROL] Expected existing /api/control-loop array response");
    return;
  }

  for (JsonObjectConst item : items) {
    const char *id = item["id"] | "";
    if (String(id) != APPLIANCE_ID) continue;
    const char *source = item["decisionSource"] | "baseline";
    const char *action = item["rlAction"] | nullptr;
    if (action == nullptr) action = item["nextAction"] | "HOLD_SETPOINT";
    int code = item["rlActionCode"] | -1;
    const char *safety = item["safetyStatus"] | "unknown";
    lastDecision = action;
    lastDecisionSource = source;
    lastDecisionCode = code;
    Serial.printf("[CONTROL] Decision=%s code=%d source=%s safety=%s\n",
                  action, code, source, safety);

    // Execute only the real trained RL model's supported OFF action. Baseline
    // heuristics and unsupported reduce/shift actions are reported, not enacted.
    if (String(source) == "rl_model" && code == 3 && String(safety) != "blocked") {
      setRelay(false, "authenticated RL action 3 / Turn OFF");
    } else if (code == 1 || code == 2 || String(action).indexOf("REDUCE") >= 0 || String(action).indexOf("ECO") >= 0) {
      Serial.println("[CONTROL] Reduce/shift is unsupported by the single relay; reporting only");
    } else if (code == 0) {
      Serial.println("[CONTROL] Action 0 Maintain: preserve current safe relay state");
    }
    return;
  }
  Serial.printf("[CONTROL] No control-loop row for appliance %s\n", APPLIANCE_ID);
}

void httpExchange(bool sendTelemetry) {
  if (WiFi.status() != WL_CONNECTED) {
    backendStatus = "OFFLINE";
    return;
  }
  HTTPClient http;
  const String url = String(BACKEND_BASE_URL) + (sendTelemetry ? "/api/telemetry" : "/api/control-loop");
  if (!http.begin(url)) {
    backendStatus = "ERROR";
    Serial.println("[API] Could not initialize HTTP connection");
    return;
  }
  http.setTimeout(HTTP_TIMEOUT_MS);
  http.addHeader("X-Device-Id", DEVICE_ID);
  http.addHeader("X-Device-Secret", DEVICE_SECRET);

  int status;
  if (sendTelemetry) {
    http.addHeader("Content-Type", "application/json");
    const String payload = telemetryJson();
    Serial.println("[API] Sending telemetry");
    status = http.POST(payload);
  } else {
    status = http.GET();
  }
  if (status > 0) {
    const String response = http.getString();
    Serial.printf("[API] HTTP status: %d\n", status);
    if (sendTelemetry) {
      if (status >= 200 && status < 300) {
        backendStatus = "ONLINE";
        Serial.printf("[API] Response: %s\n", response.c_str());
      } else {
        backendStatus = "REJECTED";
        Serial.printf("[API] Telemetry failed: %d %s\n", status, response.c_str());
      }
    } else if (status >= 200 && status < 300) {
      handleControlResponse(response);
    } else {
      Serial.printf("[API] Control-loop request failed: %d %s\n", status, response.c_str());
    }
  } else {
    backendStatus = "OFFLINE";
    Serial.printf("[API] Telemetry failed: %s\n", HTTPClient::errorToString(status).c_str());
  }
  http.end();
}

void lcdWriteLine(uint8_t row, const String &text) {
  static String previous[2] = {"", ""};
  String clipped = text;
  if (clipped.length() > 16) clipped.remove(16);
  while (clipped.length() < 16) clipped += ' ';
  if (previous[row] == clipped) return;
  lcd.setCursor(0, row);
  lcd.print(clipped);
  previous[row] = clipped;
}

String fmt(float value, uint8_t precision, const char *unit) {
  if (isnan(value)) return String("N/A") + unit;
  return String(value, precision) + unit;
}

void updateLcd() {
  if (millis() - lastLcdPageAt >= LCD_PAGE_INTERVAL_MS) {
    lcdPage = (lcdPage + 1) % 5;
    lastLcdPageAt = millis();
  }
  switch (lcdPage) {
    case 0: lcdWriteLine(0, "V " + fmt(readings.voltage, 1, "V")); lcdWriteLine(1, "P " + fmt(readings.powerW, 1, "W")); break;
    case 1: lcdWriteLine(0, "I " + fmt(readings.current, 2, "A")); lcdWriteLine(1, "E " + fmt(readings.energyKwh, 4, "kWh")); break;
    case 2: lcdWriteLine(0, "Temp " + fmt(readings.temperatureC, 1, "C")); lcdWriteLine(1, "Hum " + fmt(readings.humidityPct, 1, "%")); break;
    case 3: lcdWriteLine(0, "Freq " + fmt(readings.frequencyHz, 2, "Hz")); lcdWriteLine(1, "PF " + fmt(readings.powerFactor, 2, "")); break;
    default:
      lcdWriteLine(0, String("Relay ") + (relayOn ? "ON" : "OFF") + " RL " + (lastDecisionCode < 0 ? "--" : String(lastDecisionCode)));
      lcdWriteLine(1, String(WiFi.status() == WL_CONNECTED ? "WiFi OK " : "WiFi -- ") + backendStatus);
      break;
  }
}

void printMonitor() {
  if (millis() - lastSerialAt < 10000UL) return;
  lastSerialAt = millis();
  Serial.println("\n========== IREOS LIVE MONITOR ==========");
  printValue("Voltage", readings.voltage, "V");
  printValue("Current", readings.current, "A");
  printValue("Power", readings.powerW, "W");
  printValue("Energy", readings.energyKwh, "kWh", 4);
  printValue("Frequency", readings.frequencyHz, "Hz");
  printValue("Power Factor", readings.powerFactor, "");
  printValue("Temperature", readings.temperatureC, "C");
  printValue("Humidity", readings.humidityPct, "%");
  Serial.printf("Relay           %s\nPZEM status     %s\nDHT status      %s\nWi-Fi status    %s\nESP32 IP        %s\nBackend status  %s\nRL decision     %s (code=%d, source=%s)\n",
                relayOn ? "ON" : "OFF", readings.pzemConnected ? "CONNECTED" : "DISCONNECTED",
                readings.dhtConnected ? "CONNECTED" : "DISCONNECTED",
                WiFi.status() == WL_CONNECTED ? "CONNECTED" : "DISCONNECTED",
                WiFi.status() == WL_CONNECTED ? WiFi.localIP().toString().c_str() : "N/A",
                backendStatus.c_str(), lastDecision.c_str(), lastDecisionCode, lastDecisionSource.c_str());
  Serial.println("========================================");
}

void setup() {
  // Preload output latch before enabling output to avoid a relay pulse during boot.
  digitalWrite(RELAY_PIN, RELAY_OFF_LEVEL);
  pinMode(RELAY_PIN, OUTPUT);
  relayOn = false;
  pinMode(WIFI_RESET_PIN, INPUT_PULLUP);
  Serial.begin(115200);
  delay(100);
  Serial.println("\nIREOS ESP32 physical firmware starting; relay held OFF until initialized.");
  Wire.begin(21, 22);
  const int lcdStatus = lcd.begin(16, 2);
  if (lcdStatus) {
    Serial.printf("[LCD] hd44780 initialization error: %d\n", lcdStatus);
  } else {
    lcd.backlight();
    lcdWriteLine(0, "IREOS starting");
    lcdWriteLine(1, "Relay safe: OFF");
  }
  dht.begin();
  pzemSerial.begin(9600, SERIAL_8N1, PZEM_RX_PIN, PZEM_TX_PIN);
  ensureWifi();
  collectSensors();
  Serial.println("[BOOT] Sensors initialized; relay remains in safe OFF state.");
}

void loop() {
  const uint32_t now = millis();
  checkWifiResetButton();
  ensureWifi();

  // Always poll sensors, LCD, and local overload protection even with Flask offline.
  static uint32_t lastSensorAt = 0;
  if (now - lastSensorAt >= 1000UL) {
    lastSensorAt = now;
    collectSensors();
    updateLcd();
    printMonitor();
  }
  if (now - lastTelemetryAt >= TELEMETRY_INTERVAL_MS) {
    lastTelemetryAt = now;
    if (readings.pzemConnected && !isnan(readings.powerW)) {
      httpExchange(true);
    } else {
      backendStatus = "SENSOR WAIT";
      Serial.println("[API] Skipping upload: PZEM power reading unavailable; local monitoring continues");
    }
  }
  if (now - lastControlPollAt >= CONTROL_POLL_INTERVAL_MS) {
    lastControlPollAt = now;
    httpExchange(false);
  }
  delay(10);
}
