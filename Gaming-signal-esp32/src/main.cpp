#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "config.h"


// Hardware pins
const int BUTTON_PIN = 4;  // Switch on GPIO 4
const int LED_PIN = 2;     // Built-in LED on GPIO 2

// Timing variables
bool lastButtonState = HIGH;
unsigned long lastSignalTime = 0;
unsigned long lastDiscordCheck = 0;
const unsigned long cooldownPeriod = 2000;
const unsigned long discordCheckInterval = 3000; // Check every 3 seconds
String lastProcessedMessageId = "";


// State variables
bool gamingSignalActive = false;

// Function declarations
void sendGamingSignal();
void sendResetSignal();
void checkDiscordMessages();

void setup() {
  Serial.begin(115200);
  Serial.println("Gaming signal box starting up...");
  
  // Setup pins
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  Serial.println("Ready to send and receive gaming signals!");

}

void loop() {
  bool currentButtonState = digitalRead(BUTTON_PIN);
  
  // Detect switch state change (toggle behavior)
  static bool switchProcessed = false;
  
  if (currentButtonState == LOW && lastButtonState == HIGH && !switchProcessed) {
    // Switch just turned ON - send gaming signal
    Serial.println("Switch activated! Sending gaming signal...");
    sendGamingSignal();
    gamingSignalActive = true;  // Activate local LED state
    lastSignalTime = millis();
    switchProcessed = true;
    
    // Brief feedback blink
    for (int i = 0; i < 3; i++) {
      digitalWrite(LED_PIN, HIGH);
      delay(100);
      digitalWrite(LED_PIN, LOW);
      delay(100);
    }
  } 
  else if (currentButtonState == HIGH && lastButtonState == LOW && switchProcessed) {
    // Switch just turned OFF - send reset signal to Discord
    Serial.println("Switch deactivated! Sending reset signal...");
    sendResetSignal();  // ← New function to notify all devices
    gamingSignalActive = false;
    switchProcessed = false;
  }
  
  lastButtonState = currentButtonState;
  
  // Check Discord for messages periodically
  if (millis() - lastDiscordCheck > discordCheckInterval) {
    checkDiscordMessages();
    lastDiscordCheck = millis();
  }
  
  // LED stays on if gaming signal is active
  if (gamingSignalActive) {
    digitalWrite(LED_PIN, HIGH);
  } else {
    digitalWrite(LED_PIN, LOW);
  }
  
  delay(50);
}

void sendGamingSignal() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(webhook_url);
    http.addHeader("Content-Type", "application/json");
    
    String message = "{\"content\":\"🎮 " + String(device_name) + " wants to game!\"}";
    
    int httpResponseCode = http.POST(message);
    
    if (httpResponseCode == 200 || httpResponseCode == 204) {
      Serial.println("✅ Gaming signal sent successfully!");
    } else {
      Serial.println("❌ Failed to send signal. Response code: " + String(httpResponseCode));
    }
    
    http.end();
  }
}

void sendResetSignal() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(webhook_url);
    http.addHeader("Content-Type", "application/json");
    
    String message = "{\"content\":\"" + String(device_name) + " says gaming off\"}";
    
    int httpResponseCode = http.POST(message);
    
    if (httpResponseCode == 200 || httpResponseCode == 204) {
      Serial.println("✅ Reset signal sent successfully!");
    } else {
      Serial.println("❌ Failed to send reset signal. Response code: " + String(httpResponseCode));
    }
    
    http.end();
  }
}

void checkDiscordMessages() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  HTTPClient http;
  String url = "https://discord.com/api/v10/channels/" + String(channel_id) + "/messages?limit=10";
  
  http.begin(url);
  http.addHeader("Authorization", "Bot " + String(bot_token));
  
  int httpResponseCode = http.GET();
  
  if (httpResponseCode == 200) {
    String payload = http.getString();
    
    JsonDocument doc;
    deserializeJson(doc, payload);
    
    String latestSignalMessage = "";
    String latestResetMessage = "";
    String latestSignalId = "";
    String latestResetId = "";
    
    // Find the most recent SIGNAL and RESET messages
    for (JsonObject message : doc.as<JsonArray>()) {
      String content = message["content"];
      String messageId = message["id"];
      
      // Skip if we've already processed this message
      if (messageId == lastProcessedMessageId) continue;
      
      // Look for SIGNAL messages from other devices (not our own)
      if (content.startsWith("SIGNAL:") && content.indexOf(device_name) == -1) {
        if (latestSignalMessage == "") { // Only take the first (most recent) one
          latestSignalMessage = content;
          latestSignalId = messageId;
        }
      }
      
      // Look for reset commands
      if (content.indexOf("gaming off") != -1 || 
          content.indexOf("reset gaming") != -1 || 
          content.indexOf("stop gaming") != -1) {
        if (latestResetMessage == "") { // Only take the first (most recent) one
          latestResetMessage = content;
          latestResetId = messageId;
        }
      }
    }
    
    // Process the most recent message (reset takes priority over signal)
    if (latestResetMessage != "" && (latestResetId > lastProcessedMessageId || lastProcessedMessageId == "")) {
      Serial.println("📴 Gaming reset command received from Discord");
      gamingSignalActive = false;
      lastProcessedMessageId = latestResetId;
    }
    else if (latestSignalMessage != "" && (latestSignalId > lastProcessedMessageId || lastProcessedMessageId == "")) {
      int firstColon = latestSignalMessage.indexOf(':');
      int secondColon = latestSignalMessage.indexOf(':', firstColon + 1);
      String senderDevice = latestSignalMessage.substring(firstColon + 1, secondColon);
      
      Serial.println("🎮 Gaming signal received from: " + senderDevice);
      gamingSignalActive = true;
      lastProcessedMessageId = latestSignalId;
    }
    
  } else {
    Serial.println("Failed to check Discord messages: " + String(httpResponseCode));
  }
  
  http.end();
}