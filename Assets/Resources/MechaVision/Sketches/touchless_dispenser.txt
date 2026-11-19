#include <Servo.h>

// @pin D2 D9
const int receiverPin = 2;
const int servoPin = 9;
Servo lever;
int clearLevel;
bool armed = true;
byte clearReadings = 0;

void setup() {
  pinMode(receiverPin, INPUT_PULLUP);
  lever.attach(servoPin);
  lever.write(30);
  delay(1500);
  clearLevel = digitalRead(receiverPin);
}

void loop() {
  if (digitalRead(receiverPin) != clearLevel) {
    clearReadings = 0;
    delay(30);
    if (armed && digitalRead(receiverPin) != clearLevel) {
      armed = false;
      lever.write(100);
      delay(450);
      lever.write(30);
    }
  } else {
    if (clearReadings < 4) ++clearReadings;
    if (clearReadings == 4) armed = true;
  }
  delay(35);
}
