#include "Arduino.h"
#include <AccelStepper.h>
#ifndef Motor_h
#define Motor_h

class Motor
{
  public:

    Motor(uint8_t step_pin,
          uint8_t dir_pin,
          float max_speed,
          float acceleration);

    void init();

    void runtime(void);

    void moveRelative(long steps);

    void moveAbsolute(long position);

    void setCurrentPositionAsZero();

    long queryPosition();

    void moveToZero();

  private:

    uint8_t m_step_pin;

    uint8_t m_dir_pin;

    float m_max_speed;

    float m_acceleration;

    AccelStepper m_stepper;
};


#endif
