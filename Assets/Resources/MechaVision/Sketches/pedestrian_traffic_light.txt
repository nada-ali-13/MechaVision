const uint8_t REQUEST = 2;
const uint8_t CAR_RED = 3, CAR_YELLOW = 4, CAR_GREEN = 5;
const uint8_t WALK_RED = 6, WALK_GREEN = 7;
enum Phase { CarsGo, CarsWarn, AllRedBefore, Walk, AllRedAfter };
void show(Phase next);
Phase phase = CarsGo;
unsigned long entered = 0;

void show(Phase next) {
  phase = next;
  entered = millis();
  digitalWrite(CAR_RED, next == AllRedBefore || next == Walk || next == AllRedAfter);
  digitalWrite(CAR_YELLOW, next == CarsWarn);
  digitalWrite(CAR_GREEN, next == CarsGo);
  digitalWrite(WALK_RED, next != Walk);
  digitalWrite(WALK_GREEN, next == Walk);
}

void setup() {
  pinMode(REQUEST, INPUT_PULLUP);
  const uint8_t displays[] = {CAR_RED, CAR_YELLOW, CAR_GREEN, WALK_RED, WALK_GREEN};
  for (uint8_t pin : displays) pinMode(pin, OUTPUT);
  show(CarsGo);
}

void loop() {
  unsigned long elapsed = millis() - entered;
  static bool previous = HIGH;
  bool request = digitalRead(REQUEST);
  switch (phase) {
    case CarsGo: if (previous && !request) show(CarsWarn); break;
    case CarsWarn: if (elapsed >= 1800) show(AllRedBefore); break;
    case AllRedBefore: if (elapsed >= 650) show(Walk); break;
    case Walk: if (elapsed >= 4500) show(AllRedAfter); break;
    case AllRedAfter: if (elapsed >= 650) show(CarsGo); break;
  }
  previous = request;
  delay(15);
}
