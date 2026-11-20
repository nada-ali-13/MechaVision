#include <LiquidCrystal.h>

// @pin D2 D3 D4 D5 D6 D7 D8 D9 D10
const byte keyHome = 8;
const byte keyGuest = 9;
const byte keyReset = 10;
LiquidCrystal lcd(7, 6, 5, 4, 3, 2);
unsigned int home = 0;
unsigned int guest = 0;
bool released = true;

void drawPoints() {
  lcd.setCursor(0, 1);
  lcd.print(F("                "));
  lcd.setCursor(0, 1);
  lcd.print(home);
  lcd.setCursor(9, 1);
  lcd.print(guest);
}

void setup() {
  pinMode(keyHome, INPUT_PULLUP);
  pinMode(keyGuest, INPUT_PULLUP);
  pinMode(keyReset, INPUT_PULLUP);
  lcd.begin(16, 2);
  lcd.print(F("Home     Guest"));
  drawPoints();
}

void loop() {
  bool addHome = digitalRead(keyHome) == LOW;
  bool addGuest = digitalRead(keyGuest) == LOW;
  bool clear = digitalRead(keyReset) == LOW;
  if (!addHome && !addGuest && !clear) {
    released = true;
  } else if (released) {
    released = false;
    if (clear) {
      home = 0;
      guest = 0;
    } else {
      if (addHome && home < 999) ++home;
      if (addGuest && guest < 999) ++guest;
    }
    drawPoints();
  }
  delay(45);
}
