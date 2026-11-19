#pragma once
#include "Arduino.h"

struct SoftwareSerial : HardwareSerial {
    SoftwareSerial(uint8_t rx, uint8_t tx, bool inverseLogic = false);
};
