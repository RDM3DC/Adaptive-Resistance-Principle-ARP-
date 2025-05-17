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

## License

This project is licensed under the terms of the MIT License. See [LICENSE](LICENSE) for details.
