from common import *

matrix_center = (0,0,91e-3)
sample_height = 0
sample_position = (0, 0, sample_height)

numerical_aperture = 0.07
wavelength = 5.3e-7 #4.7e-07: "blue" , 5.3e-07: "green", 6.8e-07: "red"
pixel_size = 3.2e-6
magnification = 1


"""Fourier Pixel Factor para la configuración que tenemos y un HR_shape de 512x512"""

led_equiespaciados = True
brazo = False

radio_brazo = 9.1 * 10**(-2)
n_leds_brazo = 10
overlap = 30

if brazo:
    central_led = (1, 1)

    max_theta = 66 * (np.pi/180)
    max_angle = max_theta

    ratio_LR = calculate_LR_ratio(numerical_aperture, max_angle)

    NA_synth = 1 / np.sqrt(1+(1/np.tan(max_angle))**2)
    number_pixels_HR = 512
    ratio_LR_synt = numerical_aperture / NA_synth 
    number_pixels_LR = number_pixels_HR * ratio_LR_synt
    fourier_pixel_factor = magnification / (number_pixels_LR * pixel_size)
    
    paso_theta = max_angle / (n_leds_brazo - 1)
    thetas = np.arange(0 + paso_theta, max_theta+paso_theta, paso_theta)
    #thetas = np.delete(thetas, [-3])

    angulos_motor = circunf_max_equi_overlap(overlap, 37 // 2, max_theta, wavelength, fourier_pixel_factor) 
    led_positions = calculate_led_positions_brazo_equi(overlap, 37 // 2, angulos_motor,
                                                       thetas, radio_brazo, wavelength, fourier_pixel_factor)
    max_angle = calulate_max_angle(led_positions, central_led, sample_height)            
    leds_number_x = 10
    leds_number_y = 200
else: 
    leds_number_x = 31
    leds_number_y = 31
    central_led = (leds_number_x + 1) // 2, (leds_number_y + 1) // 2

    if led_equiespaciados:
        led_spacing = 5.4e-3 
        led_positions = calculate_led_positions_equi(leds_number_x, leds_number_y, led_spacing, matrix_center)
    else:
        #Calculamos el k_spacing teniendo en cuenta la cantidad de leds como k_spacing = 2*np.pi()*fourier_pixe_factor*(512/33) aprox un k_spacing en pixeles de 15
        # Recalcular para el brazo
        k_spacing = 405000
        k_distributions = calculate_led_positions_equi(leds_number_x, leds_number_y, k_spacing, matrix_center)
        led_positions = calculate_led_positions_no_equi(k_distributions, central_led, sample_height, wavelength, matrix_center)
        
    max_angle = calulate_max_angle(led_positions, central_led, sample_height)            
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

if led_equiespaciados:

    led_positions_offset = {}
    for key, coordenada in led_positions.items():
        led_positions_offset[key] = led_offset_incorporated(x_offset, y_offset, coordenada)

    led_positions_failed = {}
    for key, coordenada in led_positions_offset.items():
        led_positions_failed[key] = led_spacing_error_incorporated(led_spacing_error, coordenada)

    led_positions_tilt = {}
    for key, coordenada in led_positions_failed.items():
        led_positions_tilt[key] = euler_angles_incorporated(led_alpha, led_beta, led_gamma, coordenada)


# =============================================================================
# # Para graficar el espacio de Fourier
# 
# hr_shape = (number_pixels_HR, number_pixels_HR)
# lr_shape = (int(number_pixels_LR), int(number_pixels_LR))
# 
# dc_location = np.asarray(hr_shape) // 2
# k_vectors, k_indexes = calculate_k_vectors_k_indices(led_positions, wavelength,
#     sample_position, dc_location, fourier_pixel_factor)
# 
# 
# ########### Brazo ############ 
# if brazo:
#     leds_para_reconstruir = [1,2,3,4,5,6,7,8,9,10]
#     filtered_indexes = {
#         key: value
#         for key, value in k_indexes.items()
#         if key[0] in leds_para_reconstruir
#         }
#     
# ########### Matriz ############
# else:
#     numb_external_leds_discarded_row_column = 0 
#     start_x = numb_external_leds_discarded_row_column + 1
#     end_x = leds_number_x + 1 - numb_external_leds_discarded_row_column
#     step = 2
#     
#     start_y = numb_external_leds_discarded_row_column + 1
#     end_y = leds_number_y + 1 - numb_external_leds_discarded_row_column
#     
#     # 4. Generar coordenadas con el filtro aplicado
#     filtered_coordinates = [
#         (i, j) 
#         for i in range(start_x, end_x, step) 
#         for j in range(start_y, end_y, step)
#         ]
#     filtered_indexes = {key: k_indexes[key] for key in filtered_coordinates if key in k_indexes}
# 
# 
# 
# filtered_matrix = sum_pupils(hr_shape, lr_shape, round(min(lr_shape) * 0.5), 
#                              filtered_indexes)
# plt.imshow(filtered_matrix)
# plt.show()
# =============================================================================


#     import numpy as np
#     import matplotlib.pyplot as plt
#     from mpl_toolkits.mplot3d import Axes3D

#     colores = ['red', 'blue', 'green']

#     x, y, z, c = [], [], [], []
#     # Extraer coordenadas en listas separadas
#     for (fila, columna), coord in led_positions_tilt.items():
#             x.append(coord[0])
#             y.append(coord[1])
#             z.append(coord[2])
#             c.append(colores[fila % len(colores)])

#     # Crear la figura en 3D
#     fig = plt.figure(figsize=(8, 6))
#     ax = fig.add_subplot(111, projection='3d')

#     # Graficar los puntos con los colores intercalados
#     ax.scatter(x, y, z, c=c, marker='o', s=50)

#     x_range = max(x) - min(x)
#     y_range = max(y) - min(y)
#     z_range = max(z) - min(z)
#     max_range = max(x_range, y_range, z_range) / 2

#     mid_x = (max(x) + min(x)) / 2
#     mid_y = (max(y) + min(y)) / 2
#     mid_z = (max(z) + min(z)) / 2

#     ax.set_xlim(mid_x - max_range, mid_x + max_range)
#     ax.set_ylim(mid_y - max_range, mid_y + max_range)
#     ax.set_zlim(mid_z - max_range, mid_z + max_range)

#     # Etiquetas de ejes
#     ax.set_xlabel('X')
#     ax.set_ylabel('Y')
#     ax.set_zlabel('Z')
#     ax.set_title('Distribución de LEDs en R3')

#     # Mostrar la gráfica
#     plt.show()


#     if False:
#         import matplotlib.pyplot as plt

#         tmp = np.asarray(list(led_positions.values()))
#         plt.scatter(tmp[:, 0], tmp[:, 1], c="r", label="led equi")
#         plt.legend()
#         plt.show()