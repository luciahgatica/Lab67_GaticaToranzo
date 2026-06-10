#include "HardwareSerial.h"
#include "Arduino.h"
#include "Motor.h"
#include "SensorIR.h"
#include "LedController.h"
#include "Parking.h"

const int pasosPorRevolucion = 200;
const float pasosPorGrado = pasosPorRevolucion / 360.0;
float anguloActual = 0;
long posicionActualPasos = 0;
const int umbralSensor = 500; // si lectura > 500, estoy viendo algo brillante

Parking::Parking(
          Motor& motor,
          SensorIR& sensor) 
          : 
          m_motor(motor),
          m_sensor(sensor)
          
{
}

bool Parking::Execute() {
      m_motor.setCurrentPositionAsZero();

      while (m_motor.queryPosition() < 100){
            m_motor.moveRelative(1);
            int lecture = m_sensor.querySignal();

            if (lecture > 500){
                  m_motor.setCurrentPositionAsZero();
                  //Serial.print("Encontrado");
                  return true;
                  }
      }
      if (m_motor.queryPosition()  >= 100){
            m_motor.moveRelative(-50);
            m_motor.moveRelative(-50);

            while (m_motor.queryPosition() > -100){
                  m_motor.moveRelative(-1);
                  int lecture = m_sensor.querySignal();

                  if (lecture > 500){
                        m_motor.setCurrentPositionAsZero();
                        // Serial.print("Encontrado");
                        return true;
                        }
            }
      }     
      return false;
}