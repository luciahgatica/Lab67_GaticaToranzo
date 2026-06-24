#include "Arduino.h"
#ifndef LedController_h
#define LedController_h

class LedController
{
  public:

    LedController(uint8_t LED_pin);

    void init();

    void runtime(void);

    void LedIntensity(int intensity);

    void LedTurnOff();

  private:
    uint8_t m_LED_pin;
};

#endif
