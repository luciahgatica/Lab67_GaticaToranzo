import numpy as np
import matplotlib.pyplot as plt
import numpy.typing as npt
import pandas as pd
from PIL import Image
import numpy as np
from pathlib import Path

from common import calulate_max_angle,calculate_LR_ratio, reconstruct_real_images, calculate_led_positions_equi, read_into_complex_image, read_numpy_file, led_errors_incorporated, calculate_k_vectors_k_indices, calculate_k_vectors_k_indices_sample_tilt, create_pupil, sum_pupils, reconstruct, reconstruct_real_images_test
debug = False
iterations = 10
sigmaN = 0.004
mu_max = 0.4
weight = 1
numb_external_leds_discarded_row_column_x = 10
numb_external_leds_discarded_row_column_y = 8
numb_internal_leds_discarded_row_column = 0
extra_leds_for_max_angle = 4
filedir = '/home/chanoscopio/Documents/AleYLu/imagenes_tomadas/2026-06-05-b/organizado/blue/13x13_recortada_200'
input_filedir = Path(filedir)
leds_number_x = 33
leds_number_y = 29
wavelength = 4.7e-7 # g=5.3e-7, r=6.8e-7, b=4.7e-7
central_led = 17, 15
led_spacing = 6e-3
matrix_center = (0,0,0)
led_positions = calculate_led_positions_equi(leds_number_x, leds_number_y ,led_spacing, matrix_center)
sample_height = 76e-3
sample_position = (0, 0, sample_height)
numerical_aperture = 0.10
# max_angle = calulate_max_angle(led_positions, central_led, sample_height)
# ratio_LR = calculate_LR_ratio(numerical_aperture, max_angle)
pixel_size = 3.2e-6
magnification = 2

# NA_synth = 1 / np.sqrt(1+(1/np.tan(max_angle))**2)

# """Cambiar este número de pixeles cada vez que usemos el programa"""
# number_pixels_LR = 900
# number_pixels_HR = np.round(number_pixels_LR/ratio_LR)
# ratio_LR_synt = numerical_aperture / NA_synth
# number_pixels_LR = number_pixels_HR * ratio_LR_synt
# fourier_pixel_factor = magnification / (number_pixels_LR * pixel_size)

# def recontruction_pipeline_real_images(
#         recovery_error_cut,
#         input_filedir, 
#         iterations,
#         mu_max,
#         weight,
#         sigmaN, 
#         led_positions,
#         wavelength, 
#         numerical_aperture, 
#         pixel_size, 
#         magnification, 
#         max_angle,
#         ratio_LR,
#         sample_position, 
#         leds_number_x,
#         leds_number_y,
#         numb_external_leds_discarded_row_column_x,
#         numb_external_leds_discarded_row_column_y,
#         numb_internal_leds_discarded_row_column,
#         led_spacing_error,
#         x_offset,
#         y_offset, 
#         led_alpha,
#         led_beta,
#         led_gamma,
#         sample_beta,
#         h_error):
    
#     # 1️⃣ Tomamos las imágenes TIFF
#     imglist = sorted([filename for filename in input_filedir.glob("fila*.tiff")])

#     data = leds_indexes = None

#     for ndx, path in enumerate(imglist):
#         img = np.array(Image.open(path), dtype=np.float32)  # ✅ forzamos float32 para ahorrar memoria

#         if data is None:
#             data = {}
#             leds_indexes = []
            
#         key = (int(path.stem[4:6]), int(path.stem[10:12]))
#         data[key] = img
#         leds_indexes.append(key)

#     # 2️⃣ Dimensiones de las imágenes LR
#     lr_shape = data[list(data.keys())[0]].shape
#     NA_synth = 1 / np.sqrt(1+(1/np.tan(max_angle))**2)
#     number_pixels_HR = np.round(lr_shape[0]/ratio_LR)
#     ratio_LR_synt = numerical_aperture / NA_synth
#     number_pixels_LR = number_pixels_HR * ratio_LR_synt
#     fourier_pixel_factor = magnification / (number_pixels_LR * pixel_size)
#     hr_shape = np.int64(np.round(lr_shape / ratio_LR))
#     dc_location = np.asarray(hr_shape) // 2

#     # 3️⃣ Cálculo de vectores e índices k
#     led_positions_tilted = led_errors_incorporated(led_positions, 0, 0, 0, 0, 0, 0)
#     k_vectors_tilt, k_indexes_tilt = calculate_k_vectors_k_indices_sample_tilt(
#         led_positions_tilted, wavelength, sample_position, dc_location, fourier_pixel_factor, 0, 0
#     )
#     k_vectors, k_indexes = calculate_k_vectors_k_indices(
#         led_positions, wavelength, sample_position, dc_location, fourier_pixel_factor
#     )

#     # 4️⃣ Filtrado de LEDs (quitamos bordes)
#     filtered_coordinates = [
#         (i, j)
#         for i in range(numb_external_leds_discarded_row_column_x + 1, leds_number_x + 1 - numb_external_leds_discarded_row_column_x, numb_internal_leds_discarded_row_column + 1)
#         for j in range(numb_external_leds_discarded_row_column_y + 1, leds_number_y + 1 - numb_external_leds_discarded_row_column_y, numb_internal_leds_discarded_row_column + 1)
#     ]
#     filtered_indexes = {key: k_indexes[key] for key in filtered_coordinates if key in leds_indexes}
#     filtered_indexes_tilt = {key: k_indexes_tilt[key] for key in filtered_coordinates if key in leds_indexes}
#     filtered_data = {key: data[key] for key in filtered_indexes_tilt if key in leds_indexes}

#     # ✅ LIBERAMOS `data` para ahorrar memoria RAM
#     del data
#     import gc
#     gc.collect()

#     def _on_iteration(ndx: int, z: npt.NDArray[np.complex128]):
#         """Callback en cada iteración"""
#         if np.mod(ndx, 50) != 0:
#             return

#     # 5️⃣ Creamos la pupila sintética
#     synthetic_pupil = create_pupil(round(.5 * np.min(lr_shape)), lr_shape)

#     # 6️⃣ Solapamiento de pupilas (opcional, debug)
#     filtered_matrix_overlapped_with_pupils = sum_pupils(hr_shape, lr_shape, round(min(lr_shape) * 0.5), filtered_indexes)
#     filtered_matrix_overlapped_with_pupils_tilt = sum_pupils(hr_shape, lr_shape, round(min(lr_shape) * 0.5), filtered_indexes_tilt)

#     print(f"\nSample height: {h_error}, Sample beta: {sample_beta}\nOffset_y: {y_offset}, Offset_x: {x_offset}\nAlpha led: {led_alpha}, Beta led: {led_beta}, Gamma led: {led_gamma}")

#     # ✅ 7️⃣ Creamos MEMMAP en disco para no cargar todo en RAM
#     filtered_keys = sorted(filtered_data.keys())
#     num_imgs = len(filtered_keys)
#     h, w = filtered_data[filtered_keys[0]].shapemagnitud_t_im_iteraciones_300_size_300_color7e-07_max_angle0.30587887140485215.png

#     memmap_file = "data_array_temp.dat"
#     data_array = np.memmap(memmap_file, dtype=np.float32, mode='w+', shape=(h, w, num_imgs))

#     print(f"Creando memmap de {h}x{w}x{num_imgs} → {(h*w*num_imgs*4)/(1024**3):.2f} GB en disco")

#     # Copiamos imágenes al memmap, UNA a la vez
#     for idx, key in enumerate(filtered_keys):
#         img = filtered_data[key]
#         data_array[:, :, idx] = img  # se escribe en disco
#         del img  # liberamos memoria
#     # ✅ flush para asegurar que está escrito en disco
#     data_array.flush()

#     # ✅ liberamos `filtered_data` para ahorrar memoria
#     del filtered_data
#     gc.collect()

#     # 8️⃣ Llamamos reconstrucción usando el memmap (sin cargarlo en RAM)
#     z0, im_r = reconstruct_real_images(
#         recovery_error_cut,
#         data_array,
#         hr_shape,
#         0,
#         filtered_indexes_tilt,
#         synthetic_pupil,
#         iterations,
#         mu_max,
#         weight,
#         _on_iteration
#     )

#     # ✅ Borramos el archivo temporal cuando ya no sea necesario
#     import os
#     os.remove(memmap_file)safe_slice_lo

#     # 9️⃣ Guardamos resultados
#     default_filename = f"t_im_iteraciones_{iterations}_size_{lr_shape[0]}_altura_{round(h_error,4)}_offset_x_{round(x_offset,4)}_offset_y_{round(y_offset,4)}_sample_beta_{round(sample_beta,4)}_alpha_{round(led_alpha,4)}_beta_{round(led_beta,4)}_gamma_{round(led_gamma,4)}.png"

#     plt.figure()
#     plt.subplot(1, 2, 1)
#     plt.imshow(np.abs(im_r))
#     plt.subplot(1, 2, 2)
#     plt.imshow(np.angle(im_r))
#     plt.savefig(default_filename)

#     np.save(f"Matriz_transmision_{default_filename}", im_r)
#     np.save(f"fase_{default_filename}.npy", np.angle(im_r))
#     np.save(f"magnitud_{default_filename}.npy", np.abs(im_r))



"""funcion reconstruction_pipeline antes de memap"""

def recontruction_pipeline_real_images(
        recovery_error_cut,
        # output_filedir, 
        input_filedir, 
        # transmission_image,
        # mag_image, 
        # phase_image,
        iterations,
        mu_max,
        weight,
        sigmaN, 
        led_positions,
        wavelength, 
        numerical_aperture, 
        pixel_size, 
        magnification, 
        central_led, 
        sample_height,
        # max_angle,
        # ratio_LR,
        sample_position,
        leds_number_x,
        leds_number_y,
        numb_external_leds_discarded_row_column_x,
        numb_external_leds_discarded_row_column_y,
        numb_internal_leds_discarded_row_column,
        extra_leds_for_max_angle,
        led_spacing_error,
        x_offset,
        y_offset, 
        led_alpha,
        led_beta,
        led_gamma,
        sample_beta,
        h_error):
    
    # Tomamos las imágenes tomadas y las cargamos identificando a que led corresponden (key)
    imglist = sorted([filename for filename in input_filedir.glob("fila*.tiff")])

    data = leds_indexes = None

    for ndx, path in enumerate(imglist):
        
        if debug:
            if ndx == 0:
                img = np.array(Image.open(path))
        else:
            img = np.array(Image.open(path))
            
        if data is None:
            data = {}
            leds_indexes = []
            
        key = (int(path.stem[4:6]),int(path.stem[10:12]))
        data[key] = img
        leds_indexes.append(key)

    # Añadimos ruido
    # data_original_max = np.max([np.max(arr) for arr in data.values()])

    # sigma2 = (data_original_max * sigmaN) ** 2
    filtered_coordinates = [(i, j) for i in range(numb_external_leds_discarded_row_column_x+1, leds_number_x+1-numb_external_leds_discarded_row_column_x,numb_internal_leds_discarded_row_column +1) for j in range(numb_external_leds_discarded_row_column_y+1, leds_number_y+1-numb_external_leds_discarded_row_column_y,numb_internal_leds_discarded_row_column +1)]
    filtered_leds = {key: led_positions[key] for key in filtered_coordinates if key in leds_indexes}
    max_angle_led_positions_filtered = [(i, j) for i in range(numb_external_leds_discarded_row_column_x+1 - extra_leds_for_max_angle, leds_number_x+1 - numb_external_leds_discarded_row_column_x + extra_leds_for_max_angle,numb_internal_leds_discarded_row_column +1) for j in range(numb_external_leds_discarded_row_column_y+1 - extra_leds_for_max_angle, leds_number_y+1-numb_external_leds_discarded_row_column_y+extra_leds_for_max_angle,numb_internal_leds_discarded_row_column +1)]
    max_angle_led_positions =  {key: led_positions[key] for key in max_angle_led_positions_filtered}
    max_angle = calulate_max_angle(max_angle_led_positions, central_led, sample_height)
    ratio_LR = calculate_LR_ratio(numerical_aperture, max_angle)
    # Tomamos la dimension de las imágenes de LR
    lr_shape = data[list(data.keys())[0]].shape
    NA_synth = 1 / np.sqrt(1+(1/np.tan(max_angle))**2)
    number_pixels_HR = np.round(lr_shape[0]/ratio_LR)
    ratio_LR_synt = numerical_aperture / NA_synth
    number_pixels_LR = number_pixels_HR * ratio_LR_synt
    fourier_pixel_factor = magnification / (lr_shape[0] * pixel_size)
    # Tomamos las imagenes de HR de magnitud y fase
    # if isinstance(transmission_image, (tuple, list)):
    #     mag_image, phase_image = transmission_image
    #     obj = read_into_complex_image(input_filedir / mag_image, input_filedir / phase_image)
    # elif isinstance(transmission_image, str):
    #     obj = read_numpy_file(transmission_image)
    # elif isinstance(transmission_image, np.ndarray) and transmission_image.ndim == 2:
    #     obj = transmission_image
    # else:
    #     raise Exception(f"No se que hacer con {transmission_image}")

    # objf = np.fft.fftshift(np.fft.fft2(obj))
    hr_shape = np.int64(np.round(lr_shape / ratio_LR))
    dc_location = np.asarray(hr_shape) // 2

    #Calculamos los vectores en el espacio de frecuencias y los indices en el espacio de frecuencias en pixeles que usaremos en la reconstruccion
    
    led_positions_tilted = led_errors_incorporated(filtered_leds, x_offset, y_offset, 0, led_alpha, led_beta, led_gamma)

    k_vectors_tilt, k_indexes_tilt = calculate_k_vectors_k_indices_sample_tilt(
            led_positions_tilted, wavelength, sample_position, dc_location, fourier_pixel_factor, sample_beta, h_error)   

    k_vectors, k_indexes = calculate_k_vectors_k_indices( 
    filtered_leds, wavelength, sample_position, dc_location, fourier_pixel_factor)  

    # Filtramos los datos quitando un número de imagenes correspondientes a un número de leds en cada lado de las filas y columnas
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
    # z0 = im_r = np.zeros((hr_shape[0],hr_shape[1])).astype(complex)
    # recovery_errs = np.zeros((iterations))

    # Sumo las pupilas utilizadas en la reconstruccion para luego visualizarlas
    filtered_matrix_overlapped_with_pupils = sum_pupils(hr_shape, lr_shape, round(min(lr_shape)* 0.5), filtered_indexes)
    filtered_matrix_overlapped_with_pupils_tilt = sum_pupils(hr_shape, lr_shape, round(min(lr_shape)* 0.5), filtered_indexes_tilt)

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
    # nombre_del_archivo_2 = f"Reconstruccion usando {leds_number_x - 2*numb_external_leds_discarded_row_column_x} filas-columnas"
    # fig.canvas.manager.set_window_title(nombre_del_archivo_2)
    # plt.show()

    # fig, axes = plt.subplots(1, 2, figsize=(12, 6)) 
    # axes[0].imshow(filtered_matrix_overlapped_with_pupils)
    # axes[1].imshow(filtered_matrix_overlapped_with_pupils_tilt)
    # titulo = f"Solapamiento en la Reconstrucción usando {leds_number_x - 2 * numb_external_leds_discarded_row_column_x} filas-columnas"
    # fig.suptitle(titulo)  # Usé suptitle para un título general de la figura

    # fig.canvas.manager.set_window_title(titulo)  

    # plt.show()

    print(f"\nSample height: {h_error}, Sample beta: {sample_beta}\nOffset_y: {y_offset}, Offset_x: {x_offset}\nAlpha led: {led_alpha}, Beta led: {led_beta}, Gamma led: {led_gamma}")
                    

    data_array = np.stack([filtered_data[key] for key in sorted(filtered_data.keys())], axis=-1) 
    z0, im_r, imagenes_intermedias, phase_max, phase_min = reconstruct_real_images_test(recovery_error_cut, data_array, hr_shape, 0, filtered_indexes_tilt, synthetic_pupil, iterations, mu_max, weight, _on_iteration)

    # recovery_errs_df = pd.DataFrame.from_records(recovery_errs_dict)
    # recovery_errs = recovery_errs_df["recovery_err"].to_list()
    # z0=np.append(z0,z00,axis=0)   #z0.append(z00)
    # im_r=np.append(im_r,im_r00)  #im_r.append(im_r00)
    # print(f'El recovery error es: {recovery_errs[-1]}')
    default_filename = f"t_im_iteraciones_{iterations}_size_{lr_shape[0]}_color{wavelength}_max_angle_{max_angle}_used_leds_{leds_number_x - 2*numb_external_leds_discarded_row_column_x}.png"
    # if len(recovery_errs) == (iterations-1):
    plt.figure()
    plt.subplot(1, 2, 1)
    plt.imshow(np.abs(im_r))
    # plt.title(f'Recovery Error {recovery_errs[-1]}')
    plt.subplot(1, 2, 2)
    plt.imshow(np.angle(im_r))
    plt.savefig(default_filename)
    # np.save(f"Matriz_transmision_{default_filename}", im_r)
    np.save(f"fase_{default_filename}.npy", np.angle(im_r))
    np.save(f"magnitud_{default_filename}.npy", np.abs(im_r))
    # plt.show()

    for key, imagen in imagenes_intermedias.items():
        default_filename_2 = f"t_im_iteraciones_{key}_size_{lr_shape[0]}_color{wavelength}_max_angle_{max_angle}_used_leds_{leds_number_x - 2*numb_external_leds_discarded_row_column_x}.png"
        # if len(recovery_errs) == (iterations-1):
        plt.figure()
        plt.subplot(1, 2, 1)
        plt.imshow(np.abs(imagen))
        # plt.title(f'Recovery Error {recovery_errs[-1]}')
        plt.subplot(1, 2, 2)
        plt.imshow(np.angle(imagen))
        plt.savefig(default_filename_2)
        # np.save(f"Matriz_transmision_{default_filename_2}", imagen)
        np.save(f"fase_{default_filename_2}.npy", np.angle(imagen))
        np.save(f"magnitud_{default_filename_2}.npy", np.abs(imagen))
    plt.figure()

    plt.plot(phase_max, 'b-', label='Phase max')
    plt.plot(phase_min, 'r-', label='Phase min')

    plt.xlabel('Iteration')
    plt.ylabel('Phase value')
    plt.legend()

    plt.savefig(f"Phase_stats_{default_filename}")
    plt.show()
    plt.legend()
    # np.save('recovery_errs',recovery_errs)

    # recovery_errs_df.attrs = {
    #     "recovery_error_cut": recovery_error_cut,
    #     # "transmision_image": t_im,
    #     "iterations": iterations,
    #     "mu_max": mu_max,
    #     "weight": weight,
    #     "sigmaN": sigmaN, 
    #     "led_positions": led_positions,
    #     "wavelength": wavelength, 
    #     "sample_position": sample_position, 
    #     "fourier_pixel_factor": fourier_pixel_factor,
    #     "leds_number_x": leds_number_x,
    #     "leds_number_y": leds_number_y,
    #     "numb_external_leds_discarded_row_column_x": numb_external_leds_discarded_row_column_x,
    #     "numb_external_leds_discarded_row_column_y": numb_external_leds_discarded_row_column_y,
    #     "numb_internal_leds_discarded_row_column": numb_internal_leds_discarded_row_column,
    #     "led_spacing_error": led_spacing_error,
    #     "x_offset": x_offset,
    #     "y_offset": y_offset, 
    #     "led_alpha": led_alpha,
    #     "led_beta": led_beta,
    #     "led_gamma": led_gamma,
    #     "sample_beta": sample_beta,
    #     "h_error": h_error
    # }
    # return recovery_errs_df


recontruction_pipeline_real_images(
        0,
        # output_filedir, 
        input_filedir, 
        # transmission_image,
        # mag_image, 
        # phase_image,
        iterations,
        mu_max,
        weight,
        sigmaN, 
        led_positions,
        wavelength, 
        numerical_aperture, 
        pixel_size, 
        magnification, 
        central_led, 
        sample_height,
        # max_angle,
        # ratio_LR,
        sample_position, 
        leds_number_x,
        leds_number_y,
        numb_external_leds_discarded_row_column_x,
        numb_external_leds_discarded_row_column_y,
        numb_internal_leds_discarded_row_column,
        extra_leds_for_max_angle,
        0,
        0.004,
        0.002, 
        0,
        0,
        0,
        0,
        -0.002)