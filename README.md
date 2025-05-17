# Adaptive Resistance Principle (ARP)

This repository contains experiments, code, and notes exploring the **Adaptive Resistance Principle**. ARP describes networks of resistive elements that update their conductance in response to electrical stimuli, inspired by electrorheological fluids and self‑organising systems found in nature.

## Repository overview

The project includes a variety of Python scripts and markdown documents:

- **double_slit.py** – Simulate a double‑slit experiment with an optional ARP "live aperture" mode.
- **mckenna-law-simulation.py** – Demonstrates conductance evolution according to a simple ARP update rule.
- **tsp*.py** – Prototype solvers that apply ARP ideas to travelling‑salesperson problems.
- Various `.md` files with derivations, conceptual sketches, and notes about potential applications.

Most scripts depend on `numpy` and `matplotlib`. Run them with a standard Python 3 installation. For example:

```bash
python3 double_slit.py
```

## Mathematical background

ARP dynamics can be summarized by a few core relations. Conductance $G_{ij}(t)$ between nodes $i$ and $j$ evolves as

$$\frac{dG_{ij}}{dt} = \alpha |I_{ij}| - \mu G_{ij},$$

where $I_{ij}$ is the link current, $\alpha$ the reinforcement rate, and $\mu$ the decay rate. The corresponding discrete update used in the code is

$$G_{ij}^{(n+1)} = G_{ij}^{(n)} + \Delta t\,[\alpha |I_{ij}^{(n)}| - \mu G_{ij}^{(n)}].$$

At equilibrium, the currents satisfy

$$|I_{ij}| = \frac{\mu}{\alpha} G_{ij}.$$

Combining adaptive elements yields a time–dependent impedance

$$Z(t) = \frac{1}{G(t)} + j\omega L(t) - \frac{j}{\omega C(t)},$$

leading to the reflection coefficient

$$\Gamma(\omega) = \frac{Z(t,\omega) - Z_0}{Z(t,\omega) + Z_0}.$$

The instantaneous power dissipated by a branch is

$$P(t) = I^2 R(t) = \frac{I^2}{G(t)}.$$

To measure the overall network's responsiveness we define the temporal adaptation index

$$\text{TAI}(t) = \frac{1}{N} \sum_{i,j} \left| \frac{dG_{ij}}{dt} \right|.$$ 

These equations underpin the simulations found in this repository, including experiments on quantum interference and adaptive optimization.

## License

This project is licensed under the terms of the MIT License. See [LICENSE](LICENSE) for details.

