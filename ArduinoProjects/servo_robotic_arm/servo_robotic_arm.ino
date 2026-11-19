#include <Servo.h>

// @pin A0 A1 A2 D2 D9 D10 D11
const byte inputs[] = {A0, A1, A2};
const byte servoPins[] = {9, 10, 11};
const byte buttonPin = 2;
const byte channels = 3;
const int minimum[] = {25, 35, 30};
const int maximum[] = {155, 110, 85};
int remembered[channels];
bool hasPose = false;
Servo arm[channels];

void setup() {
  pinMode(buttonPin, INPUT_PULLUP);
  Serial.begin(9600);
  for (byte index = 0; index < channels; ++index) arm[index].attach(servoPins[index]);
}

void loop() {
  int live[channels];
  for (byte index = 0; index < channels; ++index) {
    live[index] = map(analogRead(inputs[index]), 0, 1023, minimum[index], maximum[index]);
  }
  if (digitalRead(buttonPin) == LOW && !hasPose) {
    for (byte index = 0; index < channels; ++index) remembered[index] = live[index];
    hasPose = true;
    Serial.println(F("Pose recorded; hold button to recall"));
    delay(350);
  }
  bool recall = hasPose && digitalRead(buttonPin) == LOW;
  for (byte index = 0; index < channels; ++index) {
    arm[index].write(recall ? remembered[index] : live[index]);
  }
  delay(30);
}
