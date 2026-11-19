#include <Wire.h>
#include <Adafruit_BME280.h>
Adafruit_BME280 instrument;

void setup() {
  Serial.begin(9600);
  Wire.begin();
  if (!instrument.begin(0x77)) {
    Serial.println(F("BME280 missing at 0x77"));
    for (;;) delay(1000);
  }
  Serial.println(F("Temperature_C,Humidity_pct,Pressure_hPa"));
}

void loop() {
  Serial.print(instrument.readTemperature(), 1);
  Serial.print(',');
  Serial.print(instrument.readHumidity(), 1);
  Serial.print(',');
  Serial.println(instrument.readPressure() / 100.0f, 1);
  delay(2000);
}
