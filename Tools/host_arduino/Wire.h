#pragma once
#include "Arduino.h"

struct TwoWire : Print {
    void begin();
    void beginTransmission(uint8_t address);
    uint8_t endTransmission(bool stop = true);
    uint8_t requestFrom(uint8_t address, uint8_t count, uint8_t stop = true);
    int available();
    int read();
};
extern TwoWire Wire;
