// @pin D2 D3 D4
const byte dataPin = 3;
const byte clockPin = 4;
const byte tarePin = 2;
long zeroCount;
bool zeroSet = false;
bool lastPressed = false;
// Set after measuring (loaded mean minus unloaded mean) / known grams.
const float countsPerGram = 0.0f;

bool readRaw(long &result) {
  unsigned long start = millis();
  while (digitalRead(dataPin) == HIGH) {
    if (millis() - start >= 300) return false;
  }
  uint32_t bits = 0;
  noInterrupts();
  for (byte i = 0; i < 24; ++i) {
    digitalWrite(clockPin, HIGH);
    delayMicroseconds(1);
    bits = (bits << 1) | (digitalRead(dataPin) == HIGH ? 1UL : 0UL);
    digitalWrite(clockPin, LOW);
    delayMicroseconds(1);
  }
  digitalWrite(clockPin, HIGH);
  delayMicroseconds(1);
  digitalWrite(clockPin, LOW);
  interrupts();
  if (bits & 0x800000UL) bits |= 0xFF000000UL;
  result = static_cast<int32_t>(bits);
  return true;
}

void setup() {
  pinMode(dataPin, INPUT);
  pinMode(clockPin, OUTPUT);
  pinMode(tarePin, INPUT_PULLUP);
  digitalWrite(clockPin, LOW);
  Serial.begin(9600);
}

void loop() {
  long reading;
  if (!readRaw(reading)) {
    Serial.println(F("HX711 timeout"));
    delay(400);
    return;
  }
  bool pressed = digitalRead(tarePin) == LOW;
  if (!zeroSet || (pressed && !lastPressed)) {
    zeroCount = reading;
    zeroSet = true;
  }
  lastPressed = pressed;
  long net = reading - zeroCount;
  if (countsPerGram == 0.0f) {
    Serial.print(F("Net counts (calibration needed): "));
    Serial.println(net);
  } else {
    Serial.print(F("Mass (g): "));
    Serial.println(net / countsPerGram);
  }
  delay(180);
}
