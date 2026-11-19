const uint8_t MOISTURE = A0, PUMP = 5;
const int DRY_ADC = 650, WET_ADC = 390;  // Replace with readings from your own sensor.
const uint8_t DRY_LIMIT = 35;
const unsigned long SOAK_MS = 60000;

void setup() {
  digitalWrite(PUMP, LOW);
  pinMode(PUMP, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  static unsigned long lastWatered = 0;
  static bool watered = false;
  constexpr uint8_t Samples = 8;
  unsigned int total = 0;
  for (uint8_t i = 0; i < Samples; i++) {
    total += analogRead(MOISTURE);
    delay(15);
  }
  unsigned int raw = total / Samples;
  int wetness = constrain(map(raw, DRY_ADC, WET_ADC, 0, 100), 0L, 100L);
  Serial.print(raw);
  Serial.print(',');
  Serial.println(wetness);
  const bool valid = raw >= 100 && raw <= 900;
  if (valid && wetness < DRY_LIMIT && (!watered || millis() - lastWatered >= SOAK_MS)) {
    digitalWrite(PUMP, HIGH);
    delay(1200);
    digitalWrite(PUMP, LOW);
    lastWatered = millis();
    watered = true;
  }
  delay(900);
}
