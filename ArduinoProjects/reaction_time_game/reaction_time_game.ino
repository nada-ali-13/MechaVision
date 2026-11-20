// @pin D2 D6
const byte buttonPin = 2;
const byte lampPin = 6;

void waitUntilReleased() {
  while (digitalRead(buttonPin) == LOW) delay(10);
  delay(30);
}

void setup() {
  pinMode(buttonPin, INPUT_PULLUP);
  pinMode(lampPin, OUTPUT);
  Serial.begin(115200);
}

void loop() {
  Serial.println(F("Press and release to start"));
  while (digitalRead(buttonPin) != LOW) delay(10);
  randomSeed(micros());
  waitUntilReleased();
  unsigned long startedAt = millis();
  unsigned long waiting = random(1200, 4500);
  while (millis() - startedAt < waiting) {
    if (digitalRead(buttonPin) == LOW) {
      Serial.println(F("False start"));
      waitUntilReleased();
      return;
    }
  }
  digitalWrite(lampPin, HIGH);
  startedAt = millis();
  while (digitalRead(buttonPin) != LOW && millis() - startedAt < 5000) {}
  unsigned long reaction = millis() - startedAt;
  digitalWrite(lampPin, LOW);
  if (reaction >= 5000) {
    Serial.println(F("Timeout"));
  } else {
    Serial.print(F("Reaction (ms): "));
    Serial.println(reaction);
  }
  waitUntilReleased();
}
