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
const float EMPTY_CM = 24.0f, FULL_CM = 5.0f;

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
  lcd.print(F("Water level"));
}

void loop() {
  float cm = distanceCm();
  blankLine(1);
  if (cm < 0) {
    lcd.print(F("No reading"));
  } else {
    float ratio = constrain((EMPTY_CM - cm) / (EMPTY_CM - FULL_CM), 0.0f, 1.0f);
    lcd.print(static_cast<int>(ratio * 100.0f + 0.5f));
    lcd.print('%');
  }
  delay(400);
}
