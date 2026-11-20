#include <Wire.h>

// @pin D2 D5 D6 D7 A4 A5
const byte rtcAddress = 0x68;
const byte acknowledgePin = 2;
const byte lamps[] = {5, 6, 7};
const int times[] = {8 * 60, 8 * 60 + 45, 9 * 60 + 30};
const byte eventCount = sizeof times / sizeof times[0];
const char *labels[] = {"Begin lesson", "Clean bench", "Return parts"};
int previousMinute = -1;
int pending = -1;

byte fromBcd(byte value) {
  return (value >> 4) * 10 + (value & 15);
}

int readMinuteOfDay() {
  Wire.beginTransmission(rtcAddress);
  Wire.write(1);
  if (Wire.endTransmission(false) != 0 || Wire.requestFrom(rtcAddress, (byte)2) != 2) return -1;
  byte minute = fromBcd(Wire.read() & 0x7F);
  byte rawHour = Wire.read();
  byte hour = (rawHour & 0x40)
    ? fromBcd(rawHour & 0x1F) % 12 + ((rawHour & 0x20) ? 12 : 0)
    : fromBcd(rawHour & 0x3F);
  if (minute > 59 || hour > 23) return -1;
  return hour * 60 + minute;
}

void setup() {
  for (byte index = 0; index < eventCount; ++index) pinMode(lamps[index], OUTPUT);
  pinMode(acknowledgePin, INPUT_PULLUP);
  Serial.begin(9600);
  Wire.begin();
}

void loop() {
  int minute = readMinuteOfDay();
  if (minute >= 0 && minute != previousMinute) {
    for (byte index = 0; index < eventCount; ++index) {
      if (minute == times[index]) {
        pending = index;
        Serial.println(labels[index]);
      }
    }
    previousMinute = minute;
  }
  if (digitalRead(acknowledgePin) == LOW) pending = -1;
  for (byte index = 0; index < eventCount; ++index) {
    digitalWrite(lamps[index], pending == index ? HIGH : LOW);
  }
  delay(150);
}
