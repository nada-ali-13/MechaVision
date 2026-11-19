#include <Servo.h>
const uint8_t TRIGGER = 7, ECHO = 8, SERVO_PIN = 9;
// @pin D9
Servo scanner;

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
  scanner.attach(SERVO_PIN);
  Serial.begin(9600);
}

void loop() {
  static int degrees = 25;
  static int increment = 5;
  scanner.write(degrees);
  delay(75);
  Serial.print(degrees);
  Serial.print(',');
  Serial.println(distanceCm(), 1);
  if (degrees >= 155 || (degrees <= 25 && increment < 0)) increment = -increment;
  degrees += increment;
}
