import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import cumulative_trapezoid

# Parameters
alpha = 0.019184  # Tuned for equilibrium G_eq ≈ 1.9184 when I is constant
mu = 0.01
dt = 0.1
T = 1000
t = np.linspace(0, T * dt, T + 1)

# Complex input current I(t): multi-harmonic + spike + noise
I_t = (
    np.abs(np.sin(t)) +                # Base oscillation
    0.3 * np.abs(np.sin(5 * t)) +      # Higher-frequency harmonic
    0.1 * np.random.randn(len(t)) +    # Noise
    np.exp(-((t - 50)**2) / 2)         # Gaussian pulse centered at t = 50
)
I_t = np.clip(I_t, 0, None)  # Ensure I(t) ≥ 0

# Compute the exact solution G(t)
exp_mu_t = np.exp(mu * t)
integrand = exp_mu_t * I_t
integral = cumulative_trapezoid(integrand, t, initial=0)
G_t = alpha * np.exp(-mu * t) * integral

# Compute windowed moving average of G(t)
window = 50
G_mean = np.convolve(G_t, np.ones(window)/window, mode='same')

# Plot results
plt.figure(figsize=(12, 6))
plt.plot(t, G_t, label="Exact $G(t)$", lw=2)
plt.plot(t, G_mean, '--', label="Windowed Mean $G_{mean}(t)$", lw=2)
plt.xlabel("Time")
plt.ylabel("Conductance $G(t)$")
plt.title("Generation-Changing ARP Simulation with Complex $I(t)$")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()