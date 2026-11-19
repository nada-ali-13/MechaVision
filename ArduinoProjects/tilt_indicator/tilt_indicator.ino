#include <Wire.h>

// @pin D6 D7 A4 A5
const byte address = 0x68;
const int tiltedLed = 6;
const int levelLed = 7;

int16_t readSignedWord() {
  uint16_t highByte = Wire.read();
  return static_cast<int16_t>((highByte << 8) | Wire.read());
}

void setup() {
  Serial.begin(9600);
  pinMode(tiltedLed, OUTPUT);
  pinMode(levelLed, OUTPUT);
  Wire.begin();
  Wire.beginTransmission(address);
  Wire.write(0x6B);
  Wire.write(0);
  if (Wire.endTransmission() != 0) {
    Serial.println(F("MPU6050 not detected"));
    while (true) delay(1000);
  }
}

void loop() {
  Wire.beginTransmission(address);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0 || Wire.requestFrom(address, (byte)6) != 6) {
    digitalWrite(tiltedLed, LOW);
    digitalWrite(levelLed, LOW);
    delay(200);
    return;
  }
  float x = readSignedWord();
  float y = readSignedWord();
  float z = readSignedWord();
  float degrees = atan2(sqrt(x * x + y * y), fabs(z)) * 57.29578f;
  digitalWrite(tiltedLed, degrees >= 20 ? HIGH : LOW);
  digitalWrite(levelLed, degrees < 20 ? HIGH : LOW);
  Serial.println(degrees);
  delay(150);
}
