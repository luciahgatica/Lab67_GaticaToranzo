#include "HardwareSerial.h"
#include "Arduino.h"
#include "simpleanaloginput.h"

SimpleAnalogInput::SimpleAnalogInput(uint8_t ch_a_pin, uint8_t ch_b_pin) : m_ch_a_pin(ch_a_pin), m_ch_b_pin(ch_b_pin) {
    pinMode(m_ch_a_pin, OUTPUT);
    pinMode(m_ch_b_pin, OUTPUT);
    zeroBuffer();
}

void SimpleAnalogInput::init() {}

void SimpleAnalogInput::runtime() {}

void SimpleAnalogInput::zeroBuffer() {
  for (int i=0; i<SAI_BUFFER_SIZE; i++) {
    m_ch_a_data[i] = 0;
  }
}

void SimpleAnalogInput::acquire(uint32_t frequency) {
  unsigned long last_micros = micros();
  unsigned long period_micros = floor(1000000 / frequency);
  unsigned long delta_micros;

  for (int i=0; i<SAI_BUFFER_SIZE; i++) {
    m_ch_a_data[i] = analogRead(m_ch_a_pin);
    m_ch_b_data[i] = analogRead(m_ch_b_pin);
    delta_micros = micros() - last_micros;
    if (period_micros > delta_micros) {
      delayMicroseconds(period_micros - delta_micros);
    }
    last_micros = micros();
  }
}

void SimpleAnalogInput::BufferToSerial() {
  Serial.write(SAI_BUFFER_SIZE);
  Serial.write(",");
  Serial.write(2);
  Serial.write(",");
  for (int i=0; i<SAI_BUFFER_SIZE; i++) {
    Serial.write(",");
    Serial.write(m_ch_a_data[i]);
  }
  for (int i=0; i<SAI_BUFFER_SIZE; i++) {
    Serial.write(",");
    Serial.write(m_ch_b_data[i]);
  }
}

 
