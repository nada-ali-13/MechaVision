#pragma once
#include "Arduino.h"

struct Servo {
    uint8_t attach(int pin);
    void write(int angle);
    void detach();
};
