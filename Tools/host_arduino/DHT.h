#pragma once
#include "Arduino.h"

constexpr uint8_t DHT11 = 11;
struct DHT {
    DHT(uint8_t pin, uint8_t type, uint8_t count = 6);
    void begin(uint8_t pullTime = 55);
    float readTemperature(bool fahrenheit = false, bool force = false);
    float readHumidity(bool force = false);
};
