#include "Arduino.h"
#ifndef __AIOSWITCH__
#define __AIOSWITCH__
#include "Wire.h"

//#define MPU_ADDR 0x68

enum AIOMode {
  disabled,
  input,
  output,
};


class AIOSwitch
{
  public:
    AIOSwitch(uint8_t, uint8_t, uint8_t, uint8_t, unsigned long);
    void init();
    void runtime(void);

    void connectInput(bool);
    void connectOutput(bool);

    void setMode(AIOMode);

  private:
    uint8_t m_input_relay_ctrl_pin;
    uint8_t m_output_relay_ctrl_pin;
    uint8_t m_input_relay_conn_state;
    uint8_t m_output_relay_conn_state;

    unsigned long m_delay_millis;
    
    AIOMode m_aio_mode;
};

#endif
