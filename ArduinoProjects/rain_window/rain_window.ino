#include <Servo.h>

// @pin A0 D9
const int rainInput = A0;
const int servoPin = 9;
const int wetLimit = 420;
const int dryLimit = 570;
Servo shutter;
bool closed = false;

void setup() {
  Serial.begin(9600);
  shutter.attach(servoPin);
  shutter.write(30);
}

void loop() {
  int moisture = analogRead(rainInput);
  Serial.println(moisture);
  if (!closed && moisture < wetLimit) {
    closed = true;
    shutter.write(125);
  } else if (closed && moisture > dryLimit) {
    closed = false;
    shutter.write(30);
  }
  delay(150);
}
