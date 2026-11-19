// @pin D2 D3 D4
const byte optionA = 2;
const byte optionB = 3;
const byte resetButton = 4;
unsigned int votesA = 0;
unsigned int votesB = 0;
bool released = true;

void showTotals() {
  Serial.print(F("A: "));
  Serial.print(votesA);
  Serial.print(F("  B: "));
  Serial.println(votesB);
}

void setup() {
  pinMode(optionA, INPUT_PULLUP);
  pinMode(optionB, INPUT_PULLUP);
  pinMode(resetButton, INPUT_PULLUP);
  Serial.begin(9600);
  showTotals();
}

void loop() {
  bool a = digitalRead(optionA) == LOW;
  bool b = digitalRead(optionB) == LOW;
  bool reset = digitalRead(resetButton) == LOW;
  if (!a && !b && !reset) {
    released = true;
  } else if (released) {
    released = false;
    if (reset) {
      votesA = 0;
      votesB = 0;
    } else if (a != b) {
      if (a && votesA < 9999) ++votesA;
      if (b && votesB < 9999) ++votesB;
    }
    showTotals();
  }
  delay(40);
}
