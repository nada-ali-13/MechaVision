#pragma once

// Declarations for host C++ syntax checking only. No AVR code or hardware is simulated.
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstdlib>

using byte = uint8_t;
using boolean = bool;
using std::isnan;
using std::round;
constexpr uint8_t LOW = 0, HIGH = 1;
constexpr uint8_t INPUT = 0, OUTPUT = 1, INPUT_PULLUP = 2;
constexpr uint8_t A0 = 14, A1 = 15, A2 = 16, A3 = 17, A4 = 18, A5 = 19;
constexpr uint8_t CHANGE = 1, FALLING = 2, RISING = 3;
constexpr uint8_t MSBFIRST = 1, LSBFIRST = 0;
constexpr float PI = 3.14159265f;
struct __FlashStringHelper;
#define F(text) (reinterpret_cast<const __FlashStringHelper *>(text))
#define min(a, b) ((a) < (b) ? (a) : (b))
#define max(a, b) ((a) > (b) ? (a) : (b))
#define constrain(x, low, high) ((x) < (low) ? (low) : ((x) > (high) ? (high) : (x)))

void pinMode(uint8_t, uint8_t);
void digitalWrite(uint8_t, uint8_t);
int digitalRead(uint8_t);
void analogWrite(uint8_t, int);
int analogRead(uint8_t);
unsigned long millis();
unsigned long micros();
void delay(unsigned long);
void delayMicroseconds(unsigned int);
unsigned long pulseIn(uint8_t, uint8_t, unsigned long = 1000000UL);
void tone(uint8_t, unsigned int, unsigned long = 0);
void noTone(uint8_t);
long map(long, long, long, long, long);
long random(long);
long random(long, long);
void randomSeed(unsigned long);
uint8_t digitalPinToInterrupt(uint8_t);
void attachInterrupt(uint8_t, void (*)(), int);
void detachInterrupt(uint8_t);
void interrupts();
void noInterrupts();
uint8_t shiftIn(uint8_t, uint8_t, uint8_t);
void shiftOut(uint8_t, uint8_t, uint8_t, uint8_t);

struct Print {
    size_t print(const __FlashStringHelper *);
    size_t print(const char *);
    size_t print(char);
    size_t print(unsigned char, int = 10);
    size_t print(int, int = 10);
    size_t print(unsigned int, int = 10);
    size_t print(long, int = 10);
    size_t print(unsigned long, int = 10);
    size_t print(double, int = 2);
    size_t println();
    template<class T> size_t println(T value) { return print(value); }
    template<class T> size_t println(T value, int format) { return print(value, format); }
    size_t write(uint8_t);
};

struct HardwareSerial : Print {
    void begin(unsigned long);
    void setTimeout(unsigned long);
    long parseInt();
    int available();
    int read();
};
extern HardwareSerial Serial;
