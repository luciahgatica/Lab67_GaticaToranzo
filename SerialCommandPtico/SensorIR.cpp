#include "HardwareSerial.h"
#include "Arduino.h"
#include <AccelStepper.h>
#include "SensorIR.h"

SensorIR::SensorIR(uint8_t sensor_pin):
  m_sensor_pin(sensor_pin) {}

/// ¿Es necesario sacar la redundante del init o del constructor?

void SensorIR::init()
{
  pinMode(m_sensor_pin, OUTPUT);
}

void SensorIR::runtime() {}

int SensorIR::querySignal()
{
    Serial.println(analogRead(m_sensor_pin));
    return analogRead(m_sensor_pin);
}

