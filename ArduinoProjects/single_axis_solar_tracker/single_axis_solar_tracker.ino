#include <Servo.h>

// @pin A0 A1 D9
const int sensorLeft = A0;
const int sensorRight = A1;
const int servoPin = 9;
const int tolerance = 40;
int angle = 90;
Servo rotation;

void setup() {
  rotation.attach(servoPin);
  rotation.write(angle);
  Serial.begin(9600);
}

void loop() {
  int left = analogRead(sensorLeft);
  int right = analogRead(sensorRight);
  if (left - right > tolerance && angle < 155) ++angle;
  if (right - left > tolerance && angle > 25) --angle;
  rotation.write(angle);
  Serial.println(angle);
  delay(60);
}
