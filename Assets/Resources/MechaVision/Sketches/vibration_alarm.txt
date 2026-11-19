// @pin D2 D6
const byte vibrationPin = 2;
const byte lampPin = 6;
volatile bool detected = false;
unsigned long lastStrike = 0;
int resting;

void vibrationEdge() {
  detected = true;
}

void setup() {
  pinMode(vibrationPin, INPUT_PULLUP);
  pinMode(lampPin, OUTPUT);
  Serial.begin(9600);
  delay(1200);
  resting = digitalRead(vibrationPin);
  attachInterrupt(digitalPinToInterrupt(vibrationPin), vibrationEdge, resting == HIGH ? FALLING : RISING);
}

void loop() {
  noInterrupts();
  bool event = detected;
  detected = false;
  interrupts();
  unsigned long now = millis();
  if (event) {
    lastStrike = now;
    Serial.println(F("Vibration detected"));
  }
  digitalWrite(lampPin, lastStrike && now - lastStrike < 1800 ? HIGH : LOW);
  delay(25);
}
