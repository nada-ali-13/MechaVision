#pragma once
#include "Wire.h"

struct Adafruit_BME280 {
    bool begin(uint8_t address = 0x77, TwoWire *wire = &Wire);
    float readTemperature();
    float readHumidity();
    float readPressure();
};
