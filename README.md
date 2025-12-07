# Adaptive Resistance Principle (ARP)

[![Sponsor RDM3DC](https://img.shields.io/badge/Sponsor-RDM3DC-ff69b4?logo=github-sponsors)](https://github.com/sponsors/RDM3DC)

This repository contains experiments, code, and notes exploring the **Adaptive Resistance Principle**—a family of adaptive-conductance laws inspired by electrorheological fluids, biological transients, and geometry-aware transport systems.

ARP is expressed here in **two complementary modes**:

* **ARP-I (Intensity-Driven, classical)**  
  $\dot G = \alpha |I| - \mu G$

* **ARP-Φ (Flux-Driven, 2025 extension)**  
  $\dot G = \alpha |\dot{\Phi}| - \mu G$

Both describe how conductances, geometric weights, or interaction strengths adapt in response to a driving signal. ARP-Φ generalizes ARP-I by replacing instantaneous intensity with the *rate of change* of a field variable, capturing sensitivity to geometry and curvature.

**Project website:** [https://rdm3dc.github.io/ARP-RDM3DC/](https://rdm3dc.github.io/ARP-RDM3DC/)  
**X/Twitter:** [https://x.com/RDM3DC](https://x.com/RDM3DC)

---

# ⭐ Novelty & Scientific Positioning

The core adaptive law explored in this repository—whether intensity-driven (ARP-I) or flux-driven (ARP-Φ)—is related to established work in adaptive flow networks, Physarum-type conductance updates, electrorheological fluids, and adaptive impedance control.

This repository does **not** claim exclusive discovery of the differential equation form itself.

Instead, the novel contributions are:

### **1. A unified, generalized software + hardware platform**

for experimenting with adaptive-conductance laws across **circuits**, **geometry**, **quantum control**, and **analog computing**.

### **2. New invariants, constants, and scaling relations**

such as the **G*** fixed point (≈1.9184), cross-domain **1/√N** cancellation laws, and stability mappings linking discrete networks to field-theoretic geometry.

### **3. New applications and cross-domain bridges**

including:

* ML optimization (RealignR)
* analog/ER-fluid TSP solvers
* adaptive curvature networks (πₐ geometry)
* classical–quantum hybrids (AIN + Grover gain control)
* emergent geometry simulations

Users are encouraged to cite both foundations in the literature and the extensions introduced in this repo.

---

# Repository Overview

This project includes a variety of Python scripts and research notes:

* **double_slit.py** – Double-slit simulation with optional ARP “live aperture.”
* **dynamic-resistance-simulation.py** – Demonstrates conductance evolution under ARP-I or ARP-Φ.
* **tsp*.py** – TSP solvers exploring ARP dynamics in path reinforcement.
* Multiple `.md` files with derivations, sketches, and conceptual extensions.

Most scripts depend on `numpy` and `matplotlib`.

Standalone reference: **[ARP_reference.md](ARP_reference.md)**

---

# 🔧 ARP Modes: ARP-I and ARP-Φ

ARP is presented in two parallel forms. Both share the same stability structure but respond to different physical cues.

---

# **ARP-I (Intensity-Driven)**

### *Classical adaptive conductance law*

\[
\dot G(t) = \alpha\,|I(t)| - \mu\,G(t)
\]

* Used for circuits, TSP, ER-fluid analog computing
* Responds to “how much signal is flowing”
* Memory increases with sustained current
* Conductance decays exponentially without stimulus

This is the formulation historically used throughout the repository.

---

# **ARP-Φ (Flux-Driven, 2025 Extension)**

### *Geometry-sensitive, derivative-based adaptation*

\[
\dot G(t) = \alpha\,\big|\dot\Phi(t)\big| - \mu\,G(t)
\]

* Used for adaptive geometry (πₐ), AQG+M, and field simulations
* Responds to *change*, not magnitude
* Curvature/gradient changes increase conductance
* Static regions decay (straight lines collapse, curves stabilize)

This generalizes ARP into geometric, field-based, and spacetime-like systems.

---

# 📌 Shared Properties of ARP-I and ARP-Φ

Both modes have identical mathematical structure. Let $u(t) = |I(t)|$ or $u(t) = |	ext{\dot\Phi(t)}|$.

Then in general:

\[
\dot G = \alpha\,u(t) - \mu\,G
\]

---

## **Closed-form solution**

\[
G(t) = e^{-\mu t}\!\left[G(0) + \alpha\!\int_0^t e^{\mu s}\,u(s)\,ds\right]
\]

A simple exponentially weighted causal filter with time-constant $1/\mu$.

---

## **Constant stimulus**

If $u(t)=u_0$:

\[
G(t) = G_\infty + \big(G(0)-G_\infty\big)e^{-\mu t},
\qquad
G_\infty = \frac{\alpha u_0}{\mu}
\]

---

## **Discrete-time form**

\[
G_{k+1} = (1-\mu\Delta t)G_k + \alpha\Delta t\,u_k
\]

Stable for $0 < \mu\Delta t < 2$.

---

## **Positivity & bounds**

If $u(t)\le u_{\max}$:

\[
0 \le G(t) \le \frac{\alpha u_{\max}}{\mu}
\]

---

## **Global exponential stability**

Let $e(t)=G(t)-G_\infty$:

\[
\dot e = -\mu e
\quad\Rightarrow\quad
 e(t)=e(0)e^{-\mu t}
\]

---

# 🌀 Multi-Edge / Network Form

For edges $(i,j)$:

\[
\dot G_{ij} = \alpha\,u_{ij} - \mu\,G_{ij}
\]

with $u_{ij} = |I_{ij}|$ (ARP-I) or $u_{ij}=|\dot\Phi_{ij}|$ (ARP-Φ).

---

# 🔬 2025 Highlights: Fixed Points, Scaling Laws, Geometry

These results emerged from experiments in this repo and the companion **graviton-PIₐ** repo.

### **1. Universal ARP Fixed Point (G*)**

In ARP-controlled Grover search:

\[
\hat G^* \approx 1.9184
\]

after factoring $1/\sqrt{N}$ geometry. This constant stabilizes quantum gain against decoherence.

---

### **2. 1/√N Scaling + N-Independent Noise Budget**

With $\gamma_G,\mu_G\propto 1/\sqrt{N}$:

\[
G_{\text{angle}}^{\text{steady}} \propto \frac{1}{\sqrt{N}}
\]

Combined with Grover’s $K(N)\propto\sqrt N$, the cancelable noise term becomes **O(1)**.

---

### **3. LDR (Law of Dynamic Resistance) in Field Theory**

In AQG+M simulations:

\[
\dot G_{\rm eff}
\approx \gamma_{\rm eff} P_{\rm lump}
- \mu_{\rm eff}G_{\rm eff}
\]

leading to universal geometry/matter ratios (e.g., $\tilde G/\tilde P\approx 1.55$), linking discrete ARP networks to adaptive curvature.

---

# 🧠 Interactive GPT Guides

These links open custom GPT assistants for deeper exploration (requires an OpenAI account):

* **Adaptive Resistance Guide**
* **Adaptive Pi Geometry**
* **Curve Memory Assistant**
* **RealignR Optimizer**
* **Geometric Neural Computation**
* **Curve Alphabet Assistant**

(Links preserved from previous README.)

---

# 🔗 Quantum Extensions (graviton-PIₐ)

See companion repo:

**[https://github.com/RDM3DC/graviton-PI_a](https://github.com/RDM3DC/graviton-PI_a)**

for:

* ARP-controlled Grover experiments
* Adaptive Impedance Network (AIN)
* quantum-classical stabilization
* emergent geometry mapping

---

# License

MIT License — see [LICENSE](LICENSE)

---

# Support

[https://cash.app/$rdm3d](https://cash.app/$rdm3d)