import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# ----------
# PARAMETERS
# ----------
nx, ny = 200, 100        # Simulation grid size
dx = 1.0                 # Spatial step (for toy model)
dt = 0.2                 # Time step
timesteps = 400          # Number of animation frames

c_wave = 2.0             # "Wave speed" factor
damping = 0.0            # Light damping of the wave

alpha = 0.01             # ARP reinforcement rate
lambda_opt = 1.9184      # "Magic" ratio alpha/mu
mu = alpha / lambda_opt  # ARP decay rate
adapt_strength = 0.5     # How strongly barrier adaptivity influences wave

attenuation_factor = 0.001  # How strongly the barrier attenuates the wave

# ----------
# ARRAYS
# ----------
psi = np.zeros((ny, nx))       # Wave field
psi_prev = np.zeros_like(psi)  # For storing wave field at t-1
Gamma = np.zeros_like(psi)     # "Conductance" or adaptive barrier strength

# Laplacian helper (toy model)
def laplacian(field):
    f_up = np.roll(field, 1, axis=0)
    f_down = np.roll(field, -1, axis=0)
    f_left = np.roll(field, 1, axis=1)
    f_right = np.roll(field, -1, axis=1)
    return f_up + f_down + f_left + f_right - 4.0 * field

# ----------
# INITIALIZATION OF THE WAVE
# ----------
# Inject a wave near the left edge
x_init = 2
for y0 in range(ny):
    psi[y0, x_init] = 2.0 * np.exp(-((y0 - ny//2) ** 2) / 40.0)

# Force the left boundary to 0.0 (rough "absorbing" boundary)
psi[:, 0] = 0.0
psi_prev[:, 0] = 0.0

# Copy current psi into psi_prev
psi_prev[:] = psi

# ----------
# SET UP THE BARRIER WITH TWO SLITS
# ----------
barrier_x = nx // 2      # Barrier column in the middle
barrier_thickness = 3    # How thick the barrier is (x-direction)
slit_gap = 10            # Vertical gap for each slit
slit_center = ny // 2
slit_offset = 15

# barrier = 1 => blocked region, barrier = 0 => open
barrier = np.ones((ny, nx), dtype=float)

# Carve out two slits in the barrier columns
barrier[
    slit_center - slit_offset : slit_center - slit_offset + slit_gap,
    barrier_x : barrier_x + barrier_thickness
] = 0

barrier[
    slit_center + slit_offset - slit_gap : slit_center + slit_offset,
    barrier_x : barrier_x + barrier_thickness
] = 0

# ----------
# ANIMATION SETUP
# ----------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
im1 = ax1.imshow(psi, vmin=-0.3, vmax=0.3, cmap='RdBu', origin='lower', animated=True)
im2 = ax2.imshow(Gamma, vmin=0, vmax=0.05, cmap='inferno', origin='lower', animated=True)

ax1.set_title("Wave Field ψ (Frame 0)")
ax2.set_title("Adaptive Barrier Γ (Frame 0)")
plt.tight_layout()

# ----------
# UPDATE FUNCTION
# ----------
def update(frame):
    global psi, psi_prev, Gamma

    # 1) Wave Equation Update
    lap_psi = laplacian(psi)
    psi_next = (
        2.0 * psi
        - psi_prev
        + (c_wave ** 2) * lap_psi * (dt ** 2) / (dx ** 2)
        - damping * psi
    )

    # 2) Barrier Attenuation:
    #    wave_penalty is 1 + (adapt_strength * Gamma) where barrier=1,
    #    0 where barrier=0 (slits).
    wave_penalty = barrier * (1.0 + adapt_strength * Gamma)
    psi_next *= np.exp(-attenuation_factor * wave_penalty)

    # 3) ARP-like Update for Gamma:
    #    Compute gradient magnitude of psi to drive reinforcement
    dy_psi = np.roll(psi, -1, axis=0) - np.roll(psi, 1, axis=0)
    dx_psi = np.roll(psi, -1, axis=1) - np.roll(psi, 1, axis=1)
    grad_mag = 0.5 * np.sqrt(dx_psi**2 + dy_psi**2)

    # Where barrier=1 => adapt, barrier=0 => no adaptation
    dGamma_dt = alpha * grad_mag * barrier - mu * Gamma
    Gamma += dGamma_dt * dt

    # 4) Shift Time Steps
    psi_prev, psi = psi, psi_next

    # 5) Update Plots
    im1.set_data(psi)
    im2.set_data(Gamma)

    # Update titles with frame count
    ax1.set_title(f"Wave Field ψ (Frame {frame})")
    ax2.set_title(f"Adaptive Barrier Γ (Frame {frame})")

    return [im1, im2]

# ----------
# RUN THE ANIMATION
# ----------
ani = animation.FuncAnimation(
    fig, update, frames=timesteps, interval=30, blit=True
)
plt.show()
