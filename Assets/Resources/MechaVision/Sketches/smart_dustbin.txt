#include <Servo.h>
const uint8_t TRIGGER = 7, ECHO = 8, SERVO_PIN = 9;
const uint8_t CLOSED = 25, OPEN = 100;
// @pin D9
Servo lid;

float distanceCm() {
  digitalWrite(TRIGGER, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIGGER, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIGGER, LOW);
  unsigned long echoTime = pulseIn(ECHO, HIGH, 30000UL);
  return echoTime ? echoTime * 0.01715f : -1.0f;
}

void setup() {
  pinMode(TRIGGER, OUTPUT);
  pinMode(ECHO, INPUT);
  lid.attach(SERVO_PIN);
  lid.write(CLOSED);
}

void loop() {
  static unsigned long lastVisitor = 0;
  static bool opened = false;
  float cm = distanceCm();
  if (cm >= 3 && cm <= 18) {
    lastVisitor = millis();
    if (!opened) lid.write(OPEN);
    opened = true;
  }
  if (opened && millis() - lastVisitor >= 2200UL) {
    lid.write(CLOSED);
    opened = false;
  }
  delay(85);
}
