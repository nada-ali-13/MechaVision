const uint8_t REED = 2, ACKNOWLEDGE = 4, BUZZER = 8, WARNING_LED = 9;

void setup() {
  pinMode(REED, INPUT_PULLUP);
  pinMode(ACKNOWLEDGE, INPUT_PULLUP);
  pinMode(BUZZER, OUTPUT);
  pinMode(WARNING_LED, OUTPUT);
}

void loop() {
  static bool latched = false, previousRaw = HIGH, stable = HIGH;
  static unsigned long changedAt = 0;
  bool raw = digitalRead(REED);
  if (raw != previousRaw) {
    changedAt = millis();
    previousRaw = raw;
  }
  if (millis() - changedAt >= 45UL) stable = raw;
  if (stable == HIGH) latched = true;
  else if (digitalRead(ACKNOWLEDGE) == LOW) latched = false;

  digitalWrite(WARNING_LED, latched ? HIGH : LOW);
  if (latched && millis() % 800 < 150) tone(BUZZER, 1350);
  else noTone(BUZZER);
}
