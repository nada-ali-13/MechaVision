const uint8_t TRIGGER = 11, ECHO = 12;

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
  beginMotors();
  pinMode(TRIGGER, OUTPUT);
  pinMode(ECHO, INPUT);
}

void loop() {
  float cm = distanceCm();
  if (cm < 0) {
    drive(0, 0);
  } else if (cm < 25.0f) {
    drive(0, 0);
    delay(100);
    drive(145, -145);
    delay(260);
    drive(0, 0);
  } else {
    drive(155, 155);
  }
  delay(65);
}
