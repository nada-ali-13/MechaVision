#include <LiquidCrystal.h>
const uint8_t LCD_RS = 12, LCD_ENABLE = 11;
const uint8_t LCD_D4 = 5, LCD_D5 = 4, LCD_D6 = 3, LCD_D7 = 2;
// @pin D12 D11 D5 D4 D3 D2
LiquidCrystal lcd(LCD_RS, LCD_ENABLE, LCD_D4, LCD_D5, LCD_D6, LCD_D7);

void blankLine(uint8_t row) {
  lcd.setCursor(0, row);
  lcd.print(F("                "));
  lcd.setCursor(0, row);
}

#include <DHT.h>
const uint8_t CLIMATE_PIN = 7;
DHT climate(CLIMATE_PIN, DHT11);

void setup() {
  climate.begin();
  lcd.begin(16, 2);
  lcd.print(F("Room climate"));
}

void loop() {
  float temp = climate.readTemperature();
  float humidity = climate.readHumidity();
  blankLine(1);
  if (isnan(temp) || isnan(humidity)) lcd.print(F("Sensor error"));
  else {
    lcd.print(temp, 0);
    lcd.print(F(" C  "));
    lcd.print(humidity, 0);
    lcd.print(F(" % RH"));
  }
  delay(2200);
}
