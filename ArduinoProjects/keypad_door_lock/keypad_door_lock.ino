#include <Servo.h>
#include <string.h>

// @pin D2 D3 D4 D5 D6 D7 D8 D9 D10
const byte rowPins[] = {2, 3, 4, 5};
const byte columnPins[] = {6, 7, 8, 9};
const byte servoPin = 10;
const char labels[4][4] = {
  {'1', '2', '3', 'A'}, {'4', '5', '6', 'B'},
  {'7', '8', '9', 'C'}, {'*', '0', '#', 'D'}
};
const char demoCode[] = "2468";
char entered[5] = "";
byte used = 0;
char previousKey = 0;
unsigned long detectedAt = 0;
bool acceptedKey = false;
bool open = false;
unsigned long openedAt = 0;
Servo latch;

char scanKey() {
  char result = 0;
  byte active = 0;
  for (byte row = 0; row < 4; ++row) {
    digitalWrite(rowPins[row], LOW);
    pinMode(rowPins[row], OUTPUT);
    for (byte column = 0; column < 4; ++column) {
      if (digitalRead(columnPins[column]) == LOW) {
        result = labels[row][column];
        ++active;
      }
    }
    pinMode(rowPins[row], INPUT);
  }
  return active == 1 ? result : 0;
}

void setup() {
  for (byte column = 0; column < 4; ++column) {
    pinMode(columnPins[column], INPUT_PULLUP);
  }
  Serial.begin(9600);
  latch.attach(servoPin);
  latch.write(20);
}

void loop() {
  unsigned long now = millis();
  char key = scanKey();
  if (key != previousKey) {
    detectedAt = now;
    previousKey = key;
    acceptedKey = false;
  }
  if (key && !acceptedKey && now - detectedAt >= 35) {
    acceptedKey = true;
    if (key == '*') {
      used = 0;
    } else if (key == '#') {
      entered[used] = '\0';
      if (strcmp(entered, demoCode) == 0) {
        latch.write(90);
        openedAt = now;
        open = true;
        Serial.println(F("Open model latch"));
      } else {
        Serial.println(F("Incorrect code"));
      }
      used = 0;
    } else if (key >= '0' && key <= '9' && used < 4) {
      entered[used++] = key;
    }
  }
  if (open && now - openedAt >= 2500) {
    latch.write(20);
    open = false;
  }
  delay(5);
}
