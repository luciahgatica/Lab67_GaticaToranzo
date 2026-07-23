import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns 
from tqdm import tqdm
from PIL import Image
from IPython.display import display
ROOT = r'C:\Users\Lenovo\Desktop\Labo67\repo_git\Simulation' + '\\'
input_filedir = "data_source"

# Defino los cuantificadores a utilizar
def MSEref(mag_orig, phase_orig, mag_rec, phase_rec, px_x0, px_y0):
    original = mag_orig * np.exp(phase_orig)
    reconstruida = mag_rec * np.exp(phase_rec)
    
    original_px0 = original[px_x0][px_y0]
    reconstruida_px0 = reconstruida[px_x0][px_y0]
    return np.mean((np.ravel(np.array(original)/original_px0) - np.ravel(np.array(reconstruida)/reconstruida_px0))**2)

def PINCC(mag_orig, phase_orig, mag_rec, phase_rec):
    original = mag_orig * np.exp(phase_orig)
    reconstruida = mag_rec * np.exp(phase_rec)
    
    suma = 0
    for i in range(len(np.ravel(np.array(original)))):
        suma += np.ravel(original)[i] * np.conjugate(np.ravel(reconstruida)[i])
    return suma / (np.linalg.norm(np.array(original)) * np.linalg.norm(np.array(reconstruida)))

def RE(mag_orig, phase_orig, mag_rec, phase_rec):
    original = mag_orig * np.exp(phase_orig)
    reconstruida = mag_rec * np.exp(phase_rec)
    
    return np.sum(np.abs(np.abs(original) - np.abs(reconstruida))) / np.sum(np.abs(original))

# Creo un selector de métricas a evaluar
def selector(mag_orig, phase_orig, dict_mag_phase_rec, metrica, px_x0=0, px_y0=0):
    
    resultado = {}
    for (leds, itr), (mag_rec, phase_rec) in tqdm(dict_mag_phase_rec.items(), 
                                                  'Calculando metrica'):
        if metrica == 'MSEref':
            resultado[(leds, itr)] = MSEref(mag_orig, phase_orig, mag_rec, 
                                            phase_rec, px_x0, px_y0)
        if metrica == 'PINCC':
            resultado[(leds, itr)] = PINCC(mag_orig, phase_orig, mag_rec, phase_rec)
        
        if metrica == 'RE':
            resultado[(leds, itr)] = RE(mag_orig, phase_orig, mag_rec, phase_rec)
            
        if metrica == 'PearsonAmp':
            resultado[(leds, itr)] = np.corrcoef(np.ravel(mag_orig), np.ravel(mag_rec))[0, 1]
                                      
        if metrica == 'PearsonPhase':
            resultado[(leds, itr)] = np.corrcoef(np.ravel(phase_orig), np.ravel(phase_rec))[0, 1]
            
    return resultado

def graficar_metrica(metrica, metrica_name, leds, colors):
    fig, ax = plt.subplots(figsize=(6,3))
    ax.grid(alpha=0.5)
    ax.set_xscale('log')
    ax.set_xticks([10, 50, 100, 500, 1000, 5000, 10000])
    ax.set_xticklabels([10, 50, 100, 500, 1000, 5000, 10000])
    
    if metrica_name == 'MSEref':
        ax.set_yscale('log')
    
    ax.set_xlabel("Iteraciones")
    ax.set_ylabel(metrica_name)

    for n_leds, c in zip(leds, colors):
        iterations = []
        metrica_list = []

        for (led, it), valor in sorted(metrica.items()):
            if led == n_leds:
                iterations.append(it)
                metrica_list.append(valor)

        if len(iterations) > 0:
            ax.scatter(iterations, metrica_list, color=c)
            ax.plot(iterations, metrica_list, color=c, lw=1,
                    label=f"{n_leds} LEDs")
            ax.scatter(iterations[-1], metrica_list[-1], marker='x', s=100, 
                       linewidths=2, color=c, zorder=5)

    ax.legend(title="Cantidad de LEDs", bbox_to_anchor=(1.02,1), loc="upper left")
    plt.tight_layout()
    return fig, ax
   
leds_brazo = np.arange(2, 11)
leds_matriz = np.arange(3, 16)**2
colors_brazo = sns.color_palette("viridis", len(leds_brazo))
colors_matriz = sns.color_palette("viridis", len(leds_matriz))

x0 = 0
y0 = 0
    
#%% Cargo todas las imágenes    

# Cargo las imágenes originales
os.chdir(ROOT + input_filedir)
baboon_orig = Image.open('baboon.tif', 'r')
maps_orig = Image.open('Map_512.tiff', 'r')

# =============================================================================
# # Genero imágenes con ruido 
# baboon_rand = baboon_orig_array32 + np.random.rand(*baboon_orig_array32.shape)*255
# maps_rand = maps_orig_array32 + np.random.rand(*maps_orig_array32.shape)*2*np.pi
# =============================================================================

# Cargo las reconstrucciones con el matriz
# Primero cargo las que tienen a baboon en amplitud
output_filedir = os.path.join(ROOT, "brazo", "mag_Baboon")
mag_baboon_brazo_all_it = {}

for i in range(2, 11): # Armo contador para las configuraciones de LEDs
    for it in [11, 51, 101, 501, 1001, 5001, 10001]: # Armo contador para las iteraciones
        folder = os.path.join(output_filedir, f"{i}_LEDs", f"{it}_it", "green")
        
        # rompo la busqueda del LED en caso de que no haya reconstrucción
        if not os.path.isdir(folder): 
            break
        
        # Cargo las imágenes en amplitud y en fase
        for file in os.listdir(folder):
            if file.startswith("magnitud") and file.endswith(".npy"):
                mag_it = np.load(os.path.join(folder, file))
            if file.startswith("fase") and file.endswith(".npy"):
                phase_it = np.load(os.path.join(folder, file))
                
        # Guardo las imágenes
        mag_baboon_brazo_all_it[(i, it - 1)] = [mag_it, phase_it]
        
# Cargo las que tienen a maps en amplitud
output_filedir = os.path.join(ROOT, "brazo", "mag_Maps")
mag_maps_brazo_all_it = {}

for i in range(2, 11): # Armo contador para las configuraciones de LEDs
    for it in [11, 51, 101, 501, 1001, 5001, 10001]: # Armo contador para las iteraciones
        folder = os.path.join(output_filedir, f"{i}_LEDs", f"{it}_it", "green")
        
        # rompo la busqueda del LED en caso de que no haya reconstrucción
        if not os.path.isdir(folder): 
            break
        
        # Cargo las imágenes en amplitud y en fase
        for file in os.listdir(folder):
            if file.startswith("magnitud") and file.endswith(".npy"):
                mag_it = np.load(os.path.join(folder, file))
            if file.startswith("fase") and file.endswith(".npy"):
                phase_it = np.load(os.path.join(folder, file))
                
        # Guardo las imágenes
        mag_maps_brazo_all_it[(i, it - 1)] = [mag_it, phase_it]
        
# Cargo las reconstrucciones con la matriz
# Primero cargo las que tienen a baboon en amplitud
output_filedir = os.path.join(ROOT, "matriz", "mag_Baboon")
mag_baboon_matriz_all_it = {}

for i in range(3, 16): # Armo contador para las configuraciones de LEDs
    for it in [11, 51, 101, 501, 1001, 5001, 10001]: # Armo contador para las iteraciones
        folder = os.path.join(output_filedir, f"{i**2}_LEDs", f"{it}_it", "green")
        
        # rompo la busqueda del LED en caso de que no haya reconstrucción
        if not os.path.isdir(folder): 
            break
        
        # Cargo las imágenes en amplitud y en fase
        for file in os.listdir(folder):
            if file.startswith("magnitud") and file.endswith(".npy"):
                mag_it = np.load(os.path.join(folder, file))
            if file.startswith("fase") and file.endswith(".npy"):
                phase_it = np.load(os.path.join(folder, file))
                
        # Guardo las imágenes
        mag_baboon_matriz_all_it[(i**2, it - 1)] = [mag_it, phase_it]
        
# Cargo las que tienen a maps en amplitud
output_filedir = os.path.join(ROOT, "matriz", "mag_Maps")
mag_maps_matriz_all_it = {}

for i in range(3, 16): # Armo contador para las configuraciones de LEDs
    for it in [11, 51, 101, 501, 1001, 5001, 10001]: # Armo contador para las iteraciones
        folder = os.path.join(output_filedir, f"{i**2}_LEDs", f"{it}_it", "green")
        
        # rompo la busqueda del LED en caso de que no haya reconstrucción
        if not os.path.isdir(folder): 
            break
        
        # Cargo las imágenes en amplitud y en fase
        for file in os.listdir(folder):
            if file.startswith("magnitud") and file.endswith(".npy"):
                mag_it = np.load(os.path.join(folder, file))
            if file.startswith("fase") and file.endswith(".npy"):
                phase_it = np.load(os.path.join(folder, file))
                
        # Guardo las imágenes
        mag_maps_matriz_all_it[(i**2, it - 1)] = [mag_it, phase_it]
        
#%% Grafico de brazo con baboon en amplitudes

baboon_orig_array32 = np.array(baboon_orig, dtype=np.float32)
maps_orig_array32 = np.array(maps_orig, dtype=np.float32)
maps_orig_array32 = maps_orig_array32*2*np.pi/np.max(maps_orig_array32)-np.pi

PINCC_mag_baboon_brazo = selector(baboon_orig_array32, maps_orig_array32,
                                  mag_baboon_brazo_all_it, 'PINCC')
MSEref_mag_baboon_brazo = selector(baboon_orig_array32, maps_orig_array32,
                                  mag_baboon_brazo_all_it, 'MSEref', x0, y0)
RE_mag_baboon_brazo = selector(baboon_orig_array32, maps_orig_array32,
                                  mag_baboon_brazo_all_it, 'RE')
PearsonAmp_mag_baboon_brazo = selector(baboon_orig_array32, maps_orig_array32,
                                  mag_baboon_brazo_all_it, 'PearsonAmp')
PearsonPhase_mag_baboon_brazo = selector(baboon_orig_array32, maps_orig_array32,
                                  mag_baboon_brazo_all_it, 'PearsonPhase')

graficar_metrica(PINCC_mag_baboon_brazo, "PINCC", leds_brazo, colors_brazo)
graficar_metrica(MSEref_mag_baboon_brazo, "MSEref", leds_brazo, colors_brazo)
graficar_metrica(RE_mag_baboon_brazo, "RE", leds_brazo, colors_brazo)
graficar_metrica(PearsonAmp_mag_baboon_brazo, "Pearson amplitud", leds_brazo, colors_brazo)
graficar_metrica(PearsonPhase_mag_baboon_brazo, "Pearson fase", leds_brazo, colors_brazo)

#%% Grafico de matriz con baboon en amplitudes

baboon_orig_array32 = np.array(baboon_orig, dtype=np.float32)
maps_orig_array32 = np.array(maps_orig, dtype=np.float32)
maps_orig_array32 = maps_orig_array32*2*np.pi/np.max(maps_orig_array32)-np.pi

PINCC_mag_baboon_matriz = selector(baboon_orig_array32, maps_orig_array32,
                                  mag_baboon_matriz_all_it, 'PINCC')
MSEref_mag_baboon_matriz = selector(baboon_orig_array32, maps_orig_array32,
                                  mag_baboon_matriz_all_it, 'MSEref', x0, y0)
RE_mag_baboon_matriz = selector(baboon_orig_array32, maps_orig_array32,
                                  mag_baboon_matriz_all_it, 'RE')
PearsonAmp_mag_baboon_matriz = selector(baboon_orig_array32, maps_orig_array32,
                                  mag_baboon_matriz_all_it, 'PearsonAmp')
PearsonPhase_mag_baboon_matriz = selector(baboon_orig_array32, maps_orig_array32,
                                  mag_baboon_matriz_all_it, 'PearsonPhase')

graficar_metrica(PINCC_mag_baboon_matriz, "PINCC", leds_matriz, colors_matriz)
graficar_metrica(MSEref_mag_baboon_matriz, "MSEref", leds_matriz, colors_matriz)
graficar_metrica(RE_mag_baboon_matriz, "RE", leds_matriz, colors_matriz)
graficar_metrica(PearsonAmp_mag_baboon_matriz, "Pearson amplitud", leds_matriz, colors_matriz)
graficar_metrica(PearsonPhase_mag_baboon_matriz, "Pearson fase", leds_matriz, colors_matriz)

#%% Grafico de brazo con maps en amplitudes

baboon_orig_array32 = np.array(baboon_orig, dtype=np.float32)
maps_orig_array32 = np.array(maps_orig, dtype=np.float32)
baboon_orig_array32 = baboon_orig_array32*2*np.pi/np.max(baboon_orig_array32)-np.pi

PINCC_mag_maps_brazo = selector(maps_orig_array32, baboon_orig_array32,
                                  mag_maps_brazo_all_it, 'PINCC')
MSEref_mag_maps_brazo = selector(maps_orig_array32, baboon_orig_array32,
                                  mag_maps_brazo_all_it, 'MSEref', x0, y0)
RE_mag_maps_brazo = selector(maps_orig_array32, baboon_orig_array32,
                                  mag_maps_brazo_all_it, 'RE')
PearsonAmp_mag_maps_brazo = selector(maps_orig_array32, baboon_orig_array32,
                                  mag_maps_brazo_all_it, 'PearsonAmp')
PearsonPhase_mag_maps_brazo = selector(maps_orig_array32, baboon_orig_array32,
                                  mag_maps_brazo_all_it, 'PearsonPhase')

graficar_metrica(PINCC_mag_maps_brazo, "PINCC", leds_brazo, colors_brazo)
graficar_metrica(MSEref_mag_maps_brazo, "MSEref", leds_brazo, colors_brazo)
graficar_metrica(RE_mag_maps_brazo, "RE", leds_brazo, colors_brazo)
graficar_metrica(PearsonAmp_mag_maps_brazo, "Pearson amplitud", leds_brazo, colors_brazo)
graficar_metrica(PearsonPhase_mag_maps_brazo, "Pearson fase", leds_brazo, colors_brazo)

#%% Grafico de matriz con maps en amplitudes

baboon_orig_array32 = np.array(baboon_orig, dtype=np.float32)
maps_orig_array32 = np.array(maps_orig, dtype=np.float32)
baboon_orig_array32 = baboon_orig_array32*2*np.pi/np.max(baboon_orig_array32)-np.pi

PINCC_mag_maps_matriz = selector(maps_orig_array32, baboon_orig_array32,
                                  mag_maps_matriz_all_it, 'PINCC')
MSEref_mag_maps_matriz = selector(maps_orig_array32, baboon_orig_array32,
                                  mag_maps_matriz_all_it, 'MSEref', x0, y0)
RE_mag_maps_matriz = selector(maps_orig_array32, baboon_orig_array32,
                                  mag_maps_matriz_all_it, 'RE')
PearsonAmp_mag_maps_matriz = selector(maps_orig_array32, baboon_orig_array32,
                                  mag_maps_matriz_all_it, 'PearsonAmp')
PearsonPhase_mag_maps_matriz = selector(maps_orig_array32, baboon_orig_array32,
                                  mag_maps_matriz_all_it, 'PearsonPhase')

graficar_metrica(PINCC_mag_maps_matriz, "PINCC", leds_matriz, colors_matriz)
graficar_metrica(MSEref_mag_maps_matriz, "MSEref", leds_matriz, colors_matriz)
graficar_metrica(RE_mag_maps_matriz, "RE", leds_matriz, colors_matriz)
graficar_metrica(PearsonAmp_mag_maps_matriz, "Pearson amplitud", leds_matriz, colors_matriz)
graficar_metrica(PearsonPhase_mag_maps_matriz, "Pearson fase", leds_matriz, colors_matriz)
