#include "HardwareSerial.h"
#include "Arduino.h"
#include "dephased_pwm.h"

#define PRESCALER 1
#define PRESCALER_BITS 0x01

#define CLK 16000000UL    // Default clock speed is 16MHz on Arduino Uno

// macro for detection of rising edge and debouncing
/*the state argument (which must be a variable) records the current
  and the last 7 reads by shifting one bit to the left at each read.
  If the value is 15(=0b00001111) we have one rising edge followed by
  4 consecutive 1's. That would qualify as a debounced rising edge*/
#define DRE(signal, state) (state=(state<<1)|signal)==B00001111

// macro for detection of falling edge and debouncing
/*the state argument (which must be a variable) records the current
  and the last 7 reads by shifting one bit to the left at each read.
  If the value is 240(=0b11110000) we have one falling edge followed by
  4 consecutive 0's. That would qualify as a debounced falling edge*/
#define DFE(signal, state) (state=(state<<1)|signal)==B11110000


void adjust_shift(int shift_value)
{
  TCCR1B = 0x18; // DISABLE Timer Clock
 
  OCR1B = shift_value; // Pass back changed Phase value
 
  TCNT1 = 0; // reset Counter
  TCCR1A = 0xA0; // Set Compare-Match bit-fields for Clear-on-Match
  TCCR1C = 0xC0; // Force Output Compares -- Clears Channel-AB Waveform Outputs!
  TCCR1A = 0x50; // Set Compare Match bit-fields for Toggle-on-Match

  TCCR1B |= 1; // Prescale=1, ENABLE Timer1 Clock
}

DephasedPWM::DephasedPWM(uint8_t pwm_a_pin, uint8_t pwm_b_pin, uint8_t invert_mode_pin, uint8_t phase_pin, uint8_t pause_pin, uint8_t phase_trigger_pin, uint8_t phase_changing_pin) 
  : m_pwm_a_pin(pwm_a_pin), m_pwm_b_pin(pwm_b_pin), m_invert_mode_pin(invert_mode_pin), m_phase_pin(phase_pin), m_pause_pin(pause_pin), m_phase_trigger_pin(phase_trigger_pin), m_phase_changing_pin(phase_changing_pin)
{

};

void DephasedPWM::init()
{
    pinMode(m_pwm_a_pin, OUTPUT);
    pinMode(m_pwm_b_pin, OUTPUT);
    pinMode(m_invert_mode_pin, OUTPUT);

    pinMode(m_phase_trigger_pin, INPUT);
    pinMode(m_phase_changing_pin, OUTPUT);

    setFrequency(m_frequency);
    setMode(fixed);
    setPhase(0);
}


DephasedPWM::setFrequency(uint32_t frequency) {
    m_clocks_per_toggle = (CLK / frequency) / 2;
    m_frequency = frequency;

    TCCR1B = 0x18; // 0001 1000, Disable Timer
    TCCR1A = 0x50; // 0101 0000

    ICR1 = m_clocks_per_toggle;

    OCR1A = 1;
    OCR1B = 1;
    TCNT1=0x0;

    TCCR1A = 0xA0; // FOC setup to clear Wavegen output flops
    TCCR1C = 0xC0; // FOC strobe
    TCCR1A = 0x50; // 0101 0000

    TCCR1B |= 1; // Prescale=1, Enable Timer
}

DephasedPWM::setMode(PhaseControlMode mode) {
  m_phase_control_mode = mode;
  m_paused = false;
}

DephasedPWM::setPhase(uint16_t phase) {
  m_fixed_phase = phase;
}

DephasedPWM::setDelta(int16_t delta) {
  m_delta_phase = delta;
}

DephasedPWM::setTimeStep(int16_t timestep) {
  m_timestep = timestep;
}

DephasedPWM::setStepsBidir(int16_t steps) {
  if (steps > 0) {
    m_bidir_current = 0;
    m_bidir_steps = steps;
    m_bidir_enabled = true;
  } else {
    m_bidir_enabled = false;
  }

}


void DephasedPWM::runtime()
{
  boolean is_paused = m_paused || digitalRead(m_pause_pin);
  // first deal with commands insensitive to pause
  if (m_phase_control_mode == fixed) {
    update_phase(m_fixed_phase);
  }
  if (is_paused) {
    return;
  }
  switch (m_phase_control_mode) {
    case external: // 1
      update_phase(360. / 1024. * analogRead(m_phase_pin));
      break;
    case timed: // 2
      if ((millis() - m_last_phase_change_millis) > m_timestep) {
        next_phase();
      }
      break;
    case triggered: // 3
      //Serial.println("Hola!");
      //Serial.println(digitalRead(m_phase_trigger_pin));
      // TODO: For some extrange reason, if you remove the next line it never goes 
      // inside the if. 
      Serial.println(m_phase_trigger_state);
      if (DFE(digitalRead(m_phase_trigger_pin), m_phase_trigger_state)) {
        // TODO: the delay is need to make a pulse consistent. Maybe there is a way to make it shorter but stable?
        delay(50);
        next_phase();
      }
      break;
  }
}

void DephasedPWM::next_phase() {
  update_phase(m_current_phase + m_delta_phase);
  if (!m_bidir_enabled) {
    return;
  }
  if (m_bidir_current > m_bidir_steps) {
    m_bidir_current = 0;
    m_delta_phase = -m_delta_phase;
  } else {
    m_bidir_current += 1;
  }
}

void DephasedPWM::update_phase(float phase_degrees) {
  digitalWrite(m_phase_changing_pin, HIGH);

  if (phase_degrees < 0) {
    return update_phase(360 + phase_degrees);
  }
  int in_circle_phase = round(phase_degrees) % 360;
  int in_half_circle_phase = in_circle_phase % 180;
  int ipart = floor(phase_degrees / 180.0);
  
  if (ipart % 2) {
    digitalWrite(m_invert_mode_pin, LOW); // invert
  } else {
    digitalWrite(m_invert_mode_pin, HIGH);  // do not invert
  };
  
  in_half_circle_phase = 180 - in_half_circle_phase;
  adjust_shift(m_clocks_per_toggle * in_half_circle_phase / 180);
  m_current_phase = in_circle_phase;

  digitalWrite(m_phase_changing_pin, LOW);

  m_last_phase_change_millis = millis();
}

void DephasedPWM::pause() {
  m_paused = true;
}