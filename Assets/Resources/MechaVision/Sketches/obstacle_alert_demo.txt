const uint8_t TRIGGER = 7, ECHO = 8, BUZZER = 9;

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
  pinMode(BUZZER, OUTPUT);
}

void loop() {
  float cm = distanceCm();
  if (cm >= 2 && cm <= 80) {
    unsigned long interval = map(static_cast<long>(cm), 2, 80, 180, 900);
    if (millis() % interval < 110) tone(BUZZER, 1500);
    else noTone(BUZZER);
  } else {
    noTone(BUZZER);
  }
  delay(62);
}
