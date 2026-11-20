const uint8_t BEAM_A = 2, BEAM_B = 3;
enum Stage { Clear, FirstA, FirstB, ExitAfterA, ExitAfterB, WaitForClear };
Stage stage = Clear;
unsigned long started = 0, staying = 0;

void setup() {
  pinMode(BEAM_A, INPUT_PULLUP);
  pinMode(BEAM_B, INPUT_PULLUP);
  Serial.begin(9600);
  Serial.println(F("Inside: 0"));
}

void loop() {
  bool a = digitalRead(BEAM_A) == LOW;
  bool b = digitalRead(BEAM_B) == LOW;
  unsigned long now = millis();
  if (stage != Clear && stage != WaitForClear && now - started > 2500UL) stage = WaitForClear;
  switch (stage) {
    case Clear:
      if (a && b) stage = WaitForClear;
      else if (a || b) {
        started = now;
        stage = a ? FirstA : FirstB;
      }
      break;
    case FirstA: if (a && b) stage = ExitAfterA; else if (!a) stage = WaitForClear; break;
    case FirstB: if (a && b) stage = ExitAfterB; else if (!b) stage = WaitForClear; break;
    case ExitAfterA:
      if (!a && b) {
        Serial.print(F("Inside: "));
        Serial.println(++staying);
        stage = WaitForClear;
      } else if (!b) stage = WaitForClear;
      break;
    case ExitAfterB:
      if (a && !b) {
        if (staying) --staying;
        Serial.print(F("Inside: "));
        Serial.println(staying);
        stage = WaitForClear;
      } else if (!a) stage = WaitForClear;
      break;
    case WaitForClear: if (!a && !b) stage = Clear; break;
  }
  delay(10);
}
