#include <Wire.h>

// @pin A0 A4 A5 D2 D6
const byte rtcAddress = 0x68;
const byte dialPin = A0;
const byte dismissPin = 2;
const byte buzzerPin = 6;
int lastMinute = -1;
int advertisedTarget = -1;
bool ringing = false;
bool sounding = false;
unsigned long startedAt = 0;

byte fromBcd(byte value) {
  return (value >> 4) * 10 + (value & 15);
}

int minuteOfDay() {
  Wire.beginTransmission(rtcAddress);
  Wire.write(1);
  if (Wire.endTransmission(false) != 0 || Wire.requestFrom(rtcAddress, (byte)2) != 2) return -1;
  byte minute = fromBcd(Wire.read() & 0x7F);
  byte rawHours = Wire.read();
  byte hour = (rawHours & 0x40)
    ? fromBcd(rawHours & 0x1F) % 12 + ((rawHours & 0x20) ? 12 : 0)
    : fromBcd(rawHours & 0x3F);
  return hour * 60 + minute;
}

void setup() {
  pinMode(dismissPin, INPUT_PULLUP);
  pinMode(buzzerPin, OUTPUT);
  Wire.begin();
  Serial.begin(9600);
}

void loop() {
  int target = (analogRead(dialPin) / 32) * 45;
  if (target != advertisedTarget) {
    Serial.print(F("Alarm: "));
    Serial.print(target / 60);
    Serial.print(':');
    if (target % 60 < 10) Serial.print('0');
    Serial.println(target % 60);
    advertisedTarget = target;
  }
  int nowMinute = minuteOfDay();
  if (nowMinute >= 0 && nowMinute != lastMinute) {
    if (nowMinute == target) {
      startedAt = millis();
      ringing = true;
    }
    lastMinute = nowMinute;
  }
  if (ringing && (digitalRead(dismissPin) == LOW || millis() - startedAt >= 10000)) {
    ringing = false;
  }
  bool play = ringing && (millis() - startedAt) % 500 < 230;
  if (play != sounding) {
    if (play) {
      tone(buzzerPin, 1950);
    } else {
      noTone(buzzerPin);
    }
    sounding = play;
  }
  delay(100);
}
