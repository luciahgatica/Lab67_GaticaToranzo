// Este código define dos funciones. Ahora mismo lo que hace es separar los 360° en giros de 30°; luego gira 360° en el sentido contrario.
#define DIR 48
#define STEP 50 
#define PWM 8

void setup() {
  // put your setup code here, to run once:
  pinMode(DIR, OUTPUT); // dir
  pinMode(STEP, OUTPUT); // step
  pinMode(PWM, OUTPUT); // PWM
}

// HIGH sentido horario, LOW sentido antihorario. 

void angulo_con_sentido(int angulo, bool direccion) {
  digitalWrite(DIR, direccion ? HIGH : LOW); // ? funciona como un if del bool, en este caso tira HIGH si true
  float pasosExactos = (200.0*angulo)/360.0 ;
  int pasos = round(pasosExactos);
  for (int i = 0; i < pasos; i = i + 1) {
    digitalWrite(STEP, HIGH);
    delayMicroseconds(1000);
    digitalWrite(STEP, LOW);
    delayMicroseconds(1000);
  }
}

void angulo_con_direccion_vuelta(int angulo, bool direccion) {
  int numero_de_veces = 360/angulo;
  for (int i = 0; i < numero_de_veces; i = i + 1){
    analogWrite(PWM, 200);
    angulo_con_sentido(angulo, direccion);
    delay(500);
    analogWrite(PWM, 0);
  }
}

void loop() {
  //angulo_con_direccion_vuelta(30, true);
  analogWrite(PWM, 10);
  delayMicroseconds(100);
  analogWrite(PWM, 0);
  delayMicroseconds(200);
  //angulo_con_sentido(360, false);
}
