// @pin D2 D3 D6
const byte incrementButton = 2;
const byte startButton = 3;
const byte buzzerPin = 6;
unsigned long seconds = 10;
unsigned long startedAt = 0;
unsigned long lastPrinted = 0;
bool running = false;
bool lastIncrement = false;
bool lastStart = false;

void setup() {
  pinMode(incrementButton, INPUT_PULLUP);
  pinMode(startButton, INPUT_PULLUP);
  pinMode(buzzerPin, OUTPUT);
  Serial.begin(9600);
  Serial.println(F("10 seconds selected. Increment or Start."));
}

void loop() {
  unsigned long now = millis();
  bool increment = digitalRead(incrementButton) == LOW;
  bool start = digitalRead(startButton) == LOW;
  if (!running && increment && !lastIncrement) {
    seconds = seconds == 120 ? 10 : seconds + 10;
    Serial.println(seconds);
  }
  if (start && !lastStart) {
    noTone(buzzerPin);
    running = !running;
    startedAt = now;
    lastPrinted = now;
    Serial.println(running ? F("Countdown started") : F("Countdown cancelled"));
  }
  if (running && now - startedAt >= seconds * 1000UL) {
    running = false;
    tone(buzzerPin, 1900, 750);
    Serial.println(F("Time is up"));
  }
  if (running && now - lastPrinted >= 1000UL) {
    Serial.println(seconds - (now - startedAt) / 1000UL);
    lastPrinted = now;
  }
  lastIncrement = increment;
  lastStart = start;
  delay(35);
}
