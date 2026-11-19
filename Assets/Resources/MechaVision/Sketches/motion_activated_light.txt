const uint8_t MOTION = 2, LAMP = 9;
const unsigned long WARMUP_MS = 45000, HOLD_MS = 5000;
unsigned long poweredAt = 0;

void setup() {
  pinMode(MOTION, INPUT);
  pinMode(LAMP, OUTPUT);
  poweredAt = millis();
}

void loop() {
  static unsigned long lastMotion = 0;
  static bool motionSeen = false;
  unsigned long now = millis();
  if (now - poweredAt < WARMUP_MS && !motionSeen) return;
  if (digitalRead(MOTION) == HIGH) {
    lastMotion = now;
    motionSeen = true;
  }
  digitalWrite(LAMP, motionSeen && now - lastMotion < HOLD_MS ? HIGH : LOW);
}
