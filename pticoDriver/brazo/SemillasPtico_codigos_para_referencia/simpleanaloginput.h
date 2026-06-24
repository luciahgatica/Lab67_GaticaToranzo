#include "Arduino.h"
#ifndef __SimpleAnalogInput__
#define __SimpleAnalogInput__
#include "Wire.h"

#define SAI_BUFFER_SIZE 255

class SimpleAnalogInput
{
  public:
    SimpleAnalogInput(uint8_t, uint8_t);
    void init();
    void runtime(void);
    void zeroBuffer(void);
    void acquire(uint32_t);
    void BufferToSerial(void);

  private:
    uint8_t m_ch_a_pin;
    uint8_t m_ch_b_pin;
    byte m_ch_a_data[SAI_BUFFER_SIZE];
    byte m_ch_b_data[SAI_BUFFER_SIZE];
};

#endif
