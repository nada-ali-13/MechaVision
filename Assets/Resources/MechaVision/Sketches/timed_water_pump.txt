const uint8_t START_BUTTON = 2, PUMP = 5;
const unsigned long RUN_TIME_MS = 3000;
const unsigned long REST_TIME_MS = 10000;

void setup() {
  digitalWrite(PUMP, LOW);
  pinMode(PUMP, OUTPUT);
  pinMode(START_BUTTON, INPUT_PULLUP);
}

void loop() {
  static bool previous = HIGH, running = false, hasRun = false;
  static unsigned long started = 0, stopped = 0;
  bool pressed = digitalRead(START_BUTTON) == LOW;
  unsigned long now = millis();
  if (running && now - started >= RUN_TIME_MS) {
    digitalWrite(PUMP, LOW);
    running = false;
    hasRun = true;
    stopped = now;
  }
  if (pressed && previous == HIGH && !running && (!hasRun || now - stopped >= REST_TIME_MS)) {
    started = now;
    running = true;
    digitalWrite(PUMP, HIGH);
  }
  previous = pressed ? LOW : HIGH;
  delay(20);
}
