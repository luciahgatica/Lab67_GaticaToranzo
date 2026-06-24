import time
import random
from serial import Serial
from typing import List, Dict, Literal
from abc import ABC, abstractmethod

import serial.tools.list_ports

puertos = serial.tools.list_ports.comports()
for puerto in puertos:
    print(puerto.device, puerto.description)

t_inicio = time.time()

BAUDRATE = 9600 # 115200 

#############################
# Motor
#############################

class Motor(ABC):
    microsteps: int = 1
    steps: int = 200

    @abstractmethod
    def __init__(self, port: str):
        self.min_angle = 360 / (self.microsteps * self.steps)
        pass

    @abstractmethod
    def clean_serial(self):
        pass

    @abstractmethod
    def rotate(self, steps: int):
        pass

    @abstractmethod
    def set_rpm(self, velocity: float, acceleration : float):
        pass

    @abstractmethod
    def get_motor_angle(self):
        pass

    @abstractmethod
    def set_origin(self):
        pass

#############################
# LEDs
#############################
    
class Illumination(ABC):
    @abstractmethod
    def __init__(self, port: str):
        pass

    @abstractmethod
    def turn_on_led_i(self, LED: int, STEP: int):
        pass

    @abstractmethod
    def intensity_led_i(self, LED: int, STEP: int, intensity: int, time: int = 0):
        pass
 
    @abstractmethod
    def turn_off_led_i(self, LED : int):
       pass

    @abstractmethod
    def turn_off_leds(self, LEDs : int):
        pass
    
#############################
# IR sensor
#############################
    
class Detection(ABC):
    @abstractmethod
    def __init__(self, port: str):
        pass

    @abstractmethod
    def signal_read():
        pass

    
#############################
# Protocols
#############################

class Drivers(Motor, Illumination, Detection):
    def __init__(self, port: str): # Agregamos los pines de LEDs??
        super().__init__(port)
        self._port = port
        self._baudrate = BAUDRATE
        self._serial = self._open_serial()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.turn_off_leds(1)
        self.close()

    def __del__(self):
        self.turn_off_leds(1)

    def _open_serial(self) -> Serial:
        """ Opens a serial port between Arduino and Python """

        serial = Serial(port=self._port, baudrate=self._baudrate, timeout=1)
        msg = ""
        start_time = time.time()
        while not msg.startswith("Chanoscopio"):
            try:
                print(repr(msg))
                msg = serial.readline().decode('utf-8')
            except UnicodeDecodeError:
                pass
            if time.time() - start_time > 15:
                raise TimeoutError("Arduino is not responding")
        return serial # Hace el protocolo de parking como está definido en SerialCommandPtico.ino antes de devolver el control
    
    def close(self):
        self._serial.close()

    # Motor specific functions

    def rotate(self, steps):
        self._serial.write(f"STEP {steps}\n".encode("ascii"))
        response = self._serial.readline().decode("ascii")
        return response
    
    def clean_serial(self): # Verificar si funciona
        while self._serial.in_waiting:
            self._serial.readline().decode('ascii')

    def get_motor_angle(self):
        #self.clean_serial()
        self._serial.write("POS?\n".encode('ascii'))
        response = self._serial.readline().decode('ascii')
        return response
    
    def set_origin(self):
        self._serial.write("ZERO\n".encode("ascii"))
        response = self._serial.readline().decode("ascii")
        return response
    
    def set_rpm(self, velocity, acceleration):
        pass
    
    # LED controller specific functions
    
    def turn_on_led_i(self, i):
        self._serial.write(f"INTENSITY{i} 254\n".encode("ascii"))
        response = self._serial.readline().decode("ascii")
        return response
    
    def intensity_led_i(self, led_index, intensity):
        self._serial.write(f"INTENSITY{led_index} {intensity}\n".encode("ascii"))
        response = self._serial.readline().decode("ascii")
        return response
    
    def turn_off_led_i(self, led_index):
        self._serial.write(f"TURNOFFLED{led_index}\n".encode("ascii"))
        response = self._serial.readline().decode("ascii")
        return response
    
    def turn_off_leds(self, total_leds):
        for led_index in range(total_leds):
            self.turn_off_led_i(led_index)
    
    # IR sensor specific functions

    def signal_read(self):
        self.clean_serial()
        self._serial.write("SENSOR?\n".encode("ascii"))
        response = self._serial.readline().decode("ascii")
        return response
        
#############################
# Pruebas
#############################


delay = 0.0005

if __name__ == "__main__":
    system = Drivers(port="COM4")#"/dev/ttyACM0")
    time.sleep(delay)
    response = system.get_motor_angle()
    print(f"POS: {response}")
    time.sleep(delay)
    print("Sensor detects : ", system.signal_read())
    

t_fin = time.time()
duracion = t_fin - t_inicio
minutos = duracion // 60
segundos = duracion % 60
print(f"⏱️ Proceso completado en {int(minutos)} min {int(segundos)} s")

print("Proceso completado, todas las imágenes guardadas.")