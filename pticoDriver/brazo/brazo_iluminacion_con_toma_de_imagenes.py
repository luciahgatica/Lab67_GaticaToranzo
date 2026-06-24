import time
import pathlib
from driver_imperx import ky, ImperxCamera, guardar_imagenes, guardar_imagenes_parciales
from serial import Serial
#from illumination import IlluminationDriver
from SerialCommunication import Drivers
from time import sleep

t_inicio = time.time()
# ========== CONFIGURACIÓN ==========
ROOT = '/home/chanoscopio/Documents/AleYLu/imagenes_tomadas/2026-06-05-b' #'[LucasC/code/ptyco-full-simulator/test/imagenes_tomadas/2025-09-30'

GANANCIA = 1.0
N_IMAGENES = 2
PUERTO_ARDUINO = "/dev/ttyACM0"

# Inicialización cámara
project = pathlib.Path('/home/chanoscopio/Documents/LucasC/Prueba3.fgprj')
roi_nuestro = ((0,0), (6608, 6608))#((1564,2736), (5436, 6608))
handle = ky.KYFG_Init()
imperx = ImperxCamera(roi=roi_nuestro, n_frames=N_IMAGENES, project_file=project)
imperx.pixel_format = "Mono12"
imperx.gain = GANANCIA

# Inicialización LEDs
driver = Drivers(port=PUERTO_ARDUINO)

# ========== BUCLE LED + FOTO OPTIMIZADO ==========
todas_las_imagenes = []
limite_memoria = 500  # guarda cada 100 imágenes

#############################
# Prueba matriz
#############################

# =============================================================================
# LEDS_POR_TIEMPO = {
#  3000: [(17, 15), (16, 15), (18, 15)],
#  4000: [(16, 14), (16, 16), (17, 13), (17, 14), (17, 16), (18, 13), (18, 14), (18, 16), (19, 14), (19, 15)],
#  5000: [(19, 16)],
#  6000: [(16, 13), (17, 17), (19, 13)],
#  7000: [(18, 17), (15, 15)],
#  8000: [(20, 15), (15, 14)],
#  9000: [(20, 14), (16, 17)],
#  10000: [(19, 17), (17, 12), (15, 16)],
#  11000: [(20, 16), (18, 12), (14, 14)],
#  14000: [(19, 12), (16, 12), (20, 13), (15, 13), (14, 15), (15, 17), (21, 14), (21, 16)],
#  21000: [(17, 18), (20, 17), (18, 18), (21, 15), (14, 13), (14, 16), (15, 12), (17, 11), (19, 11), (21, 13), (22, 15)],
#  28000: [(16, 18), (18, 11), (19, 18), (20, 12), (13, 14), (13, 15), (13, 16), (14, 12), (14, 17), (15, 18), (16, 11), (20, 18), (21, 17), (22, 14), (22, 16)],
#  35000: [(15, 11), (19, 19), (20, 11), (21, 12), (13, 17)],
#  42000: [(13, 13), (14, 18), (18, 10), (22, 13)],
#  49000: [(17, 10), (19, 10), (23, 15)],
#  56000: [(20, 19), (13, 12), (16, 10), (18, 19), (21, 11), (22, 17), (12, 16)],
#  63000: [(12, 14), (12, 15), (14, 11), (15, 19), (16, 19), (17, 19), (22, 12), (23, 14), (23, 16)],
#  70000: [(12, 13), (13, 18), (21, 18)],
#  98000: [(12, 12), (12, 17)],
#  112000: [(13, 11), (23, 13)],
#  119000: [],
#  140000: [(14, 19), (15, 9), (15, 10), (22, 11), (23, 12)],
#  147000: [(11, 16), (14, 10), (20, 10)],
#  154000: [(11, 15), (17, 20), (18, 20), (19, 20), (23, 17)],
#  175000: [(11, 14), (16, 20), (17, 9), (21, 19), (22, 18)],
#  182000: [(11, 17), (13, 19), (15, 20), (16, 9)],
#  210000: [(11, 13), (12, 11), (12, 18), (18, 9), (14, 9), (19, 9), (21, 10)],
#  280000: [(14, 20), (20, 20), (22, 19)],
#  350000: [(20, 9), (22, 10), (23, 18), (23, 11)],
#  420000: [(11, 18), (12, 19), (13, 10), (16, 21), (21, 20)],
#  490000: [(11, 10)],
#  540000: [(13, 20)],
#  630000: [(11, 11), (11, 12), (18, 21), (21, 9)],
#  700000: [(12, 10), (15, 21), (17, 21), (19, 21), (23, 20)],
#  800000: [(11, 19), (12, 20), (13, 9), (20, 21), (22, 20), (23, 19)],
#  900000: [(11, 20), (21, 21), (23, 10)],
#  1000000: [(11, 9), (11, 21), (12, 9), (12, 21), (13, 21), (14, 21), (22, 9), (22, 21), (23, 9), (23, 21)]
#  }
# 
# EXPOSICIONES = list(LEDS_POR_TIEMPO.keys())
#   # en microsegundos (100ms)
# imperx.exposure_time = EXPOSICIONES[0]
# 
# 
# for tiempo in EXPOSICIONES:
# 
#     imperx.set_gain_exposure(GANANCIA, int(round(tiempo, 1)))
# 
#     lista_leds = LEDS_POR_TIEMPO.get(tiempo, [])
# 
#     for fila, columna in lista_leds:
#         for color in ['r', 'g', 'b']:
#             driver.turn_on_led(fila, columna, color)
#             time.sleep(0.05)
# 
#             imagenes = imperx.obtener_imagenes(N_IMAGENES)
# 
#             for idx, img in enumerate(imagenes):
#                 todas_las_imagenes.append((fila, columna, color, tiempo, idx, img))
# 
#                 if len(todas_las_imagenes) >= limite_memoria:
#                     guardar_imagenes_parciales(todas_las_imagenes, ROOT)
#                     todas_las_imagenes.clear()
# 
#             driver.turn_off_leds()
# =============================================================================

#############################
# Prueba brazo
#############################

LEDS_POR_TIEMPO = {
     3000: [(1, 1)]
}

EXPOSICIONES = list(LEDS_POR_TIEMPO.keys())
  # en microsegundos (100ms)
imperx.exposure_time = EXPOSICIONES[0]

for tiempo in EXPOSICIONES:

    imperx.set_gain_exposure(GANANCIA, int(round(tiempo, 1)))

    lista_leds = LEDS_POR_TIEMPO.get(tiempo, [])
    paso_0 = driver.get_motor_angle()
    
    for paso, led in lista_leds:
        paso_1 = paso
        if paso_0 != paso_1:
            driver.rotate(paso)
            time.sleep(0.005)
            
        driver.turn_on_led_i(led)
        time.sleep(0.05)

        imagenes = imperx.obtener_imagenes(N_IMAGENES)

        for idx, img in enumerate(imagenes):
            todas_las_imagenes.append((led, paso, tiempo, idx, img))

            if len(todas_las_imagenes) >= limite_memoria:
                guardar_imagenes_parciales(todas_las_imagenes, ROOT)
                todas_las_imagenes.clear()

        driver.turn_off_leds()
        paso_0 = paso_1

# Guardar lo que quede al final (menos de 100)
if todas_las_imagenes:
    guardar_imagenes_parciales(todas_las_imagenes, ROOT)
    todas_las_imagenes.clear()

t_fin = time.time()
duracion = t_fin - t_inicio
minutos = duracion // 60
segundos = duracion % 60
print(f"⏱️ Proceso completado en {int(minutos)} min {int(segundos)} s")

print("Proceso completado, todas las imágenes guardadas.")
