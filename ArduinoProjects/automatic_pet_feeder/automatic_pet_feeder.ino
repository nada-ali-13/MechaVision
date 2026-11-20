#include <Servo.h>

// @pin D2 D9
const int testButton = 2;
const int gatePin = 9;
const unsigned long demoInterval = 30000;
const unsigned long dispenseTime = 800;
Servo gate;
unsigned long lastCycle;
bool dispensing = false;
bool lastPressed = false;

void setup() {
  pinMode(testButton, INPUT_PULLUP);
  gate.attach(gatePin);
  gate.write(25);
  lastCycle = millis();
}

void loop() {
  unsigned long now = millis();
  bool pressed = digitalRead(testButton) == LOW;
  if (!dispensing && ((pressed && !lastPressed) || now - lastCycle >= demoInterval)) {
    gate.write(95);
    dispensing = true;
    lastCycle = now;
  }
  if (dispensing && now - lastCycle >= dispenseTime) {
    gate.write(25);
    dispensing = false;
  }
  lastPressed = pressed;
  delay(30);
}
