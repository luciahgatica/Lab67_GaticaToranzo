#include "Arduino.h"
#include <AccelStepper.h>
#ifndef SensorIR_h
#define SensorIR_h

class SensorIR
{
  public:

    SensorIR(uint8_t sensor_pin);

    void init();
    void runtime(void);
    int querySignal();

  private:

    uint8_t m_sensor_pin;
};


#endif
