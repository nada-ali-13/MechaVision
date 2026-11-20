const uint8_t MOTION = 2, ARM_SWITCH = 4, BUZZER = 8, ARMED_LED = 9;
const unsigned long WARMUP_MS = 45000, EXIT_DELAY_MS = 5000;

void setup() {
  pinMode(MOTION, INPUT);
  pinMode(ARM_SWITCH, INPUT_PULLUP);
  pinMode(BUZZER, OUTPUT);
  pinMode(ARMED_LED, OUTPUT);
  delay(WARMUP_MS);
}

void loop() {
  static bool wasArmed = false, alarm = false;
  static unsigned long armedAt = 0;
  unsigned long now = millis();
  bool armed = digitalRead(ARM_SWITCH) == LOW;
  if (!armed) alarm = false;
  if (armed && !wasArmed) armedAt = now;
  bool ready = armed && now - armedAt >= EXIT_DELAY_MS;
  if (ready && digitalRead(MOTION) == HIGH) alarm = true;
  digitalWrite(ARMED_LED, ready || (armed && now % 500 < 250) ? HIGH : LOW);
  if (alarm && now % 700 < 300) tone(BUZZER, 1800);
  else noTone(BUZZER);
  wasArmed = armed;
  delay(20);
}
