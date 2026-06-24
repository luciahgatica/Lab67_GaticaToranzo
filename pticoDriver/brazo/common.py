from numbers import Number
import os
import pathlib
from typing import Generator, Callable, NewType
from matplotlib import pyplot as plt
from matplotlib.pyplot import cm
import numpy as np
import numpy.typing as npt
from PIL import Image
from skimage import transform as skt
import math
from tqdm import tqdm

# FPF reconvierte de frecuencias a espacio de LED vector k en (.,.,.) corresponde LED (.,.)
#. Es lo que hacían con Poincare? 
#. Están definiendo tipos para usar después? 
#. Son sólo de chequeo o cumplen alguna función espécifica?
#. Diferencia entre type sólo y NewType?
type PixelPosition = tuple[int, int] | npt.NDArray[np.int_]
type Vector2 = tuple[float, float] 
type Vector3 = tuple[float, float, float]
RealSpace3 = NewType("RealSpace3", Vector3)
FourierSpace3 = NewType("FourierSpace3", Vector3)
FourierPixel2 = NewType("FourierPixel2", Vector2)
FourierImage = NewType("FourierImage", npt.NDArray[np.complex64]) # Es array de vectores?

#. No entendemos esto: led_positions: dict[tuple[int, int], RealSpace3] ¿Cuáles son las keys acá? ¿Qué estructura tiene led_positions? ¿Qué tipo de objeto es?
#. Esperaría que tenga la forma 
'''
led_positions: {'(1, 1)' : [pos, pos, pos],
                '(1, 2)' : [pos, pos, pos],
                ...
                }
'''
#. son los parámetros que definen a la geometría del arreglo del LEDs a usar?
#. dc_location? Es el centro?
#. fourier_pixel_factor era necesario para hacer el mapeo a posiciones, qué cuantifica exactamente? 
#. qué te dice k_indices?
def calculate_k_vectors_k_indices(led_positions: dict[tuple[int, int], RealSpace3],
                                wavelength, sample_position, dc_location, fourier_pixel_factor) -> (dict, dict):
    k_vectors = {}
    k_pixels = {}
    k_indices = {}
    #. Estan heredando las keys de led_positions y definiendo los values a partir de cada for?
    for key, led_position in led_positions.items():
        k_vectors[key] = calculate_k_vector(led_position, wavelength, sample_position, 0)
    for key, k_vector in k_vectors.items():
        k_pixels[key] = dc_location + k_vector[:2] / (2 * np.pi * fourier_pixel_factor) 
    for key, k_pixel in k_pixels.items():
        k_indices[key] = construir_indices(k_pixel) # coordenada en pixeles
    return k_vectors, k_indices

#. Es lo que deberíamos cambiar para implementar el brazo?
def calculate_led_position_square_matrix(
    m: int, n: int, 
    central_led: tuple[int, int],
    matrix_center: RealSpace3, led_spacing: float, 
    # tilt angles
    ) -> RealSpace3:
    """Calcula la posicion del LED dada las propiedades de la matriz
    """
    x_led = (m - central_led[0]) * led_spacing + matrix_center[0]
    y_led = (n - central_led[1]) * led_spacing + matrix_center[1]

    return (x_led, y_led, matrix_center[2])

def calculate_k_vector(led_position: RealSpace3, wavelength: float, sample_position: RealSpace3, h_error) -> FourierSpace3:
    """Calcula el vector k (en dimensiones fisicas) dado un led encendido.
    """

    coordenadas = np.asarray(sample_position) + np.asarray((0,0,h_error)) - np.asarray(led_position)

    r = np.linalg.norm(coordenadas)

    vector_de_onda = (2*np.pi / wavelength) * coordenadas / r

    return vector_de_onda

#. Esta fución se adaptaría con el brazo?
#. Qué es lr_shape? Tiene que ver con la apertura numérica?
def calculate_fourier_pixel_factor(
    pixel_size: float,
    magnification: float,
    lr_shape: tuple[int, int],
    ) -> float:

    assert lr_shape[0] == lr_shape[1], "The image is not square"
    fourier_pixel_factor = magnification / (lr_shape[0]*pixel_size)
    return fourier_pixel_factor

"""
Modificamos :
    
angles = np.arctan2(deltas,sample_heigth) ->  angles = np.arctan2(deltas,z_led)

pues pasar al origen sobre la muestra da una división por cero que hace que los valores se calculen mal
para implementarlo tomamos explicitamente las posiciones de cada led y recalculamos deltas
"""
def calulate_max_angle(led_positions: dict[tuple[int, int], RealSpace3], central_led: tuple[int, int]) -> float:
    x_led = np.array(list(led_positions.values()))[:,0]
    y_led = np.array(list(led_positions.values()))[:,1]
    z_led = np.array(list(led_positions.values()))[:,2]
    
    deltas = (x_led - np.asarray(led_positions[central_led][0]), y_led - np.asarray(led_positions[central_led][1])) 
    angles = np.arctan2(deltas,z_led)
    return np.max((angles))

#. Cuál es max_angle? angulo con el led más lejos 
def calculate_LR_ratio(numerical_aperture:float, max_angle: float) -> float:
    LR_ratio = numerical_aperture / np.sin(max_angle)
    return LR_ratio

# simula ser el objetivo
#. Qué es la pupila en este caso?
def create_pupil(pupil_radio: int, lr_shape: tuple[int, int]) ->  npt.NDArray[np.bool]:
    center = int(lr_shape[0]/2), int(lr_shape[1]/2)
    Y, X = np.ogrid[:lr_shape[1], :lr_shape[0]] 
    dist_from_center2 = (X - center[0])**2 + (Y-center[1])**2
    pupil = dist_from_center2 < pupil_radio**2
    return pupil 

def calculate_led_positions_equi(leds_number_x: int, leds_number_y: int ,led_spacing: float,
                            matrix_center: RealSpace3) -> dict [tuple[int, int], RealSpace3]:
    led_positions = {}
    central_led = ((leds_number_x + 1)/ 2 , (leds_number_y +1) / 2)
    for i in range(1,leds_number_x+1):
        for j in range(1,leds_number_y+1):
            led_positions[(i,j)] = calculate_led_position_square_matrix(i, j, central_led, matrix_center, led_spacing)
    return led_positions

#. Aca se pasa a esféricas?
#. RE-VER
def calculate_led_positions_no_equi(
        k_distributions: dict, central_led: tuple, sample_heigth: float, wavelength: float,
        matrix_center: RealSpace3) -> dict [tuple[int, int], RealSpace3]:
    led_positions = {}
    k_distributions_r3 = {}
    for key, k_vector in k_distributions.items():
        kz = np.sqrt((2*np.pi/wavelength)**2 - (k_vector[0])**2 - (k_vector[1])**2)
        k_distributions_r3[key] = -1 * np.asarray(k_vector) + np.asarray((0,0,kz))
    for key, k_vector in k_distributions_r3.items():
        k_magnitude = np.linalg.norm(k_vector)
    
        if k_magnitude == 0:
            led_positions[key] = np.asarray((0,0,0))
        else:
            r_magnitude = k_magnitude * sample_heigth / k_vector[2]
            r_vector = - (r_magnitude / k_magnitude) * k_vector  # Direccionamos con la normalización de k
    
            led_position = r_vector + np.asarray((0,0,sample_heigth))
            led_positions[key] = led_position
    return led_positions

#. Por qué es necesaria? No podes usar las keys del led_positions y listo?
def construir_indices(k_pixel) -> npt.NDArray[np.int16]:
    axs0 = math.floor(k_pixel[0])
    axs1 = math.floor(k_pixel[1])
    # maximum_value_x, minimum_value_x = round((hr_shape[0])*3/4), round((hr_shape[0])/4)
    # maximum_value_y, minimum_value_y = round((hr_shape[1])*3/4), round((hr_shape[1])/4)
    
    # if axs0 < minimum_value_x or axs0 > maximum_value_x or axs1 < minimum_value_y or axs1 > maximum_value_y:
    #     pass
    # else:
    mask = np.stack((axs0, axs1)).T
    return mask

def read_into_complex_image(mag_filename: str | pathlib.Path, phase_filename: str | pathlib.Path) -> npt.NDArray[np.complex64]:    
    """Read two monochrome image files corresponding to magnitude and phase and
    generate an complex image.
    """
    magnitude = plt.imread(str(mag_filename)).astype(np.float64)
    phase = plt.imread(str(phase_filename)).astype(np.float64)
    #. Por qué hace falta estos 3 pasos modificando la fase?
    phase = phase - np.min(phase)
    phase = phase / np.max(phase)
    phase = phase * np.pi / 2
    return magnitude * np.exp(1j * phase)

#. No entiendo lo que hace esta función
def linear_operator(xx: npt.NDArray[np.complex64],
                     indices: dict[tuple[int, int], tuple[int, int]],
                     lr_shape: tuple[int, int], 
                     pupil: npt.NDArray[np.uint8]
                     )-> npt.NDArray[np.complex64]: 
    """Linear transform of the signal.

    Parameters
    ----------
    xx
        original signal (HR spectrum)
    masks
        each point indicates the index of the left-upper point of the LR image in the HR spectrum
    n0_LR, n1_LR
        the pixel numbers of xx_c (LR) in two dimensions
    pupil

    Returns
    -------
    sampling output
    """   

    xx_c = {} 
    n0_LR, n1_LR = lr_shape
    for key, (ndx0, ndx1) in indices.items(): 
        s0 = safe_slice(ndx0, n0_LR, 0, xx.shape[0])
        s1 = safe_slice(ndx1, n1_LR, 0, xx.shape[0])
        xx_c[key] = xx[s0, s1] * pupil
    for key in xx_c:
        xx_c[key] = np.fft.ifft2(np.fft.ifftshift(xx_c[key], axes=(0, 1)), axes=(0, 1))
    return xx_c

def simulate(
        obj: npt.NDArray[np.complex64], 
        lr_shape: tuple[int, int], # Qué es?
        lr_pupil_radio: int, # Qué es?
        indices: dict[tuple[int, int], tuple[int, int]]
    ) -> npt.NDArray[np.complex64]:
    """Given an object transmission, the ratio between low and high resolution and the 'masks' 

    return the acquired data, maximum value and the pupil.
    """
    pupil = create_pupil(lr_pupil_radio, lr_shape)

    objf = np.fft.fftshift(np.fft.fft2(obj))

    xx_c = linear_operator(objf, indices, lr_shape, pupil)
    y = {}
    for key in xx_c:
        y[key] = np.abs(xx_c[key]) ** 2

    y_original_max = np.max(y)

    # Esto es problematico porque puede dar negativo. Cambiar a rudio de poisson.
    # y = np.random.normal(y, sigmaN)
    return y, pupil

#. Qué son n0_LR y n1_LR? de qué minimun/maximun_value son extremos?
def safe_slice(start: int, n0_LR: int, minimun_value: int, maximum_value: int):
    start = max(start, minimun_value)
    stop = start + n0_LR
    
    if stop > maximum_value:
        stop = maximum_value
        start = stop - n0_LR
    
    return slice(start, stop)

#. Qué se hace acá?
def sum_pupils(hr_shape: tuple[int, int], lr_shape: tuple[int, int], radio:float, indices: dict[tuple[int,int], tuple[int, int]]):
    matriz_ceros = np.zeros(hr_shape)
    pupil = create_pupil(radio, lr_shape)
    n0_LR, n1_LR = lr_shape
    for key, (ndx0, ndx1) in indices.items():
        s0 = safe_slice(ndx0 - (n0_LR+1) // 2, n0_LR, 0, hr_shape[0])
        s1 = safe_slice(ndx1 - (n1_LR+1) // 2, n1_LR, 0, hr_shape[1])
        if s0 is None or s1 is None:
            pass
        else:
            matriz_ceros[s0, s1] += pupil
    return matriz_ceros

import ast
def save_images(data, carpeta):
    filedir = pathlib.Path(carpeta)
    for key, array in data.items():
        if isinstance(key, str):
            key = ast.literal_eval(key)
        nombre = f"point_{str(key[0]).zfill(3)}_{str(key[1]).zfill(3)}"
        np.save(filedir / nombre, array)

def save_images_2(data, carpeta):
    filedir = pathlib.Path(carpeta)
    for key, array in data.items():
        nombre = f"iteracion_{str(key)}"
        np.save(filedir / nombre, array)

#. Reconstruye la imágen HR?
def inverse_linear_operator(xx_c: npt.NDArray[np.complex64],
                             indices: npt.NDArray[np.intp],
                             hr_shape: tuple[int, int],
                             pupil: npt.NDArray[np.uint8]
                             )-> npt.NDArray[np.complex64]:
    """Inverse linear transform of the signal.

    Parameters
    ----------
    xx_c
        sampling output
    masks
        each point indicates the index of the left-upper point of the LR image in the HR spectrum
    n0, n1
        the pixel numbers of xx_mean_large (HR) in two dimensions
    pupil

    Returns
    -------
    original signal (HR spectrum).
    """

    n0_LR, n1_LR, L = xx_c.shape
    indices_stack = np.asarray(list(indices.values())) 
    xx_c = np.fft.fftshift(np.fft.fft2(xx_c, axes=(0, 1)), axes=(0, 1))
    mn0, mn1 = np.min(indices_stack, axis=0)
    mx0, mx1 = np.max(indices_stack, axis=0)

    xx = np.zeros(
        (mx0 - mn0 + n0_LR,
         mx1 - mn1 + n1_LR,
         L), dtype = np.complex64
         )

    for k in range(L):
        ndx0 = indices_stack[k, 0]
        ndx1 = indices_stack[k, 1]

        s0 = slice(ndx0 - mn0, ndx0 + n0_LR - mn0)
        s1 = slice(ndx1 - mn1, ndx1 + n1_LR - mn1)
        
        xx[s0, s1, k] = xx_c[:, :, k] * np.conj(pupil)
    
    xx_mean = np.mean(xx, axis=2)
    xx_mean_large = np.zeros((hr_shape), dtype=np.complex64)

    s0 = slice(mn0, mn0 + xx_mean.shape[0])
    s1 = slice(mn1, mn1 + xx_mean.shape[1])
    xx_mean_large[s0, s1] = xx_mean

    return xx_mean_large

def quality(x: npt.NDArray[np.complex64], target: npt.NDArray[np.complex64]) -> float:
    """Calculate the quality of the reconstruction by comparing 
    the reconstruction to the target value.
    """
    return np.sum(np.abs(np.abs(x) - np.abs(target))) / np.sum(np.abs(target))

import numpy as np
import numpy.typing as npt

#. Por qué calcular correlaciones con np.corrcoef y no con otro cuantificador?
#. Capaz es una pregunta medio de gede igual :(
def quality_dict(x: npt.NDArray[np.complex64], target: npt.NDArray[np.complex64]) -> dict:
    """Calculate the quality of the reconstruction by comparing 
    the reconstruction to the target value.
    Returns a dictionary with relative errors and correlations.
    """
    mag_x = np.abs(x)
    mag_target = np.abs(target)

    phase_x = np.angle(x)
    phase_target = np.angle(target)

    # Aplanar para correlaciones
    mag_corr = np.corrcoef(mag_x.ravel(), mag_target.ravel())[0, 1]
    phase_corr = np.corrcoef(phase_x.ravel(), phase_target.ravel())[0, 1]

    return {
        "magnitud": np.sum(np.abs(mag_x - mag_target)) / np.sum(mag_target),
        "fase_reconstruida": np.sum(phase_x),
        "fase_target": np.sum(phase_target),
        "fase": np.sum(np.abs(np.angle(x * np.conj(target)))) / np.sum(np.abs(phase_target)),
        "corr_magnitud": mag_corr,
        "corr_fase": phase_corr
    }

#. Qué ecuaciones sigue? Las de Bian 2016?
#. Qué función se usa para reconstruir en cada caso? reconstruct o reconstruct_real_images? Criterio?
def reconstruct(recovery_error_required,
        data: dict[tuple[int, int],npt.NDArray[np.float64]],
        hr_shape: tuple[int, int],
        sigma2: float, 
        indices: npt.NDArray[np.intp],
        pupil: npt.NDArray[np.uint8],
        iterations: int,
        mu_max: float, 
        weight: float,
        target: npt.NDArray[np.complex64],
        on_iteration: Callable[[int, npt.NDArray[np.complex64]], None]
        ) -> tuple[npt.NDArray[np.complex64], npt.NDArray[np.complex64], npt.NDArray[np.float64]]: 
    """
    Algorithm 1: TPWFP algorithm for FP reconstruction. 
    Input: linear transform matrix A, measurement vector c, and initialization z(0). 
    Ouput: retrieved complex signal z (the sample’s HR spatial spectrum). 
    1. k= 0;
    2. while not converged do
    3. Update ξ according to Eq. (9);
    4. Update μ(k+1) according to Eq. (12);
    5. Update z(k+1) according to Eq. (11);
    6. k :=k+ 1.
    7. end
    
    Parameters
    ----------
    data
        captured LR images (shape: n1_LR, n2_LR, L);
    n0, n1
        the pixel numbers of im_r (HR) in two dimensions.
    sigma2
        variance of additive noise.
    masks
        L * 2 (each point indicates the index of the left-upper point of the LR image in the HR spectrum).
    pupil
        the pupil function.
    iterations
        the number of iterations.
    mu_max
        the stepsize parameter.
    weight
        the weighting parameter. 
    newfolder
        folder for saving results.
    target
        original benchmark HR spectrum for calculating recovery error.

    Returns
    -------
    z0, final recovered image, recovery erros vs iterations
    """
    n0, n1, L = data.shape
    lr_shape = int(n0), int(n1)
    #. Qué diferencia hay entre estos dos z_im?
    z_im = np.sqrt(data[:,:,int(np.fix(L/2))]) * lr_shape[0] * lr_shape[1] / hr_shape[0] / hr_shape[1] 
    # z_im = np.sqrt(data[:, :, int(np.fix(L / 2))]) * n0_LR * n1_LR / n0 / n1

    z_im = skt.resize(z_im, hr_shape) 
    z0 = np.fft.fftshift(np.fft.fft2(z_im))
    z = z0

    recovery_errs = np.zeros(iterations)
    recovery_errs[0] = quality(z, target)
    N = np.zeros(data.shape)
    epsilon = N
    normest = np.sqrt(np.sum(data) / L / lr_shape[0] / lr_shape[1])
    
    step_size_n = 0.01
    alpha = - np.log(0.997) # De donde sale este valor?

    ## Si se necesitan recopilar imágenes intermedias
    imagenes_magnitud_200_300 = {}
    imagenes_fase_200_300 = {}
    recovery_errs_records = []
    #. Qué esta pasando en este for?????
    for ndx in tqdm(range(1, iterations)):

        # update z
        Bz = linear_operator(z, indices, lr_shape, pupil)
        Bz_array = np.stack([Bz[key] for key in sorted(Bz.keys())], axis=-1)
        Cz = (np.abs(Bz_array) ** 2 + N - data) * Bz_array  #eq 9 Bian 2016
        w = inverse_linear_operator(Cz, indices, hr_shape, pupil) #eq 10 Bian 2016 truncated Wirtinger gradient 
        
        mu = 1 - np.exp(- alpha * ndx)  
        mu = min(mu, mu_max) / normest ** 2 #eq 12 Bian 2016

        z = z - mu * w  #eq 11 Bian 2016

        # update N
        CN = (np.abs(Bz_array) ** 2 + N - data) + weight * (N * N - 9 * sigma2 + epsilon * epsilon) * 2.0 * N
        step_n = mu * step_size_n
        N = N - step_n * CN
        
        # update epsilon
        e_temp = 9 * sigma2 - N * N
        e_temp[e_temp < 0] = 0
        epsilon = np.sqrt(e_temp)
        recovery_errs[ndx] = quality(z, target)

        qd = quality_dict(z, target)
        qd["recovery_err"] = recovery_errs[ndx]

        recovery_errs_records.append(qd)
        on_iteration(ndx, z)


        # Si en un quinto de las iteraciones no llega a un error de corte se interrumpe el ciclo
        if recovery_error_required != 0:

            if recovery_errs[round(iterations * 1/ 9)] > (recovery_error_required + 0.10 * recovery_error_required):
                recovery_errs[round(iterations * 1 / 9):] = recovery_errs[ndx]
                break  

            # if recovery_errs[round(iterations * 1/ 9)] > (recovery_error_required):
            #     recovery_errs[round(iterations * 1 / 9):] = recovery_errs[ndx]
            #     break  

            if recovery_errs[round(iterations * 1/ 3)] > (recovery_error_required):
                recovery_errs[round(iterations * 1 / 3):] = recovery_errs[ndx]
                break   

            # if recovery_errs[round(iterations * 1 / 3)] > (recovery_error_required - 0.10 * recovery_error_required):
            #     recovery_errs[round(iterations * 1 / 3):] = recovery_errs[ndx]
            #     break  

            if recovery_errs[round(iterations * 3 / 5)] > (recovery_error_required - 0.10 * recovery_error_required):
                recovery_errs[round(iterations * 3 / 5):] = recovery_errs[ndx]
                break   

            # if recovery_errs[round(iterations * 3 / 5)] > (recovery_error_required - 0.30 * recovery_error_required):
            #     recovery_errs[round(iterations * 3 / 5):] = recovery_errs[ndx]
            #     break   

            # Si en un quinto de las iteraciones no llega a un error de corte se interrumpe el ciclo
            if recovery_errs[round(iterations * 9/ 10)] > (recovery_error_required - 0.9 * recovery_error_required):
                recovery_errs[round(iterations * 9 / 10):] = recovery_errs[ndx]
                break   

        # ## Si se necesitan recopilar imágenes intermedias
        # if ndx > 240 and ndx < 399:
        #     imagen = np.fft.ifft2(np.fft.ifftshift(z))
        #     imagenes_magnitud_200_300[ndx] = np.abs(imagen)
        #     imagenes_fase_200_300[ndx] = np.angle(imagen)
        # Si necesitamos saber la velocidad con la que llega a cierto error
        # if recovery_errs[ndx] < 0.85:
        #     print (f"Iteracion {ndx}")
    im_r = np.fft.ifft2(np.fft.ifftshift(z))

    # ## Si se necesitan recopilar imágenes intermedias
    # carpeta_magnitud = "/home/chanoscopio/Documents/LucasC/code/ptyco-full-simulator/test/results/200_a_300_iteraciones/magnitud"
    # carpeta_fase = "/home/chanoscopio/Documents/LucasC/code/ptyco-full-simulator/test/results/200_a_300_iteraciones/fase"
    # save_images_2(imagenes_magnitud_200_300, carpeta_magnitud)
    # save_images_2(imagenes_fase_200_300, carpeta_fase)
    # ##

    return z0, im_r, recovery_errs_records

def reconstruct_real_images(
        recovery_error_cut,
        data: np.ndarray,  # ahora float32
        hr_shape: tuple[int, int],
        sigma2: float,
        indices: np.ndarray,
        pupil: np.ndarray,
        iterations: int,
        mu_max: float,
        weight: float,
        on_iteration: Callable[[int, np.ndarray], None]
    ) -> tuple[np.ndarray, np.ndarray]:

    """
    Optimized TPWFP algorithm for FP reconstruction (memory friendly).
    Now uses float32 and complex64 to reduce memory footprint.

    Parameters
    ----------
    data : np.ndarray (float32)
        captured LR images (shape: n1_LR, n2_LR, L);
    hr_shape : tuple[int,int]
        size of reconstructed HR image
    sigma2 : float
        variance of additive noise.
    indices : np.ndarray
        frequency indices for reconstruction
    pupil : np.ndarray
        pupil function.
    iterations : int
        number of iterations.
    mu_max : float
        stepsize parameter.
    weight : float
        weighting parameter.
    on_iteration : Callable
        callback for each iteration

    Returns
    -------
    z0 : complex64
        initial HR spectrum
    im_r : complex64
        final recovered image (HR)
    """

    # --- Ensure input is float32 ---
    data = data.astype(np.float32)

    n0, n1, L = data.shape 
    lr_shape = (int(n0), int(n1))

    # Inicialización z_im → HR size
    z_im = np.sqrt(data[:, :, int(np.fix(L/2))], dtype=np.float32) * \
           (lr_shape[0] * lr_shape[1]) / (hr_shape[0] * hr_shape[1])

    # Resize to HR shape
    z_im = skt.resize(z_im, hr_shape).astype(np.float32)

    # FFT inicial en precision simple
    z0 = np.fft.fftshift(np.fft.fft2(z_im.astype(np.complex64)))
    z = z0.copy()

    # Arrays auxiliares en float32
    recovery_errs = np.zeros(iterations, dtype=np.float32)
    N = np.zeros(data.shape, dtype=np.float32)
    epsilon = np.zeros_like(N, dtype=np.float32)

    # Norm estimation también en float32
    normest = np.sqrt(np.sum(data, dtype=np.float64) / L / lr_shape[0] / lr_shape[1]).astype(np.float32)

    step_size_n = np.float32(0.01)
    alpha = np.float32(- np.log(0.997))

    # Si se necesitan imágenes intermedias (desactivado por ahora)
    # imagenes_magnitud_200_300 = {}
    # imagenes_fase_200_300 = {}

    for ndx in tqdm(range(1, iterations)):

        # update z (linear operator)
        Bz = linear_operator(z, indices, lr_shape, pupil)

        # Convertimos a complex64 para ahorrar memoria
        Bz_array = np.stack([Bz[key] for key in sorted(Bz.keys())], axis=-1).astype(np.complex64)

        # Cz = (|Bz|^2 + N - data) * Bz  (en precision simple)
        abs_Bz_sq = np.abs(Bz_array)**2  # float32
        Cz = (abs_Bz_sq + N - data).astype(np.float32) * Bz_array  # complex64

        # Wirtinger gradient
        w = inverse_linear_operator(Cz, indices, hr_shape, pupil).astype(np.complex64)

        # step mu en float32
        mu = np.float32(1 - np.exp(-alpha * ndx))
        mu = np.minimum(mu, mu_max) / (normest ** 2)

        # update z en complex64
        z = z - mu * w

        # update N
        CN = (abs_Bz_sq + N - data) + weight * (N * N - 9 * sigma2 + epsilon * epsilon) * np.float32(2.0) * N
        step_n = mu * step_size_n
        N = N - step_n * CN

        # update epsilon
        e_temp = 9 * sigma2 - N * N
        e_temp[e_temp < 0] = 0
        epsilon = np.sqrt(e_temp, dtype=np.float32)

        # Callback opcional
        on_iteration(ndx, z)

    # Recovered HR image (IFFT en complex64)
    im_r = np.fft.ifft2(np.fft.ifftshift(z.astype(np.complex64))).astype(np.complex64)

    return z0.astype(np.complex64), im_r.astype(np.complex64)

#. Tiene alguna ventaja como más cifras en cada número?
"""funcion sin optimizar la memoria RAM"""
# def reconstruct_real_images(recovery_error_cut,
#         data: dict[tuple[int, int],npt.NDArray[np.float64]],
#         hr_shape: tuple[int, int],
#         sigma2: float,
#         indices: npt.NDArray[np.intp],
#         pupil: npt.NDArray[np.uint8],
#         iterations: int,
#         mu_max: float,
#         weight: float,
#         on_iteration: Callable[[int, npt.NDArray[np.complex64]], None]
#         ) -> tuple[npt.NDArray[np.complex64], npt.NDArray[np.complex64], npt.NDArray[np.float64]]: 
#     """
#     Algorithm 1: TPWFP algorithm for FP reconstruction. 
#     Input: linear transform matrix A, measurement vector c, and initialization z(0). 
#     Ouput: retrieved complex signal z (the sample’s HR spatial spectrum). 
#     1. k= 0;
#     2. while not converged do
#     3. Update ξ according to Eq. (9);
#     4. Update μ(k+1) according to Eq. (12);
#     5. Update z(k+1) according to Eq. (11);
#     6. k :=k+ 1.
#     7. end
    
#     Parameters
#     ----------
#     data
#         captured LR images (shape: n1_LR, n2_LR, L);
#     n0, n1
#         the pixel numbers of im_r (HR) in two dimensions.
#     sigma2
#         variance of additive noise.
#     masks
#         L * 2 (each point indicates the index of the left-upper point of the LR image in the HR spectrum).
#     pupil
#         the pupil function.
#     iterations
#         the number of iterations.
#     mu_max
#         the stepsize parameter.
#     weight
#         the weighting parameter.
#     newfolder
#         folder for saving results.
#     target
#         original benchmark HR spectrum for calculating recovery error.

#     Returns
#     -------
#     z0, final recovered image, recovery erros vs iterations
#     """
#     n0, n1, L = data.shape
#     lr_shape = int(n0), int(n1)
#     z_im = np.sqrt(data[:,:,int(np.fix(L/2))]) * lr_shape[0] * lr_shape[1] / hr_shape[0] / hr_shape[1] 
#     # z_im = np.sqrt(data[:, :, int(np.fix(L / 2))]) * n0_LR * n1_LR / n0 / n1

#     z_im = skt.resize(z_im, hr_shape) 
#     z0 = np.fft.fftshift(np.fft.fft2(z_im))
#     z = z0

#     recovery_errs = np.zeros(iterations)
#     N = np.zeros(data.shape)
#     epsilon = N
#     normest = np.sqrt(np.sum(data) / L / lr_shape[0] / lr_shape[1])
    
#     step_size_n = 0.01
#     alpha = - np.log(0.997)

#     ## Si se necesitan recopilar imágenes intermedias
#     imagenes_magnitud_200_300 = {}
#     imagenes_fase_200_300 = {}
#     recovery_errs_records = []
#     for ndx in tqdm(range(1, iterations)):

#         # update z
#         Bz = linear_operator(z, indices, lr_shape, pupil)
#         Bz_array = np.stack([Bz[key] for key in sorted(Bz.keys())], axis=-1)
#         Cz = (np.abs(Bz_array) ** 2 + N - data) * Bz_array  #eq 9 Bian 2016
#         w = inverse_linear_operator(Cz, indices, hr_shape, pupil) #eq 10 Bian 2016 truncated Wirtinger gradient 
        
#         mu = 1 - np.exp(- alpha * ndx)  
#         mu = min(mu, mu_max) / normest ** 2 #eq 12 Bian 2016

#         z = z - mu * w  #eq 11 Bian 2016

#         # update N
#         CN = (np.abs(Bz_array) ** 2 + N - data) + weight * (N * N - 9 * sigma2 + epsilon * epsilon) * 2.0 * N
#         step_n = mu * step_size_n
#         N = N - step_n * CN
        
#         # update epsilon
#         e_temp = 9 * sigma2 - N * N
#         e_temp[e_temp < 0] = 0
#         epsilon = np.sqrt(e_temp)


#         on_iteration(ndx, z)


#         # Si en un quinto de las iteraciones no llega a un error de corte se interrumpe el ciclo
#         # if recovery_error_required != 0:

#         #     if recovery_errs[round(iterations * 1/ 9)] > (recovery_error_required + 0.10 * recovery_error_required):
#         #         recovery_errs[round(iterations * 1 / 9):] = recovery_errs[ndx]
#         #         break  

#         #     # if recovery_errs[round(iterations * 1/ 9)] > (recovery_error_required):
#         #     #     recovery_errs[round(iterations * 1 / 9):] = recovery_errs[ndx]
#         #     #     break  

#         #     if recovery_errs[round(iterations * 1/ 3)] > (recovery_error_required):
#         #         recovery_errs[round(iterations * 1 / 3):] = recovery_errs[ndx]
#         #         break   

#         #     # if recovery_errs[round(iterations * 1 / 3)] > (recovery_error_required - 0.10 * recovery_error_required):
#         #     #     recovery_errs[round(iterations * 1 / 3):] = recovery_errs[ndx]
#         #     #     break  

#         #     if recovery_errs[round(iterations * 3 / 5)] > (recovery_error_required - 0.10 * recovery_error_required):
#         #         recovery_errs[round(iterations * 3 / 5):] = recovery_errs[ndx]
#         #         break   

#             # if recovery_errs[round(iterations * 3 / 5)] > (recovery_error_required - 0.30 * recovery_error_required):
#             #     recovery_errs[round(iterations * 3 / 5):] = recovery_errs[ndx]
#             #     break   

#             # Si en un quinto de las iteraciones no llega a un error de corte se interrumpe el ciclo
#             # if recovery_errs[round(iterations * 9/ 10)] > (recovery_error_required - 0.9 * recovery_error_required):
#             #     recovery_errs[round(iterations * 9 / 10):] = recovery_errs[ndx]
#             #     break   

#         # ## Si se necesitan recopilar imágenes intermedias
#         # if ndx > 240 and ndx < 399:
#         #     imagen = np.fft.ifft2(np.fft.ifftshift(z))
#         #     imagenes_magnitud_200_300[ndx] = np.abs(imagen)
#         #     imagenes_fase_200_300[ndx] = np.angle(imagen)
#         # Si necesitamos saber la velocidad con la que llega a cierto error
#         # if recovery_errs[ndx] < 0.85:
#         #     print (f"Iteracion {ndx}")
#     im_r = np.fft.ifft2(np.fft.ifftshift(z))

#     # ## Si se necesitan recopilar imágenes intermedias
#     # carpeta_magnitud = "/home/chanoscopio/Documents/LucasC/code/ptyco-full-simulator/test/results/200_a_300_iteraciones/magnitud"
#     # carpeta_fase = "/home/chanoscopio/Documents/LucasC/code/ptyco-full-simulator/test/results/200_a_300_iteraciones/fase"
#     # save_images_2(imagenes_magnitud_200_300, carpeta_magnitud)
#     # save_images_2(imagenes_fase_200_300, carpeta_fase)
#     # ##

#     return z0, im_r


def convertir_matrices_a_imagenes(input_folder, output_folder):
    # Crear la carpeta de salida si no existe
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Recorrer todos los archivos en la carpeta de entrada
    for filename in os.listdir(input_folder):
        if filename.endswith('.npy'):
            # Cargar la matriz
            matriz = np.load(os.path.join(input_folder, filename))
            
            # Normalizar los valores para que estén en el rango 0-255 (si es necesario)
            matriz_normalizada = (255 * (matriz - np.min(matriz)) / (np.max(matriz) - np.min(matriz))).astype(np.uint8)

            # Convertir la matriz normalizada a imagen y guardarla
            imagen = Image.fromarray(matriz_normalizada)
            nombre_salida = os.path.splitext(filename)[0] + '.png'
            imagen.save(os.path.join(output_folder, nombre_salida))
            print(f'Imagen guardada como {nombre_salida}')


def euler_angles_incorporated(a: float, b: float, g: float, coordenadas: RealSpace3):
    """Trabajamos con la rotación extrínseca de los ángulos de Euler siguiendo las rotaciones alrededor de ejes fijos, primero sobre z con gamma, luego en y con beta y finalmente en x con alpha.
    """
    alpha = (-1) * np.deg2rad(a)
    beta = (-1) * np.deg2rad(b)
    gamma = (-1) * np.deg2rad(g)
    x, y, z = coordenadas
    #. preguntar
    x_led = (np.cos(beta) * np.cos(gamma)) * x + (np.sin(alpha) * np.sin(beta) * np.cos(gamma) - np.cos(alpha) * np.sin(gamma)) * y + (np.cos(alpha) * np.sin(beta) * np.cos(gamma) + np.sin(alpha) * np.sin(gamma)) * z
    y_led = (np.cos(beta) * np.sin(gamma)) * x + (np.sin(alpha) * np.sin(beta) * np.sin(gamma) + np.cos(alpha) * np.cos(gamma)) * y + (np.cos(alpha) * np.sin(beta) * np.sin(gamma) - np.sin(alpha) * np.cos(gamma)) * z
    z_led = (-np.sin(beta)) * x     + (np.sin(alpha) * np.cos(beta)) * y              + (np.cos(alpha) * np.cos(beta)) * z

    return (x_led, y_led, z_led)

def sample_tilt_incorporated(vector_de_onda: FourierSpace3, tilt: float):
    beta = (-1) * np.deg2rad(tilt)
    vector = np.asarray((vector_de_onda[0], vector_de_onda[1] * np.cos(beta) + vector_de_onda[2] * np.sin(beta), vector_de_onda[2] * np.cos(beta) - vector_de_onda[1] * np.sin(beta)))
    return vector

def calculate_k_vectors_k_indices_sample_tilt(led_positions: dict[tuple[int, int], RealSpace3],
                                wavelength, sample_position, dc_location, fourier_pixel_factor, sample_tilt, h_error) -> (dict, dict):
    k_vectors = {}
    k_vectors_tilt = {}
    k_pixels = {}
    k_indices = {}
    for key, led_position in led_positions.items():
        k_vectors[key] = calculate_k_vector(led_position, wavelength, sample_position, h_error)
    for key, k_vector in k_vectors.items():
        k_vectors_tilt[key] = sample_tilt_incorporated(k_vector, sample_tilt)    
    for key, k_vector in k_vectors_tilt.items():
        k_pixels[key] = dc_location + k_vector[:2] / (2 * np.pi * fourier_pixel_factor)
    for key, k_pixel in k_pixels.items():
        k_indices[key] = construir_indices(k_pixel)
    return k_vectors_tilt, k_indices

def led_spacing_error_incorporated(led_spacing_error: float, coordenadas: RealSpace3):
    x, y, z = coordenadas   
    x_led = x + np.random.choice([-1, 0, 1]) * led_spacing_error
    y_led = y + np.random.choice([-1, 0, 1]) * led_spacing_error
    z_led = z + np.random.choice([-1, 0, 1]) * led_spacing_error 
    return (x_led, y_led, z_led)

def led_offset_incorporated(x_offset:float, y_offset: float, coordenadas: RealSpace3):
    x, y, z = coordenadas
    x_led = x + x_offset
    y_led = y + y_offset
    z_led = z
    return (x_led, y_led, z_led)

def led_errors_incorporated(led_positions, x_offset, y_offset, led_spacing_error, led_alpha, led_beta, led_gamma):
    led_positions_offset = {}
    for key, coordenada in led_positions.items():
        led_positions_offset[key] = led_offset_incorporated(x_offset, y_offset, coordenada)

    led_positions_failed = {}
    for key, coordenada in led_positions_offset.items():
        led_positions_failed[key] = led_spacing_error_incorporated(led_spacing_error, coordenada)

    led_positions_tilt = {}
    for key, coordenada in led_positions_failed.items():
        led_positions_tilt[key] = euler_angles_incorporated(led_alpha, led_beta, led_gamma, coordenada)
    
    return led_positions_tilt

def plot_convergence(result_list, true_minimum=None, yscale=None, title="Convergence plot"):

    ax = plt.gca()
    ax.set_title(title)
    ax.set_xlabel("Number of calls $n$")
    ax.set_ylabel(r"$\min f(x)$ after $n$ calls")
    ax.grid()
    if yscale is not None:
        ax.set_yscale(yscale)
    colors = cm.hsv(np.linspace(0.25, 1.0, len(result_list)))

    for entry, color in zip(result_list, colors):
        name, results = entry
        n_calls = len(results.x_iters)
        iterations = range(1, n_calls + 1)
        mins = [np.min(results.func_vals[:i]) for i in iterations]
        ax.plot(iterations, mins, c=color, label=name)
        #ax.errorbar(iterations, np.mean(mins, axis=0),
        #             yerr=np.std(mins, axis=0), c=color, label=name)
    if true_minimum:
        ax.axhline(true_minimum, linestyle="--",
                   color="r", lw=1,
                   label="True minimum")
    ax.legend(loc="best")
    return ax

def read_numpy_file(numpy_file):
    pass

def intersection_circles_area(d, R):
    """Return the area of intersection of two circles of radii R and
    their centres are separated by d
    """
    
    R2 = R**2
    x = np.clip(d / (2 * R), -1, 1)
    alpha = np.arccos(x)
    if d >= 2 * R:
        return 0.0
    return (
        2 * R2 * alpha
        - R2 * np.sin(2 * alpha)
    )

def circunf_max_equi_overlap(overlap: int, OTF: int, theta: float, lmbd: float, fourier_pixel_factor: float) -> list:
    '''

    Parameters
    ----------
    overlap : int
        porcentaje de overlap deseado entre OTF en espacio k-px.
    OTF : int
        radio de la OTF en k-px.
    theta : float
        angulo del led más lejano.
    lmbd : float
        longitud de onda de la luz incidente.
    fourier_pixel_factor : float
        factor de conversión - espacio k / fourier_pixel_factor = k pixels

    Returns
    -------
    paso_phi : float
        paso del motor que se toma en la circunferencia más lejana para obtener el overlap deseado

    '''
    
    k = (2 * np.pi) / lmbd
    porcentaje_overlap = 100
    angulos_completos = np.arange(0, 200, 1) * (np.pi / 100)
    
    kx_px_0 = (k / (2 * np.pi * fourier_pixel_factor)) * np.sin(theta) * np.cos(0)
    ky_px_0 = (k / (2 * np.pi * fourier_pixel_factor)) * np.sin(theta) * np.sin(0)
    divisores = [i for i in range(1, len(angulos_completos)+1) if len(angulos_completos) % i == 0]
    
    for div in range(len(divisores)):
        phi_ind = angulos_completos[divisores[div]]
    
        kx_px_ind = (k / (2 * np.pi * fourier_pixel_factor)) * np.sin(theta) * np.cos(phi_ind)
        ky_px_ind = (k / (2 * np.pi * fourier_pixel_factor)) * np.sin(theta) * np.sin(phi_ind)

        d = np.sqrt((kx_px_ind-kx_px_0)**2 + (ky_px_ind-ky_px_0)**2)
        area = np.pi * OTF**2
        porcentaje_overlap = intersection_circles_area(d, OTF) * 100 / area
        
        if porcentaje_overlap < overlap:
            break
        
    paso_motor = divisores[div-1] * (np.pi / 100)
    angulos_motor = np.arange(0, 2 * np.pi, paso_motor)
    return angulos_motor

def calculate_led_positions_brazo_equi(overlap: int, OTF: int, angulos_motor: list, thetas: list, 
                               brazo_radio: float, lmbd: float, fourier_pixel_factor: float) -> RealSpace3:
    
    '''
    Parameters
    ----------
    overlap : int
        porcentaje de overlap deseado entre OTF en espacio k-px.
    OTF : int
        radio de la OTF en k-px.
    angulos_motor : list
        lista de pasos del motor que se toma en la circunferencia más lejana para obtener el overlap deseado
    thetas : list
        angulos de los leds sobre el brazo con el 0 en el led central.
    brazo_radio : float
        radio del brazo en m.
    lmbd : float
        longitud de onda de la luz incidente.
    fourier_pixel_factor : float
        factor de conversión - espacio k / fourier_pixel_factor = k pixels


    Returns
    -------
    led_positions : RealSpace3
        diccionario que etiqueta (theta,phi): (x,y,z).
    '''
    
    k = 2 * np.pi / lmbd
    led_positions = {}
    led_positions[(1,np.int64(0))] = (np.float64(0),np.float64(0),np.float64(brazo_radio))
    divisores = np.array([i for i in range(1, len(angulos_motor)+1) if len(angulos_motor) % i == 0]) 
    area = np.pi * OTF**2

    for i in range(len(thetas)):
        theta_i = thetas[i]
        kx_px_0 = (k / (2 * np.pi * fourier_pixel_factor)) * np.sin(theta_i) * np.cos(0)
        ky_px_0 = (k / (2 * np.pi * fourier_pixel_factor)) * np.sin(theta_i) * np.sin(0)
    
        best_div = divisores[0]
        best_err = 1e9
        
        for div in divisores:
            phi_ind = angulos_motor[div-1]
            kx_px_ind = (k / (2 * np.pi * fourier_pixel_factor)) * np.sin(theta_i) * np.cos(phi_ind)
            ky_px_ind = (k / (2 * np.pi * fourier_pixel_factor)) * np.sin(theta_i) * np.sin(phi_ind)
        
            d = np.sqrt((kx_px_ind-kx_px_0)**2 + (ky_px_ind-ky_px_0)**2)
            ov = intersection_circles_area(d, OTF) * 100 / area
            if np.isnan(ov):
                continue
        
            err = abs(ov - overlap)
            if err < best_err:
                best_err = err
                best_div = div            
        phi_list = angulos_motor[::best_div]

        for ind in range(len(phi_list)):
            # Ojo al etiquetar los pasos. Se cargaron la cantidad de pasos que rellenan la circunferencia
            # exterior. El indice corre distinto para los pasos del motor
            led_positions[(i + 2, ind * (2 * best_div))] = (
                            brazo_radio * np.sin(theta_i) * np.cos(phi_list[ind]),
                            brazo_radio * np.sin(theta_i) * np.sin(phi_list[ind]),
                            brazo_radio * np.cos(theta_i)
                            )
            
    return led_positions