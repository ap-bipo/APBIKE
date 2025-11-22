#include <Servo.h>
#include <LiquidCrystal_I2C.h>
#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN 10
#define RST_PIN 9

const int buzzer = 6;

String UID = "86 D8 0E 05";  // Correct format with zero-padding
byte lock = 0;

const int trig = 8; 
const int echo = 7; 
void startBuzzing(int x)
{
  	tone(buzzer, x); 
 	  delay(1000);      
	  noTone(buzzer);     // Stop sound... 
}

Servo servo;
LiquidCrystal_I2C lcd(0x27, 16, 2);
MFRC522 rfid(SS_PIN, RST_PIN);

void setup() {
  Serial.begin(9600);
  servo.attach(3);      // Attach first
  servo.write(70);      // Set to locked position

  lcd.init();
  lcd.backlight();

  SPI.begin();
  rfid.PCD_Init();
  pinMode(trig,OUTPUT);  
  pinMode(echo,INPUT);
  pinMode(buzzer,OUTPUT);
}

void loop() {
  unsigned long duration; 
  int distance;         
  digitalWrite(trig,0);   
  delayMicroseconds(2);
  digitalWrite(trig,1); 
  delayMicroseconds(5);  
  digitalWrite(trig,0);   
  duration = pulseIn(echo,HIGH);  
  distance = int(duration/2/29.412);
  Serial.print(distance);
  Serial.println("cm");
  if(distance < 40)
  {
    startBuzzing(5000);
  }
  if(distance<100)
  {
    startBuzzing(3000);
  }
  if(distance<200)
  {
    startBuzzing(1000);
  }
  delay(200);


  lcd.setCursor(4, 0);
  lcd.print("Welcome!");

  lcd.setCursor(1, 1);
  lcd.print("Put your card");

  if (!rfid.PICC_IsNewCardPresent())
    return;
  if (!rfid.PICC_ReadCardSerial())
    return;

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Scanning");

  String ID = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    lcd.print(".");
    if (rfid.uid.uidByte[i] < 0x10) ID.concat(" 0");  // Padding
    else ID.concat(" ");
    ID.concat(String(rfid.uid.uidByte[i], HEX));
    delay(300);
  }

  ID.toUpperCase();  // Make sure format matches
  Serial.print("Built ID: ");
  Serial.println(ID);  // Debug output

  if (ID.substring(1) == UID && lock == 0) {
    servo.write(70);  // Lock
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Door is locked");
    delay(1500);
    lcd.clear();
    lock = 1;
  } else if (ID.substring(1) == UID && lock == 1) {
    servo.write(160);  // Unlock
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Door is open");
    delay(1500);
    lcd.clear();
    lock = 0;
  } else {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Wrong card!");
    delay(1500);
    lcd.clear();
  }

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1(); 
}
