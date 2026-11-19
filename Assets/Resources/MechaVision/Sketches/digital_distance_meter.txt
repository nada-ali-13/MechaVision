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

const uint8_t TRIGGER = 7, ECHO = 8;

float distanceCm() {
  digitalWrite(TRIGGER, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIGGER, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIGGER, LOW);
  unsigned long echoTime = pulseIn(ECHO, HIGH, 30000UL);
  return echoTime ? echoTime * 0.01715f : -1.0f;
}

void setup() {
  pinMode(TRIGGER, OUTPUT);
  pinMode(ECHO, INPUT);
  lcd.begin(16, 2);
  lcd.print(F("Distance meter"));
}

void loop() {
  float cm = distanceCm();
  blankLine(1);
  if (cm < 2.0f || cm > 400.0f) lcd.print(F("Out of range"));
  else {
    lcd.print(cm, 1);
    lcd.print(F(" cm"));
  }
  delay(300);
}
