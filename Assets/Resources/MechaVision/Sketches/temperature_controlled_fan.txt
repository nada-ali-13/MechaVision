const uint8_t TMP36 = A0, FAN = 5;
const float ADC_REFERENCE_V = 5.0f;
const float FAN_ON_C = 30.0f, FAN_OFF_C = 27.0f;

void setup() {
  digitalWrite(FAN, LOW);
  pinMode(FAN, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  static bool running = false;
  unsigned int total = 0;
  for (uint8_t i = 0; i < 8; ++i) {
    total += analogRead(TMP36);
    delay(10);
  }
  float volts = (total / 8.0f) * (ADC_REFERENCE_V / 1023.0f);
  float degrees = (volts - 0.5f) * 100.0f;
  Serial.println(degrees, 1);
  if (volts < 0.1f || volts > 1.75f) running = false;
  else if (degrees >= FAN_ON_C) running = true;
  else if (degrees <= FAN_OFF_C) running = false;
  digitalWrite(FAN, running ? HIGH : LOW);
  delay(400);
}
