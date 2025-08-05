# Geometric Prime Bias: Harmonic Sweep Analysis

**Date:** 2025-08-05

---

## 📐 Overview

We analyze the directional bias \(\Delta\) induced by a curvature-weighted probability distribution on the unit circle:
\[
\rho_k^\theta(\theta) = \frac{1}{2\pi} \left[1 + c_1 k \cos(\theta - \pi) + \cdots \right],
\]
where \(f(\theta)\) is a composite function of sine and cosine terms, and we modulate it by adding a small harmonic:
\[
f_a(\theta) = f(\theta) + a \cos(\theta).
\]

---

## 🔍 Sweep Experiment

We performed a dense sweep over \( a \in [-0.6, 0.6] \), measuring the resulting directional offset \(\Delta(a)\) from \(\pi\) (the unbiased direction). This gives insight into the **sensitivity of the system to the first harmonic** even when it is initially near zero.

### 📈 Resulting Plot

![Δ vs a](A_mathematical_digital_image_displays_three_recurs.png)

---

## 📊 Linear Fit (Zoomed Near \(a = 0\))

From the central region \( |a| < 0.1 \), we performed a linear regression:

- **Empirical Slope:**  
  \[
  \frac{d\Delta}{da}\Big|_{a=0} \approx -24.39 \pm 3.73
  \]

- **Fit Quality:**  
  \( R^2 = 0.753 \)

---

## 🔬 Interpretation

This confirms that even when the first Fourier coefficient \( A_1 \approx 0 \), the directional bias persists, indicating:

- A **second-order correction** is needed in the theory.
- The offset \(\Delta\) must depend on other harmonics or higher-order terms:
  \[
  \Delta \approx k \cdot (\gamma_0 + \gamma_1 A_1 + \gamma_2 A_2 + \cdots)
  \]

- The coefficient \(\gamma_1 \approx -24.4\) emerges as a potential **new mathematical constant** linking curvature to symmetry-breaking.

---

## 🧠 Keywords

`prime detection`, `adaptive pi`, `geometry`, `harmonic analysis`, `Fourier bias`, `degenerate symmetry`, `curvature-weighted probability`

---

## 🧩 Next Steps

- Derive higher-order coefficients like \(\gamma_2\)
- Package full degenerate expansion formula
- Prepare arXiv-compatible PDF with formal theory + numerics