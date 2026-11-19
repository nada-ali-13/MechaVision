#pragma once
#include "Arduino.h"

struct LiquidCrystal : Print {
    LiquidCrystal(uint8_t rs, uint8_t enable, uint8_t d4, uint8_t d5, uint8_t d6, uint8_t d7);
    void begin(uint8_t columns, uint8_t rows);
    void clear();
    void setCursor(uint8_t column, uint8_t row);
};
