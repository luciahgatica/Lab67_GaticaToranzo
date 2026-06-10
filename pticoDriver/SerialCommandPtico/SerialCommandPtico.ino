
///////////////////////////
// Revisado 08-06-26 /////
//////////////////////////

/// 18-05. Agregado comentarios. 
/// 27-05. Agregadas las funciones para el motor. 
/// 08-06. Limpiado de codigos y agregado una copia para referenciar

#include <Arduino.h>

/// inodriver_bridge habilita la comunicación con el puerto serie. 
/// inodriver_user habilita la comunicación con el usuario.

#include "inodriver_bridge.h"
#include "inodriver_user.h"

#define BAUD_RATE 9600


void setup() {
  Serial.begin(BAUD_RATE);
  bridge_setup();
  user_setup();
  Serial.println("Chanoscopio");
}

void loop() {
  delay(1);
  bridge_loop();
  user_loop();
}