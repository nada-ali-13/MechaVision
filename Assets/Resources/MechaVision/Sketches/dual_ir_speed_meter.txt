// @pin D2 D3
const byte firstGate = 2;
const byte secondGate = 3;
const float spacingM = 0.15f;
int clearFirst;
int clearSecond;
bool lastFirst = false;
bool lastSecond = false;
bool measuring = false;
unsigned long startedAt = 0;

void setup() {
  Serial.begin(115200);
  pinMode(firstGate, INPUT_PULLUP);
  pinMode(secondGate, INPUT_PULLUP);
  delay(1500);
  clearFirst = digitalRead(firstGate);
  clearSecond = digitalRead(secondGate);
}

void loop() {
  bool first = digitalRead(firstGate) != clearFirst;
  bool second = digitalRead(secondGate) != clearSecond;
  unsigned long now = micros();
  if (measuring && now - startedAt > 3000000UL) measuring = false;
  if (!measuring && first && !lastFirst && !second) {
    startedAt = now;
    measuring = true;
  }
  if (measuring && second && !lastSecond) {
    unsigned long elapsed = now - startedAt;
    if (elapsed >= 1000UL) {
      Serial.print(F("Speed (m/s): "));
      Serial.println(spacingM * 1000000.0f / elapsed, 3);
    }
    measuring = false;
  }
  lastFirst = first;
  lastSecond = second;
}
