const uint8_t PROBE_POWER = 4, PROBE_SENSE = A0, BUZZER = 8;
const unsigned int WET_THRESHOLD = 300, DRY_THRESHOLD = 200;

void setup() {
  pinMode(PROBE_POWER, OUTPUT);
  digitalWrite(PROBE_POWER, LOW);
  pinMode(BUZZER, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  static bool wet = false;
  digitalWrite(PROBE_POWER, HIGH);
  delay(10);
  analogRead(PROBE_SENSE);
  unsigned int sample = analogRead(PROBE_SENSE);
  digitalWrite(PROBE_POWER, LOW);
  if (sample >= WET_THRESHOLD) wet = true;
  if (sample <= DRY_THRESHOLD) wet = false;
  Serial.println(sample);
  if (wet) tone(BUZZER, 2100, 190);
  delay(500);
}
