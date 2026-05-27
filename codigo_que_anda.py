#%% Importo librerías y defino parámetros del micro

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.optimize import brentq
from scipy.signal import find_peaks

M = 1                                                               # Magnificación
NA = 0.10                                                          # Apertura numérica
p_s = 10**(-6)                                                      # Tamaño por pixel - en metros
lmbd = 600*(10**(-9))                                                 # Longitud de onda
sample_height = 10**(-3)                                            # Altura de la muestra
R = 8*10**(-2)                                                      # Radio del brazo - en metros
z = R

max_angle = (75.07)*np.pi/180                                              # Máximo ángulo que el brazo permite iluminar

'''
Necesito este ángulo para pasar de px a m con el fourier_pixel_factor
para calcularlo tengo que saber cómo son las posiciones de los LEDs 
pero este código lo armo para calcular esas posiciones
tengo un problema medio circular

Ahora tomo un valor < pi/2 para probar
más tarde cambiar esto por un valor coherente con los límites físicos del micro
'''

ratio_LR = NA / np.sin(max_angle)

NA_synth = 1 / np.sqrt(1+(1/np.tan(max_angle))**2)
n_HR = 512
ratio_LR_synt = NA / NA_synth
n_LR = n_HR * ratio_LR_synt
fourier_pixel_factor = M / (n_LR * p_s) # Este multiplicado a k_px da k

k = (2 * np.pi) / lmbd                                              # Magnitud de los k vect
matrix_center = (0,0,0)
pupil_k = 37 // 2                                # Tamaño de la pupila en px

n_LEDs = 10                                                          # Cantidad de LEDs en el brazo
rota_led_central = False                         
porcentaje_overlap = 30
overlap = porcentaje_overlap/100                                     

#%% Defino funciones

def intersection_area(d, R, r):
    """Return the area of intersection of two circles.

    The circles have radii R and r, and their centres are separated by d.
    """

    if d <= abs(R - r):
        # One circle is entirely enclosed in the other.
        return np.pi * min(R, r) ** 2
    if d >= r + R:
        # The circles don't overlap at all.
        return 0

    r2, R2, d2 = r**2, R**2, d**2
    alpha = np.arccos((d2 + r2 - R2) / (2 * d * r))
    beta = np.arccos((d2 + R2 - r2) / (2 * d * R))
    return (
        r2 * alpha
        + R2 * beta
        - 0.5 * (r2 * np.sin(2 * alpha) + R2 * np.sin(2 * beta))
    )

def find_d(A, R, r):
    """
    Find the distance between the centres of two circles giving overlap area A.
    """

    # A cannot be larger than the area of the smallest circle!
    if A > np.pi * min(r, R) ** 2:
        raise ValueError(
            "Intersection area can't be larger than the area"
            " of the smallest circle"
        )
    if A == 0:
        # If the circles don't overlap, place them next to each other
        return R + r

    if A < 0:
        raise ValueError("Negative intersection area")

    def f(d, A, R, r):
        return intersection_area(d, R, r) - A

    a, b = abs(R - r), R + r
    d = brentq(f, a, b, args=(A, R, r))
    return d

#%% Calculo y grafico la red de k-vectores en px

area_overlap = np.pi * (pupil_k**2) * overlap 
dist_k_sucesivos = find_d(area_overlap, pupil_k, pupil_k)
area_chequeo = intersection_area(dist_k_sucesivos, pupil_k, pupil_k)

if rota_led_central:
    kx_equi = np.arange(-pupil_k - (n_LEDs - 2) * dist_k_sucesivos, pupil_k + (n_LEDs - 2) * dist_k_sucesivos, dist_k_sucesivos)
    ky_equi = np.arange(-pupil_k - (n_LEDs - 2) * dist_k_sucesivos, pupil_k + (n_LEDs - 2) * dist_k_sucesivos, dist_k_sucesivos)
else:
    kx_equi = np.arange(-pupil_k - (n_LEDs - 1.5) * dist_k_sucesivos, pupil_k + (n_LEDs - 1.5) * dist_k_sucesivos, dist_k_sucesivos)
    ky_equi = np.arange(-pupil_k - (n_LEDs - 1.5) * dist_k_sucesivos, pupil_k + (n_LEDs - 1.5) * dist_k_sucesivos, dist_k_sucesivos)

kx_px, ky_px = np.meshgrid(kx_equi, ky_equi)
kx = kx_px * 2 * np.pi * fourier_pixel_factor
ky = ky_px * 2 * np.pi * fourier_pixel_factor

fig, ax = plt.subplots(1, 2, figsize=(12,6))
ax[0].plot(kx_px, ky_px, marker='o', color='k', linestyle='none')
ax[1].plot(kx, ky, marker='o', color='k', linestyle='none')
for i in range(len(kx_px)):
    for j in range(len(ky_px)):
        circle = patches.Circle((kx_px[i,j], ky_px[i,j]), pupil_k, color='b', alpha=0.3)
        ax[0].add_patch(circle)
ax[0].legend(title='pixels', loc=1)
ax[1].legend(title='espacio k', loc=1)
plt.show()

#%% Calculo las posciones de los LEDs y ploteo

kz = np.sqrt(k**2 - kx**2 - ky**2)

x_ideal = -(kx / k) * R
y_ideal = -(ky / k) * R
z_ideal = -(kz / k) * R

fig, ax = plt.subplots(figsize=(6,6))
ax.plot(x_ideal, y_ideal, marker='o', color='k', linestyle='none')
ax.set_xlabel('x [m]')
ax.set_ylabel('y [m]')
ax.grid()
plt.show()

#%% Calculo los valores que puedo reproducir con el esquema

dist_LEDs = 22 * 10**(-3)
min_theta = dist_LEDs / R
m = 1

paso_theta = (max_angle) / 11 #/ 15                                   # Distancia entre LEDs
paso_phi = np.pi/100                                                # Paso angular del motor
theta = []
phi = []

ang_phi = 0
ang_theta = 0

x_re = []
y_re = []
z_re = []

while ang_phi < 2 * np.pi:
    contador = []
    while ang_theta < max_angle:
        
        x = R * np.cos(ang_phi) * np.sin(ang_theta)
        y = R * np.sin(ang_phi) * np.sin(ang_theta)
        z = R * np.cos(ang_theta)
        
        x_re.append(x)
        y_re.append(y)
        z_re.append(z)
        theta.append(ang_theta)
        phi.append(ang_phi)
        ang_theta += paso_theta
        contador.append(1)
        
    ang_theta = 0
    ang_phi += paso_phi
    

x_re = np.array(x_re)
y_re = np.array(y_re)
z_re = np.array(z_re)
phi = np.array(phi)
theta = np.array(theta)

kx_re = -x_re * (k/R)
ky_re = -y_re * (k/R)
kz_re = -z_re * (k/R)

kx_re_px, ky_re_px = (kx_re / (2 * np.pi * fourier_pixel_factor), ky_re / (2 * np.pi *  fourier_pixel_factor))

fig, ax = plt.subplots(1,2, figsize=(12,6))
#ax[0].plot(x_ideal, y_ideal, marker='o', color='k', linestyle='none')
ax[0].plot(x_re, y_re, marker='o', color='b', label='reales', linestyle='none')
ax[0].set_xlabel('x [m]')
ax[0].set_ylabel('y [m]')
ax[0].grid()
ax[0].legend()

#ax[1].scatter(kx_px, ky_px, marker='o', color='b', alpha=0.3)
ax[1].plot(kx_re_px, ky_re_px, marker='o', color='k', linestyle='none')
for i in range(len(kx_re_px)):
    circle = patches.Circle((kx_re_px[i], ky_re_px[i]), pupil_k, color='g', alpha=0.05)
    ax[1].add_patch(circle)
    
#for i in range(len(kx_px)):
#    for j in range(len(kx_px[0])):
#        circle = patches.Circle((kx_px[i][j], ky_px[i][j]), pupil_k, color='b', alpha=0.05)
#        ax[1].add_patch(circle)
ax[1].grid()
plt.show()

#%% Proyecto los valores reales en los ideales

x_elegido = []
y_elegido = []

for j in range(len(x_ideal)):
    for l in range(len(x_ideal[0])):
        d = []
        for i in range(len(x_re)):
            d.append(np.sqrt((-x_ideal[j,l] + x_re[i])**2 + (-y_ideal[j,l] + y_re[i])**2))
    
        x_elegido.append(x_re[np.argmin(d)])
        y_elegido.append(y_re[np.argmin(d)])
    
fig, ax = plt.subplots(figsize=(6,6))
ax.plot(x_elegido, y_elegido, marker='o', color='k', label='elegidos', linestyle='none', zorder=3)
ax.plot(x_re, y_re, marker='o', color='r', label='reales', linestyle='none', alpha = 0.5, zorder=2)
ax.plot(x_ideal, y_ideal, marker='o', color='b', linestyle='none', alpha=0.5, zorder=2)

circle = patches.Circle((0, 0), NA, color='g', alpha=0.05, zorder=1)
#ax.add_patch(circle)

ax.set_xlabel('x [m]')
ax.set_ylabel('y [m]')
ax.grid()
ax.legend()
plt.show()

#%%

def intersection_circles_area(d, R):
    """Return the area of intersection of two circles of radii R and
    their centres are separated by d
    """
    
    R2, d2 = R**2, d**2
    alpha = np.arccos(d2 / (2 * d * R))
    return (
        2 * R2 * alpha
        - R2 * np.sin(2 * alpha)
    )

max_angle_theta, _ = find_peaks(theta)
kx_max_ang_px = kx_re_px[max_angle_theta]
ky_max_ang_px = ky_re_px[max_angle_theta]

ind_i = []
ind_j = []
phi_filt = []

i = 0
while i < len(max_angle_theta):
    kx_px_i = kx_max_ang_px[i]
    ky_px_i = ky_max_ang_px[i]
    
    porcentaje_overlap_i = 100
    j = i+1
    while porcentaje_overlap_i > 40:
        kx_px_j = kx_max_ang_px[j % len(ky_max_ang_px)]
        ky_px_j = ky_max_ang_px[j % len(ky_max_ang_px)]
        
        dist_ij = np.sqrt((kx_px_i - kx_px_j)**2 + (ky_px_i - ky_px_j)**2)
        area_overlap_ij = intersection_circles_area(dist_ij, pupil_k)
        porcentaje_overlap_i = (area_overlap_ij / (np.pi * pupil_k**2)) * 100
        j+=1
        
    ind_i.append(i)
    ind_j.append(j % len(kx_max_ang_px) - 1)
    phi_filt.append(phi[max_angle_theta[i]])
    i = j - 1

fig, ax = plt.subplots(1,2, figsize=(12,6))
#ax[0].plot(x_ideal, y_ideal, marker='o', color='k', linestyle='none')
ax[0].plot(x_re, y_re, marker='o', color='b', label='reales', linestyle='none')
ax[0].set_xlabel('x [m]')
ax[0].set_ylabel('y [m]')
ax[0].grid()
ax[0].legend()

#ax[1].scatter(kx_px, ky_px, marker='o', color='b', alpha=0.3)
ax[1].plot(kx_max_ang_px[ind_i], ky_max_ang_px[ind_i], marker='o', color='k', linestyle='none')
for i in ind_i:
    circle = patches.Circle((kx_max_ang_px[i], ky_max_ang_px[i]), pupil_k, color='g', alpha=0.05)
    ax[1].add_patch(circle)

ax[1].grid()
plt.show()

#%%

trigger = {}

for l in range(len(contador) - 1):
    ind_l = max_angle_theta - l
    phi_l = phi[ind_l]
    
    kx_filt_l = []
    ky_filt_l = []
    for t in range(len(phi_l)):
        if phi_l[t] in phi_filt:
            kx_filt_l.append(kx_re_px[ind_l][t])
            ky_filt_l.append(ky_re_px[ind_l][t])
        
    trigger_l = np.zeros(len(kx_filt_l))            
    i = 0
    while i < len(kx_filt_l):
        kx_px_i = kx_filt_l[i]
        ky_px_i = ky_filt_l[i]
        
        porcentaje_overlap_i = 100
        j = i+1

        while porcentaje_overlap_i > 40: 
            kx_px_j = kx_filt_l[j % len(kx_filt_l)]
            ky_px_j = ky_filt_l[j % len(ky_filt_l)]
            
            dist_ij = np.sqrt((kx_px_i - kx_px_j)**2 + (ky_px_i - ky_px_j)**2)
            area_overlap_ij = intersection_area(dist_ij, pupil_k, pupil_k)
            porcentaje_overlap_i = (area_overlap_ij / (np.pi * pupil_k**2)) * 100
            j+=1
            
        trigger_l[j % len(kx_filt_l) - 1] = 1
        i = j - 1   
    
    trigger[f'{theta[max_angle_theta - l][0]}'] = trigger_l

x_filt = []
y_filt = []

kx_filt_px = []
ky_filt_px = []

for key, value in trigger.items():
    theta_j = float(key)
    trig_i = value
    x_filt_j = - R * trig_i * np.cos(phi_filt) * np.sin(theta_j)
    y_filt_j = - R * trig_i * np.sin(phi_filt) * np.sin(theta_j)
    
    x_filt.append(x_filt_j)
    y_filt.append(y_filt_j)

    kx_filt_j = k * trig_i * np.cos(phi_filt) * np.sin(theta_j) / (2 * np.pi * fourier_pixel_factor)
    ky_filt_j = k * trig_i * np.sin(phi_filt) * np.sin(theta_j) / (2 * np.pi * fourier_pixel_factor)
    
    kx_filt_px.append(kx_filt_j)
    ky_filt_px.append(ky_filt_j)

kx_filt_px = np.concatenate(kx_filt_px)
ky_filt_px = np.concatenate(ky_filt_px)

mask_no_origen = ~((kx_filt_px == 0) & (ky_filt_px == 0))
kx_filt_px = kx_filt_px[mask_no_origen]
ky_filt_px = ky_filt_px[mask_no_origen]

kx_filt_px = np.append(kx_filt_px, 0)
ky_filt_px = np.append(ky_filt_px, 0)

fig, ax = plt.subplots(1,2,figsize=(12,6))
#ax[0].plot(x_ideal, y_ideal, marker='o', color='k', linestyle='none', alpha=0.3)
ax[0].plot(x_filt, y_filt, marker='o', color='b', linestyle='none')
ax[0].set_xlabel('x [m]')
ax[0].set_ylabel('y [m]')
ax[0].grid()

ax[1].plot(kx_filt_px, ky_filt_px, marker='o', color='k', linestyle='none')
for i in range(len(kx_filt_px)):
    circle = patches.Circle((kx_filt_px[i], ky_filt_px[i]), pupil_k, color='g', alpha=0.1)
    ax[1].add_patch(circle)
ax[1].grid()
plt.show()

#%%
'''
max_angle_theta, _ = find_peaks(theta)
kx_ang_px = []
ky_ang_px = []

for l in range(len(contador) - 1):
    kx_px_circulo_l = kx_re_px[max_angle_theta - l]
    ky_px_circulo_l = ky_re_px[max_angle_theta - l]
    
    ind_i = []
    ind_j = []
    
    i = 0
    while i < len(kx_px_circulo_l):
        kx_px_i = kx_px_circulo_l[i]
        ky_px_i = ky_px_circulo_l[i]
        
        porcentaje_overlap_i = 100
        j = i+1
        
        max_iterations = len(kx_px_circulo_l) 
        while porcentaje_overlap_i > 30:
            #if len(ind_i) >= 2 and ind_i[-1] < ind_i[len(ind_i) -2]:
             #   del ind_i[-1]
              #  break
            kx_px_j = kx_px_circulo_l[j % len(kx_px_circulo_l)]
            ky_px_j = ky_px_circulo_l[j % len(ky_px_circulo_l)]
            
            dist_ij = np.sqrt((kx_px_i - kx_px_j)**2 + (ky_px_i - ky_px_j)**2)
            area_overlap_ij = intersection_area(dist_ij, pupil_k, pupil_k)
            porcentaje_overlap_i = (area_overlap_ij / (np.pi * pupil_k**2)) * 100
            j+=1
            print(dist_ij)
                      
        ind_i.append(i)
        ind_j.append(j % len(kx_px_circulo_l) - 1)
        i = j % len(kx_px_circulo_l) - 1
        if ind_i[-1] < ind_i[len(ind_i) -2]:
            del ind_i[-1]
            break
        
        kx_ang_px.append(kx_px_circulo_l[i])
        ky_ang_px.append(ky_px_circulo_l[i])
    
kx_ang_px.append(0)
ky_ang_px.append(0)
    
fig, ax = plt.subplots(1,2, figsize=(12,6))
ax[0].plot(x_ideal, y_ideal, marker='o', color='k', linestyle='none')
ax[0].plot(x_re, y_re, marker='o', color='b', label='reales', linestyle='none')
ax[0].set_xlabel('x [m]')
ax[0].set_ylabel('y [m]')
ax[0].grid()
ax[0].legend()

#ax[1].scatter(kx_px, ky_px, marker='o', color='b', alpha=0.3)
ax[1].plot(kx_ang_px, ky_ang_px, marker='o', color='k', linestyle='none')
for i in range(len(kx_ang_px)):
    circle = patches.Circle((kx_ang_px[i], ky_ang_px[i]), pupil_k, color='g', alpha=0.1)
    ax[1].add_patch(circle)
ax[1].set_xlabel('kx')
ax[1].set_ylabel('ky')
ax[1].grid()
plt.show()

#%%

kx_ang = np.array(kx_ang_px) * fourier_pixel_factor
ky_ang = np.array(ky_ang_px) * fourier_pixel_factor

x_ang = - (R/k) * kx_ang
y_ang = - (R/k) * ky_ang

fig, ax = plt.subplots(1,2, figsize=(12,6))
#ax[0].plot(x_ideal, y_ideal, marker='o', color='k', linestyle='none', alpha=0.3)
ax[0].plot(x_ang, y_ang, marker='o', color='b', linestyle='none')
ax[0].set_xlabel('x [m]')
ax[0].set_ylabel('y [m]')
ax[0].grid()
ax[0].legend()

#ax[1].scatter(kx_px, ky_px, marker='o', color='b', alpha=0.3)
ax[1].plot(kx_ang_px, ky_ang_px, marker='o', color='k', linestyle='none')
for i in range(len(kx_ang_px)):
    circle = patches.Circle((kx_ang_px[i], ky_ang_px[i]), pupil_k, color='g', alpha=0.1)
    ax[1].add_patch(circle)
ax[1].set_xlabel('kx')
ax[1].set_ylabel('ky')
ax[1].grid()
plt.show()
'''