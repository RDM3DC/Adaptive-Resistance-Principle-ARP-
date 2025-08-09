
# ARP Experiments — Quickstart README

**Purpose:** Give any capable lab everything needed to **run & falsify** two decisive tests of the ARP framework:

1) **Hydrides (LaH10) ridge test** — map `Tc(P)` at 120–220 GPa and check predicted trends.  
2) **Bell‑chip geometry/bath test** — verify `α(L) ∝ e^{−L/ξ}/L` and a visibility drop `V(μ)` under controlled noise (non‑signaling).

---

## TL;DR
- Clone this repo, install Python deps, and use our CSV templates.  
- Run **one script** to produce overlays + falsifier plots from your data.  
- Pass/fail is **pre‑stated** below; no curve‑fitting gymnastics required.

---

## What you’ll need

### Software
- Python ≥ 3.10 with: `numpy`, `pandas`, `matplotlib`
- Our analysis script: [`arp_fit_overlay.py`](./arp_fit_overlay.py) (CSV‑in → PNG/JSON‑out)

Install deps:
```bash
pip install numpy pandas matplotlib
```

### Hardware (A) Hydrides (LaH10)
- Diamond anvil cell (DAC) capable of **120–220 GPa**
- 4‑probe electrical leads; optional magnetization/Meissner (SQUID/VSM in‑situ)
- Temp control around room‑T ±50 K
- (Optional) Phonon/DFT support to estimate `ω_log(P)`, `μ*(P)`, and coupling `g(P)`

### Hardware (B) Bell‑chip
- Entangled photon/electronic pair source with variable **separation L** (hundreds μm → cm)
- Controlled bath/noise injector to dial **μ** (thermal/phononic)
- Standard CHSH/visibility readout; **no signaling** channels

---

## Minimal model ingredients (for context)
- Range parameter: `ξ = sqrt(D/μ)`; overlap: `W(L,ξ) = exp(−L/ξ)/L`  
- Geometry factor: `α_geom ∝ μ · W(L,ξ)`  
- Polaritons/phonons: `Δ_eff = k · (g/ω)^2 · Q_fac · C^2` (effective, non‑signaling)  
- Critical temperature (Allen–Dynes):
```
Tc = (ω_log/1.2) * exp{ −1.04(1+λ_tot) / [λ_tot − μ*(1+0.62 λ_tot)] }
```
You do **not** need to implement this; our script handles it.

---

## Data you collect (CSV)

### Hydrides — experimental Tc(P)
`your_LaH10_TcP.csv`
```csv
Pressure_GPa,Tc_K
120,191
136,241
138,243
170,250
# add as many rows as you have
```

**Optional DFT curves** (if available): `your_LaH10_DFT.csv`
```csv
Pressure_GPa,g_eV,omega_log_K,mu_star
150,0.30,1230,0.10
170,0.28,1250,0.11
# g in eV, omega_log in Kelvin, mu_star dimensionless
```

### Bell‑chip — visibility vs μ and vs L
`bellchip_visibility_vs_mu.csv`
```csv
L_mm,mu_units,Visibility
10.0,0.00,0.92
10.0,0.05,0.81
10.0,0.10,0.70
```

`bellchip_visibility_vs_L.csv`
```csv
L_mm,Visibility
1.0,0.95
5.0,0.88
10.0,0.78
```

Templates (optional):  
- [`TEMPLATE_hydride_film_inputs.csv`](./TEMPLATE_hydride_film_inputs.csv)  
- [`TEMPLATE_squid_film_inputs.csv`](./TEMPLATE_squid_film_inputs.csv)

---

## Run the analysis (Hydrides)
Generate overlays + report from your `Tc(P)` (and optional DFT curves):
```bash
python arp_fit_overlay.py --mode hydride \
  --exp_csv your_LaH10_TcP.csv \
  --dft_csv your_LaH10_DFT.csv \
  --outdir fit_out_hydride
```
**Outputs:**
- `fit_out_hydride/hydride_fit_overlay.png` — experimental dome vs ARP baseline and ARP+Δ
- `fit_out_hydride/hydride_fit_report.json` — RMSE, best‐fit scale `s_lambda`, polariton factor `k_scale`
- (Use our extra tools to plot `g_required(P)` or `Δ_required(P)` for `Tc=300 K` if desired)

## Run the analysis (Cuprates)
```bash
python arp_fit_overlay.py --mode cuprate \
  --exp_csv your_YBCO_TcP.csv \
  --outdir fit_out_cuprate
```
**Outputs:** `cuprate_fit_overlay.png`, `cuprate_fit_report.json`

---

## What to look for (falsifiers)

### Hydrides (LaH10)
- **Ridge + derivative sign flip**: `dTc/dP ≈ +1 K/GPa` near ~150–170 GPa, then `≈ −0.4 K/GPa` > ~200 GPa.  
- **Feasibility**: A 300 K contour appears around 160–200 GPa only if `Δ_eff` (or `g/Q`) is large enough for your `ω_log` and `μ*`.  
**Fail** if no ridge/derivative trends beyond heating/defects or maps cannot be reconciled for any plausible {g, ω_log, μ*}.

### Bell‑chip
- **Distance law**: visibility families consistent with `α(L) ∝ e^{−L/ξ}/L`.  
- **Bath law**: `V(μ)` shows a characteristic knee/roll‑off as μ increases.  
- **Non‑signaling**: no information transfer; only correlations move.  
**Fail** if there’s no `L` law, no `V(μ)` drop, or any signaling.

---

## Safety notes
- **DAC @ 200+ GPa**: follow high‑pressure lab best practices (gaskets, shielding, ruby fluorescence calibration).  
- Electrical isolation for 4‑probe; watch Joule heating near Tc.  
- For Bell‑chips: observe standard laser/electronics safety; isolate auxiliary channels to preserve non‑signaling.

---

## Contact & license
- Questions / coordination: **RDM3DC** (DM on X)  
- License: **CC‑BY 4.0** — reuse with attribution

> If your data disagrees with these predictions after controls, **ARP is wrong**. If it matches, we’ve cleared a decisive hurdle — thank you for testing it.