#include "HardwareSerial.h"
#include "Arduino.h"
#include "aioswitch.h"

AIOSwitch::AIOSwitch(uint8_t input_relay_ctrl_pin, uint8_t input_relay_conn_state, uint8_t output_relay_ctrl_pin, uint8_t output_relay_conn_state, unsigned long delay_millis) : 
                     m_input_relay_ctrl_pin(input_relay_ctrl_pin), 
                     m_input_relay_conn_state(input_relay_conn_state), 
                     m_output_relay_ctrl_pin(output_relay_ctrl_pin), 
                     m_output_relay_conn_state(output_relay_conn_state), 
                     m_delay_millis(delay_millis)
{

}

void AIOSwitch::init()
{
    pinMode(m_input_relay_ctrl_pin, OUTPUT);
    pinMode(m_output_relay_ctrl_pin, OUTPUT);
    setMode(disabled);
}

void AIOSwitch::runtime() {}

void AIOSwitch::connectInput(bool value) {
  if (value) {
    digitalWrite(m_input_relay_ctrl_pin, m_input_relay_conn_state);
  } else {
    digitalWrite(m_input_relay_ctrl_pin, !m_input_relay_conn_state);
  }
}

void AIOSwitch::connectOutput(bool value) {
  if (value) {
    digitalWrite(m_output_relay_ctrl_pin, m_output_relay_conn_state);
  } else {
    digitalWrite(m_output_relay_ctrl_pin, !m_output_relay_conn_state);
  }
}

void AIOSwitch::setMode(AIOMode mode) {
  if (mode == disabled) {
    connectOutput(false);
    connectInput(false);
  } else if (mode == input) {
    connectOutput(false);
    delay(m_delay_millis);
    connectInput(true);
  } else if (mode == output) {
    connectInput(false);
    delay(m_delay_millis);
    connectOutput(true);
  }
}

