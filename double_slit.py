#!/usr/bin/env python3
# double_slit_sim.py
# ---------------------------------------------
# Latest ARP‑aware double‑slit experiment model
# Revision: 2025‑05‑06
#
# This script uses a 1‑D Fresnel‑FFT propagator to
# reproduce the interference pattern produced by
# two slits and provides an optional Adaptive‑
# Resistance Principle (ARP) “live aperture” mode
# so you can watch the slits evolve conductance
# over time.
# ---------------------------------------------

import numpy as np
import matplotlib.pyplot as plt

# ------------------------ 1. Physical constants
λ  = 633e-9          # 633 nm (He‑Ne red) wavelength [m]
k  = 2 * np.pi / λ   # wave‑number

# ------------------------ 2. Geometry (feel free to tweak)
slit_width       = 50e-6    # single‑slit width  [m]
slit_separation  = 200e-6   # centre‑to‑centre    [m]
screen_distance  = 1.20     # mask ➜ screen      [m]

# ------------------------ 3. Numerical grid
N      = 4096        # points  (power‑of‑2 for FFT speed)
extent = 5e-3        # half‑width of computational window at mask [m]
x      = np.linspace(-extent/2, extent/2, N)
dx     = x[1] - x[0]

# ------------------------ 4. Make the aperture (two rectangular slits)
mask = np.zeros_like(x)
half_w = slit_width / 2
mask[np.abs(x -  slit_separation/2) < half_w] = 1.0
mask[np.abs(x + slit_separation/2) < half_w] = 1.0

# ------------------------ 5. OPTIONAL: ARP live‑aperture update
def arp_update(G, I_sample, α=0.01, μ=0.001):
    """One Euler step of Ġ = α|I| − μG."""
    return G + (α * np.abs(I_sample) - μ * G)

enable_arp   = False   # <- flip to True to watch the slits adapt
arp_steps    = 500
α, μ         = 0.01, 0.001          # ARP parameters (our gold standard ratio)

if enable_arp:
    G = mask.astype(float)          # interpret mask pixels as conductances
    for _ in range(arp_steps):
        # simple sample: illuminate with plane wave ⇒ I proportional to G
        G = arp_update(G, I_sample=G, α=α, μ=μ)
    mask = G / G.max()              # rescale 0‒1

# ------------------------ 6. Fresnel propagation via FFT
fx = np.fft.fftfreq(N, d=dx)                             # spatial frequencies
H  = np.exp(-1j * np.pi * λ * screen_distance * fx**2)   # transfer function

U0 = mask                    # incident field amplitude (plane wave ⇒ 1)
Uf = np.fft.ifft(np.fft.fft(U0) * H)      # propagated field at screen
I  = np.abs(Uf)**2
I /= I.max()                                  # normalise

# convert frequency axis to screen coordinate x′
x_screen = np.fft.fftshift(λ * screen_distance * fx)
I        = np.fft.fftshift(I)

# ------------------------ 7. Plot
plt.figure(figsize=(8, 4))
plt.plot(x_screen * 1e3, I)
plt.title("Double‑slit interference pattern (latest build)")
plt.xlabel("Screen coordinate  x  [mm]")
plt.ylabel("Normalised intensity")
plt.grid(True)
plt.tight_layout()
plt.show()
