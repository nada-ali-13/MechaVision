const uint8_t LIGHT = A0, LAMP = 5;
const int DARK_ADC = 180, BRIGHT_ADC = 650;

void setup() {
  pinMode(LAMP, OUTPUT);
}

void loop() {
  static int filtered = analogRead(LIGHT);
  filtered = (7 * filtered + analogRead(LIGHT)) / 8;
  int brightness = constrain(map(filtered, DARK_ADC, BRIGHT_ADC, 255, 0), 0L, 255L);
  analogWrite(LAMP, brightness);
  delay(40);
}
