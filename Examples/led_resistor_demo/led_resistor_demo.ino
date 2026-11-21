// Arduino Uno R3: D9 -> 220 ohm -> LED anode; LED cathode -> GND.
// The LED and resistor are installed while the Uno is disconnected.
constexpr int ledPin = 9;

void setup() {
  pinMode(ledPin, OUTPUT);
}

void loop() {
  digitalWrite(ledPin, HIGH);
  delay(500);
  digitalWrite(ledPin, LOW);
  delay(500);
}
