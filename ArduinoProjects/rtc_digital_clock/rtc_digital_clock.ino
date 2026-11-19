#include <Wire.h>

// @pin A4 A5
const byte rtcAddress = 0x68;
// Send a newline-terminated T HH:MM:SS command to set 24-hour time.
unsigned long lastRead = 0;
char command[10];
byte commandLength = 0;
bool commandTooLong = false;

byte fromBcd(byte value) {
  return (value >> 4) * 10 + (value & 15);
}

byte toBcd(byte value) {
  return (value / 10 << 4) | (value % 10);
}

void printTwo(byte value) {
  if (value < 10) Serial.print('0');
  Serial.print(value);
}

int readTwoDigits(byte offset) {
  char first = command[offset];
  char second = command[offset + 1];
  if (first < '0' || first > '9' || second < '0' || second > '9') return -1;
  return (first - '0') * 10 + (second - '0');
}

bool setTime() {
  if (commandTooLong || commandLength != sizeof command || command[0] != 'T' ||
      command[1] != ' ' || command[4] != ':' || command[7] != ':') return false;
  int hours = readTwoDigits(2);
  int minutes = readTwoDigits(5);
  int seconds = readTwoDigits(8);
  if (hours < 0 || hours > 23 || minutes < 0 || minutes > 59 || seconds < 0 || seconds > 59) return false;
  Wire.beginTransmission(rtcAddress);
  Wire.write(0);
  Wire.write(toBcd(seconds));
  Wire.write(toBcd(minutes));
  Wire.write(toBcd(hours));  // Switch the RTC to 24-hour mode.
  if (Wire.endTransmission() == 0) {
    Serial.println(F("Time updated"));
  } else {
    Serial.println(F("RTC not detected"));
  }
  return true;
}

void readCommand() {
  while (Serial.available()) {
    char character = Serial.read();
    if (character == '\r') continue;
    if (character == '\n') {
      if (!setTime()) Serial.println(F("Enter T HH:MM:SS"));
      commandLength = 0;
      commandTooLong = false;
    } else if (commandLength < sizeof command) {
      command[commandLength++] = character;
    } else {
      commandTooLong = true;
    }
  }
}

void setup() {
  Wire.begin();
  Serial.begin(9600);
}

void loop() {
  readCommand();
  unsigned long now = millis();
  if (now - lastRead < 1000) return;
  lastRead = now;
  Wire.beginTransmission(rtcAddress);
  Wire.write(0);
  if (Wire.endTransmission(false) != 0 || Wire.requestFrom(rtcAddress, (byte)3) != 3) {
    Serial.println(F("RTC not detected"));
    return;
  }
  byte seconds = fromBcd(Wire.read() & 0x7F);
  byte minutes = fromBcd(Wire.read() & 0x7F);
  byte rawHours = Wire.read();
  byte hours = (rawHours & 0x40)
    ? fromBcd(rawHours & 0x1F) % 12 + ((rawHours & 0x20) ? 12 : 0)
    : fromBcd(rawHours & 0x3F);
  printTwo(hours);
  Serial.print(':');
  printTwo(minutes);
  Serial.print(':');
  printTwo(seconds);
  Serial.println();
}
