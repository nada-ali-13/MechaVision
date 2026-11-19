const uint8_t BEAM = 2, RESET_BUTTON = 4;

void setup() {
  pinMode(BEAM, INPUT_PULLUP);
  pinMode(RESET_BUTTON, INPUT_PULLUP);
  Serial.begin(9600);
  Serial.println(F("Count: 0"));
}

void loop() {
  static bool stable = digitalRead(BEAM), rawLast = stable;
  static unsigned long changedAt = 0, count = 0;
  static bool resetLast = HIGH;
  bool raw = digitalRead(BEAM);
  if (raw != rawLast) {
    rawLast = raw;
    changedAt = millis();
  }
  bool reset = digitalRead(RESET_BUTTON);
  if (reset == LOW && resetLast == HIGH) {
    count = 0;
    Serial.println(F("Count: 0"));
  }
  if (raw != stable && millis() - changedAt >= 20UL) {
    stable = raw;
    if (stable == LOW && reset == HIGH) {
      Serial.print(F("Count: "));
      Serial.println(++count);
    }
  }
  resetLast = reset;
}
