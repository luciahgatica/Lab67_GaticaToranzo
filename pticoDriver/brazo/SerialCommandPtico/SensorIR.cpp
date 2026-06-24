#include "HardwareSerial.h"
#include "Arduino.h"
#include <AccelStepper.h>
#include "SensorIR.h"

SensorIR::SensorIR(uint8_t sensor_pin):
  m_sensor_pin(sensor_pin) {}

void SensorIR::init()
{
  Serial.begin(9600);
}

void SensorIR::runtime() {}

int SensorIR::querySignal()
{
    return analogRead(m_sensor_pin);
}

