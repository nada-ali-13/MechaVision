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

const uint8_t SLOT_A = 6, SLOT_B = 7;

void setup() {
  pinMode(SLOT_A, INPUT_PULLUP);
  pinMode(SLOT_B, INPUT_PULLUP);
  lcd.begin(16, 2);
}

void loop() {
  bool occupiedA = digitalRead(SLOT_A) == LOW;
  bool occupiedB = digitalRead(SLOT_B) == LOW;
  lcd.setCursor(0, 0);
  lcd.print(occupiedA ? F("A: FULL ") : F("A: FREE "));
  lcd.print(occupiedB ? F("B: FULL ") : F("B: FREE "));
  lcd.setCursor(0, 1);
  lcd.print(F("Free spaces: "));
  lcd.print(2 - occupiedA - occupiedB);
  delay(250);
}
