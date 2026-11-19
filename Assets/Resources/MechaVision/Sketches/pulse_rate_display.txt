// @pin A0
const int pulsePin = A0;
const int threshold = 550;
const int hysteresis = 25;
bool wasHigh = false;
unsigned long lastPeak = 0;
unsigned long lastSample = 0;

void setup() {
  Serial.begin(115200);
  Serial.println(F("Educational sensor: not medical equipment"));
}

void loop() {
  unsigned long now = millis();
  if (now - lastSample < 10) return;
  lastSample = now;
  int value = analogRead(pulsePin);
  if (!wasHigh && value >= threshold) {
    wasHigh = true;
    if (lastPeak == 0) {
      lastPeak = now;
    } else {
      unsigned long interval = now - lastPeak;
      if (interval >= 300) {
        if (interval <= 2000) {
          Serial.print(F("Estimated BPM: "));
          Serial.println(60000UL / interval);
        }
        lastPeak = now;
      }
    }
  } else if (wasHigh && value < threshold - hysteresis) {
    wasHigh = false;
  }
}
