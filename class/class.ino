// === PARÁMETROS DEL MOTOR ===
const int pasosPorRevolucion = 200;      // 200 pasos = 360°
const float pasosPorGrado = pasosPorRevolucion / 360.0;
const int velocidadParking = 50;          // pasos/seg durante el homing
const int velocidadNormal = 200;         // velocidad para movimientos normales
const int aceleracionNormal = 100;       // aceleración básica


// 27/11/2025. Creada la clase Motor. Agregado void setear, setearParking, moverAGrado.

class Motor{
  public:
    // Constructor. Se inicia con cada llamada de la clase
    Motor(int stepPin, int dirPin, int pasosPorRev)
        : stepper(AccelStepper::DRIVER, stepPin, dirPin), //Inicializa stepper con su constructor.
          pasosPorGrado(pasosPorRev /360.0)               //Inicializa pasos por grado.
    {}

    //Setea velocidad máxima y aceleración. 
    void setear(int vel, int acel) {
      stepper.setMaxSpeed(vel);
      stepper.setAcceleration(acel);
    }

    //Setea velocidad máxima y aceleración del parking. ¿Pasar a otra clase?  
    void setearParking(int vel, int acel) {
      stepper.setMaxSpeed(vel);
      stepper.setAcceleration(acel);
    }

    // Mover el motor a tantos grados de su posición inicial con velocidad fija.
    void moverAGrado(float anguloDestino) {
      long pasosDestino = anguloDestino * pasosPorGrado;
      stepper.moveTo(pasosDestino)
      while (stepper.distanceToGo() != 0) {
        stepper.run();
      }
    // Agregar un guardado de posiciones. 
    }

    void moverUnPaso(int direccion) {
      stepper.moveTo(stepper.currentPosition() + direccion);
      stepper.runToPositon();
    }

    long posicionPasos() {
      return stepper.currentPosition();
    }         
  }
  private:
    AccelStepper s

};