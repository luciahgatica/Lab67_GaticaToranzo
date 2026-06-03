#include "Arduino.h"
#include "Motor.h"
#include "SensorIR.h"
#include "LedController.h"
#ifndef Parking_h
#define Parking_h

class Parking
{
  public:
  Parking(Motor& motor, SensorIR& sensor);

  bool Execute();
  private:
  Motor& m_motor;
  SensorIR& m_sensor;
};

#endif