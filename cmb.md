from astropy.io import fits
import numpy as np
import matplotlib.pyplot as plt

# Load Planck CMB power spectra FITS file
hdulist = fits.open('COM_PowerSpect_CMB_R2.02.fits')
# Use TT low-ℓ unbinned extension (ℓ = 2–29) and high‑ℓ unbinned (ℓ = 30–2508)
tt_low = hdulist['TTLOLUNB'].data
tt_high = hdulist['TTHILUNB'].data
ell = np.concatenate((tt_low['ELL'], tt_high['ELL']))
cl_tt = np.concatenate((tt_low['CL'], tt_high['CL']))
hdulist.close()

# Drift function similar to misalignment model
def angular_drift(l, pi_a=3.2):
    theta = 2 * pi_a / l
    phase = (np.cumsum(np.full(l, theta))) % (2 * np.pi)
    return abs(phase[-1])

delta = np.array([angular_drift(l) for l in ell])
primes = [l for l in ell if l >= 2 and all(l % d != 0 for d in range(2, int(l**0.5) + 1))]

# Plotting
plt.figure(figsize=(12, 6))
plt.subplot(2,1,1)
plt.plot(ell, cl_tt, label='Planck Cₗᵀᵀ')
plt.xlabel('ℓ')
plt.ylabel('Cₗᵀᵀ [$μK^2$]')
plt.title('Planck CMB TT Power Spectrum')
plt.grid(True)

plt.subplot(2,1,2)
plt.plot(ell, delta, label='Model Δ(ℓ): Angular Drift')
plt.scatter(primes, delta[[np.where(ell == l)[0][0] for l in primes]],
            color='red', s=20, label='Prime ℓ-values')
plt.xlabel('ℓ')
plt.ylabel('Model Drift Δ')
plt.title('Prime‑indexed Drift vs. Composite Spectrum')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()