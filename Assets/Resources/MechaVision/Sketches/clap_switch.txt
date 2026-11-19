// @pin A0 D6
const int microphone = A0;
const int lightPin = 6;
const int clapSpan = 135;
bool lightOn = false;
unsigned long lastClap = 0;

void setup() {
  pinMode(lightPin, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  unsigned long start = millis();
  int smallest = 1023;
  int largest = 0;
  while (millis() - start < 35) {
    int sample = analogRead(microphone);
    if (sample < smallest) smallest = sample;
    if (sample > largest) largest = sample;
  }
  int span = largest - smallest;
  Serial.println(span);
  if (span >= clapSpan && millis() - lastClap >= 300) {
    lightOn = !lightOn;
    digitalWrite(lightPin, lightOn ? HIGH : LOW);
    lastClap = millis();
  }
}
