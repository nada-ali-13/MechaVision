const uint8_t FLOAT_SWITCH = 2, BUZZER = 8, WARNING_LED = 9;
void setup() {
  pinMode(FLOAT_SWITCH, INPUT_PULLUP);
  pinMode(BUZZER, OUTPUT);
  pinMode(WARNING_LED, OUTPUT);
}

void loop() {
  static bool previousRaw = HIGH, stable = HIGH;
  static unsigned long changedAt = 0;
  bool raw = digitalRead(FLOAT_SWITCH);
  if (raw != previousRaw) {
    changedAt = millis();
    previousRaw = raw;
  }
  if (millis() - changedAt >= 60) stable = raw;
  bool full = stable == LOW;
  digitalWrite(WARNING_LED, full ? HIGH : LOW);
  if (full && millis() % 600 < 250) tone(BUZZER, 2000);
  else noTone(BUZZER);
}
