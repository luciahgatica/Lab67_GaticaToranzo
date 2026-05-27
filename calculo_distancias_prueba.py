import numpy as np
import matplotlib.pyplot as plt

# -------------------------------
# Grilla
# -------------------------------
xx = np.arange(-5, 6)   # valores de x
yy = np.zeros(len(xx))   # valores de y
zz = 0                     # altura fija

X, Y = np.meshgrid(xx, yy)
pos_LEDs_grilla = np.vstack([X.ravel(), Y.ravel(), np.full(X.size, zz)]).T

# -------------------------------
# Muestra y esfera
# -------------------------------
pos_muestra = np.array([0,0,3], dtype=float)
radio_esfera = np.abs(pos_muestra[-1] - zz)  

pos_LEDs_esfera = []
for pos_led in pos_LEDs_grilla:
    d = pos_led - pos_muestra  
    norm_d = np.linalg.norm(d)
    if norm_d == 0:
        continue  
    t = radio_esfera / norm_d  
    interseccion = pos_muestra + t * d
    pos_LEDs_esfera.append(interseccion)
pos_LEDs_esfera = np.array(pos_LEDs_esfera)

# -------------------------------
# Gráfico 2D (X vs Z)
# -------------------------------
fig, ax = plt.subplots(figsize=(8,6))

# Dibujar esfera en 2D como círculo (XZ)
theta = np.linspace(0, 2*np.pi, 200)
ax.plot(radio_esfera*np.cos(theta), radio_esfera*np.sin(theta) + pos_muestra[-1], 'c--', alpha=0.5, label="Esfera (proyección XZ)")

# LEDs de la grilla (solo X y Z)
ax.scatter(pos_LEDs_grilla[:,0], pos_LEDs_grilla[:,2], c='blue', label='LEDs grilla')

# Intersecciones en la esfera (solo X y Z)
ax.scatter(pos_LEDs_esfera[:,0], pos_LEDs_esfera[:,2], c='green', label='LEDs esfera')

# Muestra
ax.scatter(pos_muestra[0], pos_muestra[2], c='red', s=100, label='Muestra')

# Líneas entre grilla y esfera (XZ)
for led, inter in zip(pos_LEDs_grilla, pos_LEDs_esfera):
    ax.plot([pos_muestra[0], led[0]], [pos_muestra[2], led[2]], 'b-', alpha=0.3)  # rayo a la grilla
    ax.plot([pos_muestra[0], inter[0]], [pos_muestra[2], inter[2]], 'g-', alpha=0.7)  # rayo a la esfera

ax.legend()
ax.set_xlabel('X')
ax.set_ylabel('Z')
ax.set_title("Proyección 2D (X vs Z) de LEDs y esfera")
ax.set_aspect('equal', adjustable='box')
plt.show()
