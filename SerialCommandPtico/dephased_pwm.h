#include "Arduino.h"
#ifndef __DEPHASED_PWM__
#define __DEPHASED_PWM__
#include "Wire.h"

//#define MPU_ADDR 0x68

enum PhaseControlMode {
  fixed,
  external,
  timed,
  triggered,
};


class DephasedPWM
{
  public:
    DephasedPWM(uint8_t, uint8_t, uint8_t, uint8_t, uint8_t, uint8_t, uint8_t);
    void init();
    void runtime(void);

    int16_t setFrequency(uint32_t);
    int16_t setMode(PhaseControlMode);
    int16_t setPhase(uint16_t);
    int16_t setDelta(int16_t);
    int16_t setTimeStep(int16_t);
    int16_t setStepsBidir(int16_t);
    void pause();

    void update_phase(float);
    void next_phase();

  private:
    uint8_t m_pwm_a_pin;
    uint8_t m_pwm_b_pin;
    uint8_t m_phase_pin;
    uint8_t m_invert_mode_pin;
    uint8_t m_pause_pin;
    uint8_t m_phase_trigger_pin;
    uint8_t m_phase_changing_pin;

    uint32_t m_frequency = 40000;
    uint16_t m_clocks_per_toggle;
    PhaseControlMode m_phase_control_mode;

    uint16_t m_fixed_phase = 0;
        
    // state
    unsigned long m_last_phase_change_millis = 0;
    float m_current_phase = -1;

    // Phase sequence
    int16_t m_timestep = 50;
    bool m_paused = false;
    int16_t m_delta_phase = 10;
    bool m_bidir_enabled = false;
    uint8_t m_bidir_steps = 5;
    uint8_t m_bidir_current = 0;

    byte m_phase_trigger_state = LOW;
};



#endif
