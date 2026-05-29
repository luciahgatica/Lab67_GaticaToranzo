#include "HardwareSerial.h"
#include "Arduino.h"


LedController::LedController(uint8_t LED_pin)
  :
  m_LED_pin(LED_pin) {}

void LedController::init()
{
  pinMode(m_LED_pin, OUTPUT);
}

void LedController::runtime(){}

void LedController::LedIntensity(int intensity)
{
  analogWrite(m_LED_pin, intensity);
}

void LedController::LedTurnOff()
{
  analogWrite(m_LED_pin, 0);
}