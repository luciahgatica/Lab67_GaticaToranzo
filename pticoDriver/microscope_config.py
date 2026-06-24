import os 
os.chdir(r'C:\Users\Lenovo\Desktop\Labo67\repo_git\pticoDriver')
from common import *
import numpy as np

matrix_center = (0,0,91e-3)

sample_height = 0
sample_position = (0, 0, sample_height)

numerical_aperture = 0.07
wavelength = (5.25) * 10**(-7)
pixel_size = 3.2e-6
magnification = 1


"""Fourier Pixel Factor para la configuración que tenemos y un HR_shape de 512x512"""

led_equiespaciados = True
brazo = True

radio_brazo = 9.1 * 10**(-2)
n_leds_brazo = 9
overlap = 50

if brazo:
    central_led = (1, 0)

    max_theta = 65 * (np.pi/180)
    max_angle = max_theta

    ratio_LR = calculate_LR_ratio(numerical_aperture, max_angle)

    NA_synth = 1 / np.sqrt(1+(1/np.tan(max_angle))**2)
    number_pixels_HR = 512
    ratio_LR_synt = numerical_aperture / NA_synth 
    number_pixels_LR = number_pixels_HR * ratio_LR_synt
    fourier_pixel_factor = magnification / (number_pixels_LR * pixel_size)
    
    paso_theta = (max_angle / (n_leds_brazo - 1))
    thetas = np.arange(0 + paso_theta, max_theta+paso_theta, paso_theta)
    thetas = np.delete(thetas, 7)

    angulos_motor = circunf_max_equi_overlap(overlap, 37 // 2, max_theta, wavelength, fourier_pixel_factor) 
    led_positions = calculate_led_positions_brazo_equi(overlap, 37 // 2, angulos_motor,
                                                       thetas, radio_brazo, wavelength, fourier_pixel_factor)
    max_angle = calulate_max_angle(led_positions, central_led)            
    leds_number_x = 200
    leds_number_y = 200
else: 
    leds_number_x = 41
    leds_number_y = 41
    central_led = (leds_number_x + 1) // 2, (leds_number_y + 1) // 2

    if led_equiespaciados:
        led_spacing = 6e-3 
        led_positions = calculate_led_positions_equi(leds_number_x, leds_number_y, led_spacing, matrix_center)
    else:
        #Calculamos el k_spacing teniendo en cuenta la cantidad de leds como k_spacing = 2*np.pi()*fourier_pixe_factor*(512/33) aprox un k_spacing en pixeles de 15
        # Recalcular para el brazo
        k_spacing = 405000
        k_distributions = calculate_led_positions_equi(leds_number_x, leds_number_y, k_spacing, matrix_center)
        led_positions = calculate_led_positions_no_equi(k_distributions, central_led, sample_height, wavelength, matrix_center)

    max_angle = calulate_max_angle(led_positions, central_led)           
ratio_LR = calculate_LR_ratio(numerical_aperture, max_angle)
    
NA_synth = 1 / np.sqrt(1+(1/np.tan(max_angle))**2)
number_pixels_HR = 512
ratio_LR_synt = numerical_aperture / NA_synth
number_pixels_LR = number_pixels_HR * ratio_LR_synt
fourier_pixel_factor = magnification / (number_pixels_LR * pixel_size)
    
## Los valores deben estar en mm y deben estar entre -5e-3 y 5e-3 
h_error = 0
x_offset = 0
y_offset = 0
led_spacing_error = 0
## Escribir los ángulos en grados considerndo el sentido antihorario como positivo
# El valor debe ser par y entre 10º y -10º
led_alpha = 0
led_beta = 0
led_gamma = 0
sample_beta = 0



# Para graficar el espacio de Fourier
hr_shape = np.round(np.asarray((number_pixels_HR, number_pixels_HR))).astype(np.int_)
lr_shape = np.round(np.asarray((number_pixels_HR, number_pixels_HR)) * ratio_LR).astype(np.int_)
dc_location = np.array([256,256])

k_vectors, k_indexes = calculate_k_vectors_k_indices(
    led_positions, wavelength, sample_position, dc_location, fourier_pixel_factor)
hr_shape = (512,512)

coverage = sum_pupils(hr_shape, lr_shape, round(min(lr_shape)*0.5), k_indexes)

plt.figure(figsize=(10,10))
plt.imshow(coverage, cmap="viridis", origin="lower")
#plt.colorbar(label="Número de OTF superpuestas")
#plt.xlabel("kx [px]")
#plt.ylabel("ky [px]")
plt.show()