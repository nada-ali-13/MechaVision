#include <Servo.h>

// @pin A0 A1 D9 D10
const int panInput = A0;
const int tiltInput = A1;
const int panPin = 9;
const int tiltPin = 10;
Servo pan;
Servo tilt;

void setup() {
  pan.attach(panPin);
  tilt.attach(tiltPin);
}

void loop() {
  pan.write(map(analogRead(panInput), 0, 1023, 25, 155));
  tilt.write(map(analogRead(tiltInput), 0, 1023, 45, 135));
  delay(25);
}
