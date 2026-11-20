const uint8_t LEFT_SENSOR = A0, RIGHT_SENSOR = A1;
// The selected TCRT5000 modules output LOW over the dark line.
// Check both indicators over the course and adjust their trim pots first.
const uint8_t DARK = LOW;

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
  pinMode(LEFT_SENSOR, INPUT);
  pinMode(RIGHT_SENSOR, INPUT);
}

void loop() {
  bool left = digitalRead(LEFT_SENSOR) == DARK;
  bool right = digitalRead(RIGHT_SENSOR) == DARK;
  if (left && right) drive(145, 145);
  else if (left) drive(35, 155);
  else if (right) drive(155, 35);
  else drive(0, 0);
  delay(15);
}
