# 🧠 ARP Simulation: Target Shape Stabilization in Fluid Dynamics

This simulation demonstrates the **Adaptive Resistance Principle (ARP)** applied to a 2D fluid field with an injected **target vortex shape**. The goal is to observe whether ARP can evolve a **conductance field \( G(x, y) \)** that learns to **preserve the structure** despite diffusion and turbulence.

---

## 🎯 Goal

Inject a circular vortex and let ARP:

- Adaptively adjust local resistance
- React to the swirling vorticity
- Try to preserve the target structure

---

## 🧪 ARP Dynamics

The conductance field evolves via:

\[
\frac{dG_{ij}}{dt} = \alpha \cdot |I_{ij}|^\gamma - \mu G_{ij}
\]

Where:
- \( G_{ij} \): Conductance (inverse of local resistance)
- \( I_{ij} \): Local vorticity magnitude
- \( \alpha \): Reinforcement rate
- \( \mu \): Decay rate
- \( \gamma \): Sensitivity to turbulence

---

## 🌀 Velocity and Vorticity Fields

- Initial velocity is seeded with a **circular swirl** (vortex).
- Vorticity is computed as the curl of the velocity field.

\[
\omega = \nabla \times \vec{v}
\]

The velocity field is diffused using ARP-modified resistance.

---

## 📊 Dual Visualization

The animation shows:
- 🔥 Left: Vorticity field (structure)
- 🌐 Right: Conductance field \( G(x, y) \)

---

## 🧠 Python Code

```python
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Grid and simulation parameters
nx, ny = 100, 100
dx, dy = 1.0, 1.0
dt = 0.01
viscosity = 0.1
alpha, mu, gamma = 0.05, 0.01, 1.5

# Initialize fields
vx = np.zeros((nx, ny))
vy = np.zeros((nx, ny))
G = np.ones((nx, ny))

# Inject a circular vortex (target shape)
cx, cy = nx // 2, ny // 2
radius = 15
Y, X = np.meshgrid(np.arange(nx), np.arange(ny), indexing='ij')
mask = (X - cx)**2 + (Y - cy)**2 <= radius**2
vx[mask] = -(Y[mask] - cy)
vy[mask] = (X[mask] - cx)

# Vorticity computation
def compute_vorticity(vx, vy, dx, dy):
    dvy_dx = (np.roll(vy, -1, axis=0) - np.roll(vy, 1, axis=0)) / (2 * dx)
    dvx_dy = (np.roll(vx, -1, axis=1) - np.roll(vx, 1, axis=1)) / (2 * dy)
    return dvy_dx - dvx_dy

# ARP update
def update_G(G, vorticity, alpha, mu, gamma):
    return G + dt * (alpha * np.abs(vorticity)**gamma - mu * G)

# Velocity diffusion using ARP
def diffuse_velocity(vx, vy, G, dx, dy, dt):
    G_inv = 1 / (G + 1e-5)
    laplace_vx = (np.roll(vx, -1, axis=0) + np.roll(vx, 1, axis=0) +
                  np.roll(vx, -1, axis=1) + np.roll(vx, 1, axis=1) - 4 * vx) / (dx * dy)
    laplace_vy = (np.roll(vy, -1, axis=0) + np.roll(vy, 1, axis=0) +
                  np.roll(vy, -1, axis=1) + np.roll(vy, 1, axis=1) - 4 * vy) / (dx * dy)
    vx += dt * viscosity * G_inv * laplace_vx
    vy += dt * viscosity * G_inv * laplace_vy
    return vx, vy

# Plot setup
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
vort_img = ax1.imshow(np.zeros((nx, ny)), cmap='inferno', vmin=-5, vmax=5)
g_img = ax2.imshow(np.ones((nx, ny)), cmap='viridis', vmin=0, vmax=2)
ax1.set_title("Vorticity (Target Shape)")
ax2.set_title("ARP Conductance Field G")

# Animation loop
def update(frame):
    global vx, vy, G
    vorticity = compute_vorticity(vx, vy, dx, dy)
    G = update_G(G, vorticity, alpha, mu, gamma)
    vx, vy = diffuse_velocity(vx, vy, G, dx, dy, dt)
    vort_img.set_data(vorticity)
    g_img.set_data(G)
    return [vort_img, g_img]

ani = animation.FuncAnimation(fig, update, frames=200, interval=30, blit=True)
plt.close()

# Save animation (optional)
ani.save("arp_target_shape_sim.mp4", fps=20, extra_args=['-vcodec', 'libx264'])