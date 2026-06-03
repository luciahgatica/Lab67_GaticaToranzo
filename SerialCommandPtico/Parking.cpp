#include "HardwareSerial.h"
#include "Arduino.h"
#include "Motor.h"
#include "SensorIR.h"
#include "LedController.h"
#include "Parking.h"

const uint8_t pinDir = 48;
const uint8_t pinStep = 50;
const uint8_t maxSpeed = 300.0;
const uint8_t acceleration = 100.0;
const uint8_t pinSensor = A11;

Motor motor(pinStep, pinDir, maxSpeed, acceleration);
SensorIR sensor(pinSensor);

void Parking_setup() {
  motor.init();
  sensor.init();
}

const int pasosPorRevolucion = 200;
const float pasosPorGrado = pasosPorRevolucion / 360.0;
float anguloActual = 0;
long posicionActualPasos = 0;
const int umbralSensor = 500; // si lectura > 500, estoy viendo algo brillante

