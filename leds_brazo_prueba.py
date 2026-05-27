import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

M = 1                                                               # Magnificación
NA = 0.07                                                           # Apertura numérica
p_s = 10**(-6)                                                      # Tamaño por pixel - en metros
n_LEDs = 10
R = 0.15
lmbd = 600*10**(-9)                                                 # Longitud de onda
sample_height = 10**(-3)                                            # Altura de la muestra
paso_theta = np.pi / (2*7)                                          # Distancia entre LEDs
paso_phi = np.pi/3                                                 # Paso angular del motor

max_angle = 4*np.pi/10                                             # Máximo ángulo que el brazo permite iluminar
ratio_LR = NA / np.sin(max_angle)

NA_synth = 1 / np.sqrt(1+(1/np.tan(max_angle))**2)
n_HR = 512
ratio_LR_synt = NA / NA_synth
n_LR = n_HR * ratio_LR_synt
fourier_pixel_factor = M / (n_LR * p_s)                             # Este multiplicado a k_px da k

k = (2 * np.pi) / lmbd                                              # Magnitud de los k vect
matrix_center = (0,0,0)
pupil_k = (NA * p_s * n_LR) / (lmbd)                                # Tamaño de la pupila en px

n_LEDs = int(max_angle/paso_theta)                                  # Cantidad de LEDs en el brazo
rota_led_central = False                         
porcentaje_overlap = 10
overlap = porcentaje_overlap/100                                     

#%%

pos_leds = {}

ang_phi = 0
ang_theta = 0

while ang_phi < 2 * np.pi:
    while ang_theta < max_angle:
        
        x = R * np.cos(ang_phi) * np.sin(ang_theta)
        y = R * np.sin(ang_phi) * np.sin(ang_theta)
        z = R * np.cos(ang_theta)
        
        pos_leds[(ang_theta, ang_phi)] = (x,y,z)
        ang_theta += paso_theta
        
    ang_theta = 0
    ang_phi += paso_phi
 
x_pos, y_pos, z_pos = zip(*pos_leds.values())

fig, ax = plt.subplots(1, 2, figsize=(12,6))
ax[0].scatter(x_pos ,y_pos , label='plano xy', color='k')
ax[1].scatter(x_pos ,z_pos , label='plano xz', color='k')
for a in ax:
    a.legend()
    a.grid()
plt.tight_layout()
plt.show()

#%%

x_pos = np.array(x_pos)
y_pos = np.array(y_pos)
z_pos = np.array(z_pos)

kx = k * (x_pos / R)
ky = k * (y_pos / R)
kz = k * (z_pos / R)

kx_px = kx / fourier_pixel_factor
ky_px = ky / fourier_pixel_factor

fig, ax = plt.subplots(1, 2, figsize=(12,6))
ax[0].plot(kx, ky, marker='o', color='k', linestyle='none')
ax[1].plot(kx_px, ky_px, marker='o', color='k', linestyle='none')
for i in range(len(kx_px)):
    circle = patches.Circle((kx[i], ky[i]), k, color='r', alpha=0.1)
    ax[0].add_patch(circle)
    circle = patches.Circle((kx_px[i], ky_px[i]), pupil_k, color='r', alpha=0.1)
    ax[1].add_patch(circle)
ax[0].legend(title='espacio k', loc=1)
ax[1].legend(title='pixels', loc=1)
plt.show()

#%%

fig, ax = plt.subplots(figsize=(6,6))
circle = patches.Circle((0, 0), k, color='r', alpha=0.1)
ax.add_patch(circle)
ax.set_xlim(-k,k)
ax.set_ylim(-k,k)