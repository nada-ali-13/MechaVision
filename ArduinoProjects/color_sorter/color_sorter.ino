#include <Wire.h>
#include <Servo.h>

// @pin A4 A5 D9
const byte sensorAddress = 0x29;
const int servoPin = 9;
Servo diverter;

bool writeRegister(byte registerId, byte value) {
  Wire.beginTransmission(sensorAddress);
  Wire.write(0x80 | registerId);
  Wire.write(value);
  return Wire.endTransmission() == 0;
}

uint16_t readChannel() {
  uint16_t lowByte = Wire.read();
  return lowByte | (static_cast<uint16_t>(Wire.read()) << 8);
}

void setup() {
  Serial.begin(9600);
  Wire.begin();
  diverter.attach(servoPin);
  diverter.write(90);
  if (!writeRegister(0x01, 0xEB) || !writeRegister(0x00, 0x01)) {
    Serial.println(F("Color sensor not detected"));
    while (true) delay(1000);
  }
  delay(4);
  writeRegister(0x00, 0x03);
}

void loop() {
  Wire.beginTransmission(sensorAddress);
  Wire.write(0xB4);  // Read clear, red, green and blue consecutively.
  if (Wire.endTransmission(false) != 0 || Wire.requestFrom(sensorAddress, (byte)8) != 8) {
    diverter.write(90);
    delay(150);
    return;
  }
  uint16_t clear = readChannel();
  uint32_t red = readChannel();
  uint32_t green = readChannel();
  uint32_t blue = readChannel();
  if (clear >= 60 && red * 10 > blue * 13 && red * 10 > green * 13) {
    diverter.write(45);
    Serial.println(F("Red"));
  } else if (clear >= 60 && blue * 10 > red * 13 && blue * 10 > green * 13) {
    diverter.write(135);
    Serial.println(F("Blue"));
  } else {
    diverter.write(90);
    Serial.println(F("Neutral"));
  }
  delay(220);
}
