#include <SPI.h>
#include <LoRa.h>
#include <DHT.h>
#include <TinyGPSPlus.h>

#define DHTPIN 27
#define DHTTYPE DHT11
#define TILT_PIN 33

#define GPS_RX 16
#define GPS_TX 17

#define LORA_CS 5
#define LORA_RST 14
#define LORA_IRQ 26


DHT dht(DHTPIN, DHTTYPE);
TinyGPSPlus gps;
HardwareSerial gpsSerial(2); 

void setup() {
  Serial.begin(115200);
  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX, GPS_TX);

  dht.begin();
  pinMode(TILT_PIN, INPUT);

  LoRa.setPins(LORA_CS, LORA_RST, LORA_IRQ);
  if (!LoRa.begin(433E6)) {
    Serial.println("LoRa init failed!");
    while (true);
  }
  Serial.println("LoRa sender started.");
}

void loop() {

  float temp = dht.readTemperature();
  float hum = dht.readHumidity();
  bool tilted = digitalRead(TILT_PIN);

  while (gpsSerial.available()) {
    gps.encode(gpsSerial.read());
  }

  float lat = gps.location.isValid() ? gps.location.lat() : 0.0;
  float lng = gps.location.isValid() ? gps.location.lng() : 0.0;
  float speed = gps.speed.isValid() ? gps.speed.kmph() : 0.0;

  // === Create Data Packet ===
  String packet = "TEMP:" + String(temp, 1) +
                  ",HUM:" + String(hum, 1) +
                  ",TILT:" + String(tilted) +
                  ",LAT:" + String(lat, 6) +
                  ",LNG:" + String(lng, 6) +
                  ",SPD:" + String(speed, 2);


  LoRa.beginPacket();
  LoRa.print(packet);
  LoRa.endPacket();

  Serial.println("Sent: " + packet);

  delay(1000); 
}
