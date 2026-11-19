#pragma once
#include "Wire.h"

struct Adafruit_BMP280 {
    Adafruit_BMP280(TwoWire *wire = &Wire);
    bool begin(uint8_t address = 0x77, uint8_t chipId = 0x58);
    float readPressure();
    float readAltitude(float seaLevelhPa = 1013.25f);
};
