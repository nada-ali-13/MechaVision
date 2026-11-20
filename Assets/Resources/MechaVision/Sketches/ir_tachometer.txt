// @pin D2
const byte sensorPin = 2;
const unsigned long slots = 1;
volatile unsigned long edges = 0;
unsigned long lastRead;

void registerEdge() {
  ++edges;
}

void setup() {
  pinMode(sensorPin, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(sensorPin), registerEdge, FALLING);
  Serial.begin(9600);
  lastRead = millis();
}

void loop() {
  unsigned long now = millis();
  unsigned long elapsed = now - lastRead;
  if (elapsed < 1000) return;
  noInterrupts();
  unsigned long total = edges;
  edges = 0;
  interrupts();
  lastRead = now;
  float rpm = total * 60000.0f / (slots * elapsed);
  Serial.print(F("Approximate RPM: "));
  Serial.println(rpm, 1);
}
