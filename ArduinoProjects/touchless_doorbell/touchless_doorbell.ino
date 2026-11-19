// @pin D6 D7 D8
const int triggerPin = 7;
const int echoPin = 8;
const int buzzerPin = 6;
bool armed = true;
byte clearSamples = 0;

void setup() {
  pinMode(triggerPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(buzzerPin, OUTPUT);
}

void loop() {
  digitalWrite(triggerPin, LOW);
  delayMicroseconds(2);
  digitalWrite(triggerPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(triggerPin, LOW);
  unsigned long echoUs = pulseIn(echoPin, HIGH, 22000);
  bool nearby = echoUs >= 116 && echoUs <= 1050;
  if (nearby) {
    clearSamples = 0;
    if (armed) {
      tone(buzzerPin, 2100, 160);
      armed = false;
    }
  } else {
    if (clearSamples < 3) ++clearSamples;
    if (clearSamples == 3) armed = true;
  }
  delay(70);
}
