#include <Wire.h>
#include <Adafruit_PN532.h>

// @pin D2 D6 D7 A4 A5
const byte shieldIrq = 2;
const byte shieldResetUnused = 3;
const byte allowLed = 6;
const byte denyLed = 7;
Adafruit_PN532 reader(shieldIrq, shieldResetUnused);
uint8_t enrolled[7];
uint8_t enrolledLength = 0;

void setup() {
  Serial.begin(115200);
  pinMode(allowLed, OUTPUT);
  pinMode(denyLed, OUTPUT);
  reader.begin();
  if (!reader.getFirmwareVersion()) {
    Serial.println(F("PN532 shield unavailable"));
    while (true) delay(1000);
  }
  reader.SAMConfig();
  Serial.println(F("First tag after reset enrolls this classroom demo"));
}

void loop() {
  uint8_t uid[10];  // Reserve room for all ISO 14443-A UID sizes.
  uint8_t length = 0;
  if (!reader.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &length, 200)) return;
  if (length != 4 && length != 7) return;
  if (enrolledLength == 0) {
    for (uint8_t index = 0; index < length; ++index) enrolled[index] = uid[index];
    enrolledLength = length;
  }
  bool allowed = length == enrolledLength;
  for (uint8_t index = 0; allowed && index < length; ++index) {
    if (uid[index] != enrolled[index]) allowed = false;
  }
  const byte ledPin = allowed ? allowLed : denyLed;
  digitalWrite(ledPin, HIGH);
  Serial.println(allowed ? F("Recognized tag") : F("Different tag"));
  delay(900);
  digitalWrite(ledPin, LOW);
}
