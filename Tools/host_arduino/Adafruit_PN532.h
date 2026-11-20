#pragma once
#include "Wire.h"

constexpr uint8_t PN532_MIFARE_ISO14443A = 0;
struct Adafruit_PN532 {
    Adafruit_PN532(uint8_t irq, uint8_t reset, TwoWire *wire = &Wire);
    void begin();
    uint32_t getFirmwareVersion();
    bool SAMConfig();
    bool setPassiveActivationRetries(uint8_t retries);
    bool readPassiveTargetID(uint8_t type, uint8_t *uid, uint8_t *length, uint16_t timeout = 0);
};
