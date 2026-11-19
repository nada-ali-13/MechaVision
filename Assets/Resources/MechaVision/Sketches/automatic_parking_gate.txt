#include <Servo.h>
const uint8_t BEAM = 2, SERVO_PIN = 9;
const uint8_t CLOSED = 20, OPEN = 95;
// @pin D9
Servo gate;

void setup() {
  pinMode(BEAM, INPUT_PULLUP);
  gate.attach(SERVO_PIN);
  gate.write(CLOSED);
}

void loop() {
  static bool opened = false;
  static unsigned long lastBlocked = 0;
  unsigned long now = millis();
  if (digitalRead(BEAM) == LOW) {
    lastBlocked = now;
    if (!opened) gate.write(OPEN);
    opened = true;
  }
  if (opened && now - lastBlocked >= 2000UL) {
    gate.write(CLOSED);
    opened = false;
  }
  delay(15);
}
