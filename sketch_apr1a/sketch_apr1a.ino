// Código de prueba para probar accelstepper

#include <AccelStepper.h> // importa el paquete

AccelStepper stepper(AccelStepper::DRIVER, 50, 48); // dice el tipo de driver que manejamos y los pines STEP y DIR respectivamente 

long zeroOffset = 0; // solo es necesario si utilizo un cero que sea distinto al del contador interno.

void setup() {
  stepper.setMaxSpeed(1000);   // pasos por segundo, se puede setear
  stepper.setAcceleration(200); // pasos/seg^2, se puede setear
  
  // Al inicio fijamos el cero
  stepper.setCurrentPosition(0); // setCurrentPosition(long position) setea la posición donde está el motor como pasos. Como efecto setea la current velocity a 0. 
  // zeroOffset = stepper.currentPosition(); // esto es necesario si nuestro cero físico está lejos del offset interno

}

void loop() {
  moveRelativeToZero(500);
  while (stepper.distanceToGo() != 0) {  // stepper.distanceToGo() devuelve cuántos apasos faltan para llegar al destino. Mientras no sea 0, seguimos llamando a stepper.run()
    stepper.run();                      // stepper.run() hace avanzar al motor de a pequeños pasos según la velocidad y aceleración definidas.
  }

  delay(100);

  moveRelativeToZero(0);
  while (stepper.distanceToGo() != 0) {
    stepper.run();
  }

  delay(200);
}

void moveRelativeToZero(long pos){
  stepper.moveTo(zeroOffset + pos);  // moveTo((long) absolute_position) mueve el motor una posición según el contador interno.
}