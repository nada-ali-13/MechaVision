#include <SoftwareSerial.h>
const uint8_t BT_RX = 2, BT_TX = 3;
// @pin D2 D3
SoftwareSerial bluetooth(BT_RX, BT_TX);
unsigned long lastCommand = 0;

const uint8_t LEFT_ENABLE = 5, LEFT_IN1 = 7, LEFT_IN2 = 8;
const uint8_t RIGHT_ENABLE = 6, RIGHT_IN1 = 9, RIGHT_IN2 = 10;

void motor(uint8_t enable, uint8_t input1, uint8_t input2, int speed) {
  analogWrite(enable, 0);
  digitalWrite(input1, speed > 0 ? HIGH : LOW);
  digitalWrite(input2, speed < 0 ? HIGH : LOW);
  analogWrite(enable, abs(speed));
}

void drive(int left, int right) {
  motor(LEFT_ENABLE, LEFT_IN1, LEFT_IN2, left);
  motor(RIGHT_ENABLE, RIGHT_IN1, RIGHT_IN2, right);
}

// @pin D5 D7 D8 D6 D9 D10
void beginMotors() {
  const uint8_t pins[] = {LEFT_ENABLE, LEFT_IN1, LEFT_IN2, RIGHT_ENABLE, RIGHT_IN1, RIGHT_IN2};
  for (uint8_t pin : pins) {
    digitalWrite(pin, LOW);
    pinMode(pin, OUTPUT);
  }
  drive(0, 0);
}

void setup() {
  beginMotors();
  bluetooth.begin(9600);
}

void loop() {
  while (bluetooth.available()) {
    char command = bluetooth.read();
    switch (command) {
      case 'F': drive(145, 145); break;
      case 'B': drive(-145, -145); break;
      case 'L': drive(-115, 115); break;
      case 'R': drive(115, -115); break;
      case 'S': drive(0, 0); break;
      default: continue;
    }
    lastCommand = millis();
  }
  if (millis() - lastCommand >= 500UL) drive(0, 0);
}
