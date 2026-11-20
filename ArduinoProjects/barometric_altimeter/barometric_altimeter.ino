#include <Wire.h>
#include <Adafruit_BMP280.h>

// @pin A4 A5
Adafruit_BMP280 barometer;
float baselineHpa = 0.0f;
const float seaLevelHpa = 1013.25f;

void setup() {
  Serial.begin(9600);
  if (!barometer.begin(0x77) && !barometer.begin(0x76)) {
    Serial.println(F("BMP280 missing: check I2C wiring"));
    while (true) delay(1000);
  }
  for (int sample = 0; sample < 12; ++sample) {
    baselineHpa += barometer.readPressure() / 100.0f;
    delay(100);
  }
  baselineHpa /= 12.0f;
}

void loop() {
  float pressureHpa = barometer.readPressure() / 100.0f;
  float height = 44330.0f * (1.0f - pow(pressureHpa / baselineHpa, 0.1903f));
  Serial.print(F("Pressure (hPa): "));
  Serial.print(pressureHpa);
  Serial.print(F(" | Relative height (m): "));
  Serial.print(height);
  Serial.print(F(" | Standard altitude (m): "));
  Serial.println(barometer.readAltitude(seaLevelHpa));
  delay(1000);
}
