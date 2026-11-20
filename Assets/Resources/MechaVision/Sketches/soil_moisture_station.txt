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

const uint8_t MOISTURE = A0;
const int DRY_ADC = 650, WET_ADC = 390;

void setup() {
  lcd.begin(16, 2);
  lcd.print(F("Soil moisture"));
}

void loop() {
  unsigned int total = 0;
  for (uint8_t i = 0; i < 8; ++i) {
    total += analogRead(MOISTURE);
    delay(20);
  }
  unsigned int raw = total / 8;
  int percentage = constrain(map(raw, DRY_ADC, WET_ADC, 0, 100), 0L, 100L);
  blankLine(1);
  lcd.print(percentage);
  lcd.print(F("% ADC "));
  lcd.print(raw);
  delay(600);
}
