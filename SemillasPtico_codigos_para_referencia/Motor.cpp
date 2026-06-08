#include "HardwareSerial.h"
#include "Arduino.h"
#include <AccelStepper.h>
#include "Motor.h"

Motor::Motor(uint8_t step_pin,
             uint8_t dir_pin,
             float max_speed,
             float acceleration)

  :

  m_step_pin(step_pin),
  m_dir_pin(dir_pin),
  m_max_speed(max_speed),
  m_acceleration(acceleration),

  m_stepper(AccelStepper::DRIVER,
            step_pin,
            dir_pin)

{
    m_stepper.setMaxSpeed(m_max_speed);
    m_stepper.setAcceleration(m_acceleration);
}

/// ¿Es necesario sacar la redundante del init o del constructor?

void Motor::init()
{
  pinMode(m_dir_pin, OUTPUT);
  pinMode(m_step_pin, OUTPUT);

  m_stepper.setMaxSpeed(m_max_speed);
  m_stepper.setAcceleration(m_acceleration);
}

void Motor::runtime(){}

void Motor::moveRelative(long steps)
{
  m_stepper.moveTo(m_stepper.currentPosition() + steps);
  while (m_stepper.distanceToGo() != 0) {
    m_stepper.run();
  }
}

void Motor::moveAbsolute(long position)
{
  m_stepper.moveTo(position);
  while (m_stepper.distanceToGo() !=0) {
    m_stepper.run();
  }
}

void Motor::setCurrentPositionAsZero()
{
  m_stepper.setCurrentPosition(0);
}

void Motor::moveToZero()
{
 m_stepper.moveTo(0);
 while (m_stepper.distanceToGo() != 0) {
  m_stepper.run();
 }
}

long Motor::queryPosition()
{
  // Serial.println(m_stepper.currentPosition());
  return m_stepper.currentPosition();
}

