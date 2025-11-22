#include <WiFi.h>
#include <SPI.h>
#include <LoRa.h>
#include <WebServer.h>

// LoRa pins
#define LORA_CS 5
#define LORA_RST 14
#define LORA_IRQ 26

const char* ssid = "ESP32_AP";
const char* password = "12345678";

WebServer server(80);

String temperature = "N/A";
String humidity = "N/A";
String tilt = "N/A";
String lat = "0.0";
String lng = "0.0";
String speed = "N/A";

void handleRoot() {
  String html = R"rawliteral(
  <!DOCTYPE html>
  <html>
  <head>
    <title>Bike Tracker</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      body { font-family: Arial; text-align: center; margin: 0; background: #f4f4f4; }
      h1 { background: #333; color: white; padding: 1em; }
      .card {
        display: inline-block; background: white; margin: 1em; padding: 1em;
        border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        min-width: 200px; height: 180px;
      }
      .label { font-weight: bold; font-size: 1.2em; color: #555; }
      .value { font-size: 2em; color: #222; }
      .btn {
        margin-top: 10px;
        display: inline-block;
        background: #007bff;
        color: white;
        padding: 0.5em 1em;
        border-radius: 5px;
        text-decoration: none;
        font-size: 1em;
      }
    </style>
  </head>
  <body>
    <h1>AP-Bike Data</h1>
    <div class="card"><div class="label">Temperature</div><div class="value" id="temp">--</div></div>
    <div class="card"><div class="label">Humidity</div><div class="value" id="hum">--</div></div>
    <div class="card"><div class="label">Tilt</div><div class="value" id="tilt">--</div></div>
    <div class="card"><div class="label">Latitude</div><div class="value" id="lat">--</div></div>
    <div class="card"><div class="label">Longitude</div><div class="value" id="lng">--</div></div>
    <div class="card"><div class="label">Speed (km/h)</div><div class="value" id="spd">--</div></div>
    <div class="card">
      <div class="label">Map</div>
      <a id="maplink" class="btn" href="#" target="_blank">View on Map</a>
    </div>

    <script>
      function updateData() {
        fetch("/data").then(res => res.json()).then(data => {
          document.getElementById("temp").innerText = data.temperature;
          document.getElementById("hum").innerText = data.humidity;
          document.getElementById("tilt").innerText = data.tilt;
          document.getElementById("lat").innerText = data.lat;
          document.getElementById("lng").innerText = data.lng;
          document.getElementById("spd").innerText = data.speed;
          document.getElementById("maplink").href =
            "https://www.google.com/maps/search/?api=1&query=" + data.lat + "," + data.lng;
        });
      }

      setInterval(updateData, 2000);
      window.onload = updateData;
    </script>
  </body>
  </html>
  )rawliteral";

  server.send(200, "text/html", html);
}


void handleData() {
  String json = "{";
  json += "\"temperature\":\"" + temperature + "\",";
  json += "\"humidity\":\"" + humidity + "\",";
  json += "\"tilt\":\"" + tilt + "\",";
  json += "\"lat\":\"" + lat + "\",";
  json += "\"lng\":\"" + lng + "\",";
  json += "\"speed\":\"" + speed + "\"";
  json += "}";
  server.send(200, "application/json", json);
}

void setup() {
  Serial.begin(115200);

  LoRa.setPins(LORA_CS, LORA_RST, LORA_IRQ);
  if (!LoRa.begin(433E6)) {
    Serial.println("LoRa init failed.");
    while (true);
  }

  WiFi.softAP(ssid, password);
  Serial.println("AP IP address: " + WiFi.softAPIP().toString());

  server.on("/", handleRoot);
  server.on("/data", handleData);

  // Fix captive portal redirect
  server.on("/generate_204", []() {
    server.sendHeader("Location", "/", true);
    server.send(302, "text/plain", "");
  });

  server.begin();
  Serial.println("Web server started.");
}

void loop() {
  server.handleClient();

  int packetSize = LoRa.parsePacket();
  if (packetSize) {
    String data = "";
    while (LoRa.available()) {
      data += (char)LoRa.read();
    }

    Serial.println("Received: " + data);

    int tIndex = data.indexOf("TEMP:");
    int hIndex = data.indexOf(",HUM:");
    int tiltIndex = data.indexOf(",TILT:");
    int latIndex = data.indexOf(",LAT:");
    int lngIndex = data.indexOf(",LNG:");
    int spdIndex = data.indexOf(",SPD:");

    if (tIndex >= 0 && hIndex > tIndex)
      temperature = data.substring(tIndex + 5, hIndex);

    if (hIndex >= 0 && tiltIndex > hIndex)
      humidity = data.substring(hIndex + 5, tiltIndex);

    if (tiltIndex >= 0 && latIndex > tiltIndex)
      tilt = data.substring(tiltIndex + 6, latIndex);

    if (latIndex >= 0 && lngIndex > latIndex)
      lat = data.substring(latIndex + 5, lngIndex);

    if (lngIndex >= 0 && spdIndex > lngIndex)
      lng = data.substring(lngIndex + 5, spdIndex);

    if (spdIndex >= 0)
      speed = data.substring(spdIndex + 5);
  }
}
