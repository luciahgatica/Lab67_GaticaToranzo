import pandas as pd
import pathlib
import numpy as np
import numpy.typing as npt
import matplotlib.pyplot as plt
import os
os.chdir(r'C:\Users\nahue\OneDrive\Documents\Arduino\simulaciones_nuevas')
from common import read_into_complex_image, calculate_k_vectors_k_indices_sample_tilt, simulate, save_images, create_pupil, sum_pupils, reconstruct, calculate_k_vectors_k_indices, led_errors_incorporated, plot_convergence, read_numpy_file, reconstruct_test
import time
from tqdm import tqdm
import sys
from skopt import callbacks
from skopt.callbacks import CheckpointSaver
from skopt import gp_minimize
from skopt.space import Real
from skopt.utils import cook_initial_point_generator
from functools import partial

time_start = time.time()
# Establecemos la carpeta en la que trabajaremos
ROOT = pathlib.Path(r"C:\Users\nahue\OneDrive\Documents\Arduino\simulaciones_nuevas")
# Establecemos la carpeta con las imágenes a simular y la carpeta en donde se guardarán las imágenes
# input_filedir = ROOT / "muestras_simuladas"
# output_filedir = ROOT / "simulacion_nueva"
# # Nombres de las imágenes de magnitud y fase
# mag_image = "magnitud_13_particulas_wavelength_red_disminucionruido_100.tiff"
# phase_image = "fase_envuelta_13_particulas_wavelength_red_ruido_0.tiff"

# t_im = (mag_image, phase_image)
# t_im = np.load(ROOT/input_filedir/"matriz_de_transmision_8x8.npy")
def simulation_pipeline(
        input_filedir, 
        output_filedir, 
        transmission_image,
        # mag_image, 
        # phase_image, 
        ratio_LR, 
        led_positions, 
        wavelength, 
        sample_position, 
        fourier_pixel_factor,
        led_spacing_error,
        x_offset,
        y_offset, 
        led_alpha,
        led_beta,
        led_gamma,
        sample_beta,
        h_error):
    
    if isinstance(transmission_image, (tuple, list)):
        mag_image, phase_image = transmission_image
        obj = read_into_complex_image(input_filedir / mag_image, input_filedir / phase_image)
    elif isinstance(transmission_image, str):
        obj = read_numpy_file(transmission_image)
    elif isinstance(transmission_image, np.ndarray) and transmission_image.ndim == 2:
        obj = transmission_image
    else:
        raise Exception(f"No se que hacer con {transmission_image}")
    
    # Leemos las imágenes de magnitud y fase de alta resolución (HR) y ubicamos el centro de la misma
    dc_location_HR = np.asarray((obj.shape)) // 2

    # Luego calculamos el tamaño de las imágenes de baja resolución (LR)
    lr_shape = np.round(np.asarray(obj.shape) * ratio_LR).astype(np.int_)

    # Calculamos las coordenadas de los índices en el espacio de frecuencias en pixeles
    # Estos serán el centro de cada imagen simulada de LR 

    led_positions_tilted = led_errors_incorporated(led_positions, x_offset, y_offset, led_spacing_error, led_alpha, led_beta, led_gamma)

    k_vectors, k_indexes = calculate_k_vectors_k_indices_sample_tilt(
            led_positions_tilted, wavelength, sample_position, dc_location_HR, fourier_pixel_factor, sample_beta, h_error)    

    # Simulamos las imágenes
    data, pupil = simulate(obj, lr_shape, round(min(lr_shape)*.5), k_indexes)

    # plt.imshow(pupil, cmap="gray", interpolation="nearest")
    # plt.axis("off")  # Ocultar ejes
    # plt.show()

    save_images(data, output_filedir)

    return "Imágenes de Baja Resolucion simuladas"


def recontruction_pipeline(
        recovery_error_cut,
        output_filedir, 
        input_filedir, 
        save_filedir, #
        transmission_image,
        # mag_image, 
        # phase_image,
        debug, #
        iterations,
        iteraciones_a_guardar, #
        mu_max,
        weight,
        sigmaN, 
        led_positions,
        wavelength, 
        sample_position, 
        fourier_pixel_factor,
        leds_number_x,
        leds_number_y,
        numb_external_leds_discarded_row_column,
        numb_internal_leds_discarded_row_column,
        led_spacing_error,
        x_offset,
        y_offset, 
        led_alpha,
        led_beta,
        led_gamma,
        sample_beta,
        h_error):
    
    # Tomamos las imágenes simuladas y las cargamos identificando a que led corresponden (key)
    imglist = sorted([filename for filename in output_filedir.glob("point*.npy")])

    data = leds_indexes = None

    for ndx, path in enumerate(imglist):
        
        if debug:
            if ndx == 0:
                img = np.load(path)
        else:
            img = np.load(path)
            
        if data is None:
            data = {}
            leds_indexes = []
            
        key = (int(path.stem[6:8]),int(path.stem[9:11]))
        data[key] = img
        leds_indexes.append(key)

    # Añadimos ruido
    data_original_max = np.max([np.max(arr) for arr in data.values()])

    sigma2 = (data_original_max * sigmaN) ** 2

    # Tomamos la dimension de las imágenes de LR
    lr_shape = data[list(data.keys())[0]].shape

    # Tomamos las imagenes de HR de magnitud y fase
    if isinstance(transmission_image, (tuple, list)):
        mag_image, phase_image = transmission_image
        obj = read_into_complex_image(input_filedir / mag_image, input_filedir / phase_image)
    elif isinstance(transmission_image, str):
        obj = read_numpy_file(transmission_image)
    elif isinstance(transmission_image, np.ndarray) and transmission_image.ndim == 2:
        obj = transmission_image
    else:
        raise Exception(f"No se que hacer con {transmission_image}")

    objf = np.fft.fftshift(np.fft.fft2(obj))
    hr_shape = (obj.shape[0], obj.shape[1])
    dc_location = np.asarray((obj.shape)) // 2

    #Calculamos los vectores en el espacio de frecuencias y los indices en el espacio de frecuencias en pixeles que usaremos en la reconstruccion
    
    led_positions_tilted = led_errors_incorporated(led_positions, x_offset, y_offset, led_spacing_error, led_alpha, led_beta, led_gamma)

    k_vectors_tilt, k_indexes_tilt = calculate_k_vectors_k_indices_sample_tilt(
            led_positions_tilted, wavelength, sample_position, dc_location, fourier_pixel_factor, sample_beta, h_error)   

    k_vectors, k_indexes = calculate_k_vectors_k_indices( 
    led_positions, wavelength, sample_position, dc_location, fourier_pixel_factor)  

# =============================================================================
#     # Filtramos los datos quitando un número de imagenes correspondientes a un número de leds en cada lado de las filas y columnas
#     # 1. Definir los límites del cuadrado (como ya lo hacías)
#     start_x = numb_external_leds_discarded_row_column + 1
#     end_x = leds_number_x + 1 - numb_external_leds_discarded_row_column
#     step = numb_internal_leds_discarded_row_column + 1
# 
#     start_y = numb_external_leds_discarded_row_column + 1
#     end_y = leds_number_y + 1 - numb_external_leds_discarded_row_column
# 
#     # 2. Encontrar el centro exacto de la matriz
#     center_x = (leds_number_x + 1) / 2.0
#     center_y = (leds_number_y + 1) / 2.0
# 
#     # 3. Calcular el radio cuadrado máximo sobre los ejes
#     # (Distancia desde el centro hasta tu límite de descarte original)
#     radius_x = abs((end_x - 1) - center_x)
#     radius_y = abs((end_y - 1) - center_y)
#     radius_sq = min(radius_x, radius_y) ** 2  # Usamos el radio al cuadrado para evitar raíces cuadradas (más rápido)
# 
#     # 4. Generar coordenadas con el filtro circular aplicado
#     filtered_coordinates = [
#         (i, j) 
#         for i in range(start_x, end_x, step) 
#         for j in range(start_y, end_y, step)
#         # Condición circular: la distancia al centro debe ser menor o igual al radio
#         if (i - center_x)**2 + (j - center_y)**2 <= radius_sq
#     ]
# 
#     # 5. Mantener tus diccionarios intactos
#     filtered_indexes = {key: k_indexes[key] for key in filtered_coordinates if key in leds_indexes}
#     filtered_indexes_tilt = {key: k_indexes_tilt[key] for key in filtered_coordinates if key in leds_indexes}
#     filtered_data = {key: data[key] for key in filtered_indexes_tilt if key in leds_indexes}
# =============================================================================

# =============================================================================
#     ####### MATRIZ #######
#     
#     # Filtramos los datos para la matriz cuadrada
#     # 1. Definir los límites del cuadrado (como ya lo hacías)
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
# =============================================================================

    ####### BRAZO #######
    
    # Filtramos los datos para la matriz cuadrada
    # 1. Definir los límites 
    
    keys_dict_de_leds = list(led_positions.keys())
    leds_para_reconstruir = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    filtered_coordinates = []
    for led, angulo in keys_dict_de_leds:
        if led in leds_para_reconstruir:
            filtered_coordinates.append((led, angulo))

    # 5. Mantener tus diccionarios intactos
    filtered_indexes = {key: k_indexes[key] for key in filtered_coordinates if key in leds_indexes}
    filtered_indexes_tilt = {key: k_indexes_tilt[key] for key in filtered_coordinates if key in leds_indexes}
    filtered_data = {key: data[key] for key in filtered_indexes_tilt if key in leds_indexes}

    def _on_iteration(ndx: int, z: npt.NDArray[np.complex128]):
        """This will be call on each iteration
        """
        if np.mod(ndx, 50) != 0:
            return

    # Creamos la pupila que usaremos en cada imagen simulada al reconstruir
    synthetic_pupil = create_pupil(round(.5 * np.min(data[list(data.keys())[0]].shape)), data[list(data.keys())[0]].shape)

    # Definimos los indices en los que reconstruiremos, sumando y restando diez pixeles a los valores de los indices calculados anteriormente
    z0 = im_r = np.zeros((hr_shape[0],hr_shape[1])).astype(complex)
    recovery_errs = np.zeros((iterations))

    # Sumo las pupilas utilizadas en la reconstruccion para luego visualizarlas
    filtered_matrix_overlapped_with_pupils = sum_pupils(obj.shape, lr_shape, round(min(lr_shape)* 0.5), filtered_indexes)
    filtered_matrix_overlapped_with_pupils_tilt = sum_pupils(obj.shape, lr_shape, round(min(lr_shape)* 0.5), filtered_indexes_tilt)

    # fig, axes = plt.subplots(2, 2, figsize=(8, 8))
    # tmp = np.asarray(list(led_positions.values()))
    # axes[0,0].scatter(tmp[:, 0], tmp[:, 1], c="g")
    # axes[0,0].set_title("Espacio real")

    # tmp1 = np.asarray(list(k_vectors.values()))
    # tmp2 = np.asarray(list(k_vectors_tilt.values()))
    # axes[0,1].scatter(tmp1[:, 0], tmp1[:, 1], c="r", label="k_vectors")
    # axes[0,1].scatter(tmp2[:, 0], tmp2[:, 1], c="b", label="k_vectors_tilt")
    # axes[0,1].set_title("Espacio k")

    # tmp = np.asarray(list(k_indexes_tilt.values()))
    # axes[1,0].scatter(tmp[:, 0], tmp[:, 1], c="r")
    # axes[1,0].set_title("k en la Simulacion - pixeles")

    # tmp1 = np.asarray(list(filtered_indexes.values()))
    # tmp2 = np.asarray(list(filtered_indexes_tilt.values()))
    # axes[1,1].scatter(tmp1[:, 0], tmp1[:, 1], c="r", label="indices_filtrados")
    # axes[1,1].scatter(tmp2[:, 0], tmp2[:, 1], c="b", label="indices_filtrados_tilt")
    # axes[1,1].set_title("k en la reconstruccion")
    # axes[1,1].legend()

    # plt.tight_layout()
    # nombre_del_archivo_2 = f"Reconstruccion quitando {2*numb_external_leds_discarded_row_column} filas-columnas"
    # fig.canvas.manager.set_window_title(nombre_del_archivo_2)
    # plt.show()

    fig, axes = plt.subplots(1, 2, figsize=(12, 6)) 
    axes[0].imshow(filtered_matrix_overlapped_with_pupils)
    axes[1].imshow(filtered_matrix_overlapped_with_pupils_tilt)
    titulo = f"Solapamiento en la Reconstrucción quitando {2 * numb_external_leds_discarded_row_column} filas-columnas"
    fig.suptitle(titulo)  # Usé suptitle para un título general de la figura

    fig.canvas.manager.set_window_title(titulo)  

    plt.show()

    print(f"\nSample height: {h_error}, Sample beta: {sample_beta}\nOffset_y: {y_offset}, Offset_x: {x_offset}\nAlpha led: {led_alpha}, Beta led: {led_beta}, Gamma led: {led_gamma}\nSigma(ruido): {sigmaN}")
                    

    data_array = np.stack([filtered_data[key] for key in sorted(filtered_data.keys())], axis=-1) 
    z0, im_r, recovery_errs_dict, dictionary, imagenes_intermedias, phase_max, phase_min, pasos, diferencias, perfiles, perfil_target = reconstruct_test(
        recovery_error_cut, data_array, hr_shape, sigma2, filtered_indexes_tilt, synthetic_pupil, iterations, mu_max, weight, objf, _on_iteration, iteraciones_a_guardar)
    os.makedirs(save_filedir, exist_ok=True)
    iteraciones_x = np.arange(iteraciones_a_guardar, (len(phase_max) + 1) * iteraciones_a_guardar, iteraciones_a_guardar)
    recovery_errs_df_HR = pd.DataFrame.from_records(recovery_errs_dict)
    recovery_errs_df_HR['iteraciones'] = iteraciones_x
    recovery_errs = recovery_errs_df_HR["recovery_err"].to_list()
    recovery_errs_df_LR = pd.DataFrame.from_records(dictionary)
    recovery_errs_df_LR['iteraciones'] = iteraciones_x
    diferencias_df = pd.DataFrame.from_records(diferencias)
    perfiles_df = pd.DataFrame.from_records(perfiles)
    perfiles_df['iteraciones'] = iteraciones_x
    perfil_target_df = pd.DataFrame.from_records(perfil_target)
    # z0=np.append(z0,z00,axis=0)   #z0.append(z00)
    # im_r=np.append(im_r,im_r00)  #im_r.append(im_r00)
    folder_intermedias = f"imagenes_intermedias_iter_{iterations}"
    os.makedirs(ROOT/folder_intermedias, exist_ok=True)

    print("Guardando capturas de imágenes intermedias...")
    
    # Asumiendo que 'imagenes_intermedias' es una lista de matrices...
    for clave, img_intermedia in imagenes_intermedias.items():
        # Creamos una figura pequeña y compacta (baja calidad/bajo peso)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 3))
        
        # Graficamos Magnitud y Fase de la etapa intermedia
        ax1.imshow(np.abs(img_intermedia), cmap='gray')
        ax1.set_title(f'Mag - Paso {clave}')
        ax1.axis('off')
        
        ax2.imshow(np.angle(img_intermedia), cmap='magma')
        ax2.set_title(f'Fase - Paso {clave}')
        ax2.axis('off')
        
        # Ajustamos los márgenes para que no haya espacios en blanco extra
        plt.tight_layout()
        
        # Guardamos en formato PNG comprimido dentro de la carpeta
        nombre_limpio = f"t_im_iteraciones_{clave}_size_{hr_shape[0]}_color{wavelength}_used_leds_{leds_number_y - 2*numb_external_leds_discarded_row_column}_ruido_{sigmaN:.3f}.png"
        nombre_archivo = os.path.join(ROOT/folder_intermedias, f"intermedia_{nombre_limpio}.png")
        
        # El parámetro 'dpi=80' o 'dpi=100' asegura que la imagen sea liviana y tenga pocos píxeles
        plt.savefig(nombre_archivo, bbox_inches='tight')
        plt.close(fig)


    print(f'El recovery error es: {recovery_errs[-1]}')
    default_filename = f"t_im_iteraciones_{iterations}_size_{hr_shape[0]}_color{wavelength}_used_leds_{leds_number_y - 2*numb_external_leds_discarded_row_column}_ruido_{sigmaN:.3f}.png"
    # if len(recovery_errs) == (iterations-1):
    plt.figure()
    plt.subplot(1, 2, 1)
    plt.imshow(np.abs(im_r))
    # plt.title(f'Recovery Error {recovery_errs[-1]}')
    plt.subplot(1, 2, 2)
    plt.imshow(np.angle(im_r))
    plt.savefig(os.path.join(save_filedir, default_filename))
    plt.close()
    # np.save(f"Matriz_transmision_{default_filename}", im_r)
    np.save(os.path.join(save_filedir, f"fase_{default_filename}.npy"), np.angle(im_r))
    np.save(os.path.join(save_filedir, f"magnitud_{default_filename}.npy"), np.abs(im_r))
    # plt.show()
    plt.figure()

    plt.plot(iteraciones_x, recovery_errs)
    plt.xlabel('Iteration')
    plt.ylabel('Recovery Error')
    RE_default_filename = f"RE_{default_filename}"
    plt.savefig(RE_default_filename)
    # plt.show()
    plt.legend()
    np.save('recovery_errs',recovery_errs)

    plt.plot(iteraciones_x, phase_max, 'b-', label='Phase max/pi')
    plt.plot(iteraciones_x, phase_min, 'r-', label='Phase min/pi')
    plt.plot(iteraciones_x, pasos, 'g-', label='Pasos*10')
    plt.xlabel('Iteration')
    plt.ylabel('Phase value')
    plt.legend()

    plt.savefig(os.path.join(save_filedir, f"Phase_stats_{default_filename}"))
    plt.close()
    # plt.show()
    # plt.legend()
    

    recovery_errs_df_HR.attrs = {
        "recovery_error_cut": recovery_error_cut,
        "transmision_image": transmission_image,
        "iterations": iterations,
        "mu_max": mu_max,
        "weight": weight,
        "sigmaN": sigmaN, 
        "led_positions": led_positions,
        "wavelength": wavelength, 
        "sample_position": sample_position, 
        "fourier_pixel_factor": fourier_pixel_factor,
        "leds_number_x": leds_number_x,
        "leds_number_y": leds_number_y,
        "numb_external_leds_discarded_row_column": numb_external_leds_discarded_row_column,
        "numb_internal_leds_discarded_row_column": numb_internal_leds_discarded_row_column,
        "led_spacing_error": led_spacing_error,
        "x_offset": x_offset,
        "y_offset": y_offset, 
        "led_alpha": led_alpha,
        "led_beta": led_beta,
        "led_gamma": led_gamma,
        "sample_beta": sample_beta,
        "h_error": h_error
    }
    return recovery_errs_df_HR, diferencias_df, recovery_errs_df_LR, perfiles_df, perfil_target_df

from microscope_config import ratio_LR, led_positions, sample_position, fourier_pixel_factor, leds_number_x, leds_number_y, sample_beta, h_error, x_offset, y_offset, led_spacing_error, led_alpha, led_beta, led_gamma

debug = False
iterations = 10
sigmaN = [0.004]
mu_max = 0.4
weight = 1
numb_external_leds_discarded_row_column = 5
numb_internal_leds_discarded_row_column = 0
n_iteraciones_a_guardar = 1

config_colores = {
    #4.7e-07: {"name": "blue", "wave": 4.7e-07},
    5.3e-07: {"name": "green", "wave": 5.3e-07},
    #6.8e-07: {"name": "red", "wave": 6.8e-07}
}
size_de_imagenes = 512
for wave, info in config_colores.items():
    input_filedir = ROOT / "data_source"
    output_filedir = ROOT / f"simulacion_nueva_{info["name"]}"
    # Nombres de las imágenes de magnitud y fase
    mag_image = "Map_512.tiff"
    phase_image = "baboon.tif"
    t_im = (mag_image, phase_image)
    simulation_pipeline(
        input_filedir,
        output_filedir,
        t_im,
        # mag_image, phase_image,
        ratio_LR,
        led_positions,
        wave,
        sample_position,
        fourier_pixel_factor,
        led_spacing_error,
        x_offset=x_offset,
        y_offset=y_offset, 
        led_alpha=led_alpha, 
        led_beta=led_beta, 
        led_gamma=led_gamma,
        sample_beta=sample_beta,
        h_error=h_error)

# Este será el error buscado, si caemos por debajo de este error damos por buena la reconstruccion
    recovery_error_required = 1
    print()
    print(f"Recontruccion en el color {info['name']}")
    save_filedir = ROOT/ f"{info['name']}"
    for sigma in sigmaN:
        df_results_reconstruccion_exacta_HR, df_diferencias, df_results_reconstruccion_exacta_LR, perfiles_df, perfil_target_df = recontruction_pipeline(
        0,
        output_filedir, 
        input_filedir,
        save_filedir,
        t_im, 
        # mag_image, 
        # phase_image,
        debug,
        iterations,
        n_iteraciones_a_guardar,
        mu_max,
        weight,
        sigma,
        led_positions,
        wave, 
        sample_position, 
        fourier_pixel_factor,
        leds_number_x,
        leds_number_y,
        numb_external_leds_discarded_row_column,
        numb_internal_leds_discarded_row_column,
        0,
        x_offset=x_offset,
        y_offset=y_offset,
        led_alpha=led_alpha,
        led_beta=led_beta,
        led_gamma=led_gamma,
        sample_beta=sample_beta,
        h_error=h_error)
    
    # print(df_results_reconstruccion_exacta_HR["recovery_err"].iloc[-1])

    # file_name_reconstruccion_exacta_HR = f"resultados_errores_reconstruccion_exacta_HR_{mag_image}_{phase_image}_iteraciones_{iterations}.csv"
    # df_results_reconstruccion_exacta_HR.to_csv(file_name_reconstruccion_exacta_HR, index=False)
    # df_results_reconstruccion_exacta_HR.to_pickle(file_name_reconstruccion_exacta_HR + ".pandas")

    # print(df_results_reconstruccion_exacta_LR["recovery_err"].iloc[-1])

    # file_name_reconstruccion_exacta_LR = f"resultados_errores_reconstruccion_exacta_LR_{mag_image}_{phase_image}_iteraciones_{iterations}.csv"
    # df_results_reconstruccion_exacta_LR.to_csv(file_name_reconstruccion_exacta_LR, index=False)
    # df_results_reconstruccion_exacta_LR.to_pickle(file_name_reconstruccion_exacta_LR + ".pandas")

        file_name_reconstruccion_exacta_HR = f"resultados_errores_reconstruccion_exacta_HR_{info['name']}_{size_de_imagenes}_iteraciones_{iterations}_ruido_{sigma:.3f}.csv"
        ruta_final_HR = os.path.join(save_filedir, file_name_reconstruccion_exacta_HR)
        df_results_reconstruccion_exacta_HR.to_csv(ruta_final_HR, index=False)
        file_name_diferencias = f"resultados_diferencias_reconstruccion_HR_{info['name']}_{size_de_imagenes}_iteraciones_{iterations}_ruido_{sigma:.3f}.csv"
        ruta_final_diferencias = os.path.join(save_filedir, file_name_diferencias)
        df_diferencias.to_csv(ruta_final_diferencias, index=False)

        file_name_reconstruccion_exacta_LR = f"resultados_errores_reconstruccion_exacta_LR_{info['name']}_{size_de_imagenes}_iteraciones_{iterations}_ruido_{sigma:.3f}.csv"
        ruta_final_LR = os.path.join(save_filedir, file_name_reconstruccion_exacta_LR)
        df_results_reconstruccion_exacta_LR.to_csv(ruta_final_LR, index=False)

        file_name_perfiles = f"resultados_perfiles_{info['name']}_{size_de_imagenes}_iteraciones_{iterations}_ruido_{sigma:.3f}.csv"
        ruta_final_perfiles = os.path.join(save_filedir, file_name_perfiles)
        perfiles_df.to_csv(ruta_final_perfiles, index=False)

        file_name_perfil_target = f"resultados_perfil_target_{info['name']}_{size_de_imagenes}_iteraciones_{iterations}_ruido_{sigma:.3f}.csv"
        ruta_final_perfil_target = os.path.join(save_filedir, file_name_perfil_target)
        perfil_target_df.to_csv(ruta_final_perfil_target, index=False)

time_end = time.time()
print(f"Tiempo total de ejecución: {time_end - time_start:.2f} segundos")