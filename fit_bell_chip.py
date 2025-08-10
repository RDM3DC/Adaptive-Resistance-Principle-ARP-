#!/usr/bin/env python3
import argparse, os, json, csv, numpy as np, matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Optional, Callable

@dataclass
class Params:
    Delta: float; Omega: float; alpha: float; mu: float; lam: float
    Gamma2: float=0.0; eta: float=0.0

def deriv(state, t, p, Omega_of_t=None):
    x,y,z,gx,gy = state
    Omega = p.Omega if Omega_of_t is None else Omega_of_t(t)
    Gamma2_eff = p.Gamma2 + p.eta*(gy**2)
    dx = -p.Delta*y - 2*p.lam*gy*z - Gamma2_eff*x
    dy =  p.Delta*x - Omega*z + 2*p.lam*gx*z - Gamma2_eff*y
    dz =  Omega*y + 2*p.lam*(gy*x - gx*y)
    dgx = 0.5*p.alpha*x - p.mu*gx
    dgy = 0.5*p.alpha*y - p.mu*gy
    return np.array([dx,dy,dz,dgx,dgy], float)

def rk4_step(f, y, t, dt, *args, **kwargs):
    k1 = f(y, t, *args, **kwargs)
    k2 = f(y + 0.5*dt*k1, t + 0.5*dt, *args, **kwargs)
    k3 = f(y + 0.5*dt*k2, t + 0.5*dt, *args, **kwargs)
    k4 = f(y + dt*k3, t + dt, *args, **kwargs)
    return y + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)

def integrate(f, y0, t0, t1, dt, *args, **kwargs):
    n = int((t1 - t0)/dt)
    y = np.array(y0, float); t=t0
    for _ in range(n):
        y = rk4_step(f, y, t, dt, *args, **kwargs)
        t += dt
    return y

def settle_steady(p, s0, T=6.0, dt=0.004):
    return integrate(deriv, s0, 0.0, T, dt, p)

def read_csv_columns(path):
    cols = {}
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for k,v in row.items():
                cols.setdefault(k.strip(), []).append(float(v))
    return {k: np.array(v, float) for k,v in cols.items()}

def simulate_p1_curves(deltas_data, Lambda, alpha, mu, Omega, scale, offset):
    lam = Lambda * mu / alpha
    deltas_sim = deltas_data*scale + offset
    s = np.array([0,0,1,0,0], float)
    z_up = []
    for D in deltas_sim:
        p = Params(Delta=float(D), Omega=Omega, alpha=alpha, mu=mu, lam=lam)
        s = settle_steady(p, s)
        z_up.append(s[2])
    z_dn = []
    for D in deltas_sim[::-1]:
        p = Params(Delta=float(D), Omega=Omega, alpha=alpha, mu=mu, lam=lam)
        s = settle_steady(p, s)
        z_dn.append(s[2])
    z_dn = np.array(z_dn[::-1])
    return np.array(z_up), z_dn

def fit_p1(deltas, z_up, z_dn, alpha=0.6, mu=0.2, Omega=1.0, samples=40, seed=0):
    rng = np.random.default_rng(seed)
    best = None
    for _ in range(samples):
        Lambda = rng.uniform(0.0, 3.0)
        scale  = rng.uniform(0.5, 2.0)
        offset = rng.uniform(-2.0, 2.0)
        zu, zd = simulate_p1_curves(deltas, Lambda, alpha, mu, Omega, scale, offset)
        mse = np.mean((zu - z_up)**2) + np.mean((zd - z_dn)**2)
        if (best is None) or (mse < best[0]):
            best = (mse, Lambda, scale, offset, zu, zd)
    mse, Lambda_b, scale_b, offset_b, zu_b, zd_b = best
    return dict(Lambda=float(Lambda_b), scale=float(scale_b), offset=float(offset_b), mse=float(mse))

def fit_p2(csv_path, alpha=0.6, mu=0.2):
    cols = read_csv_columns(csv_path)
    if "y2" in cols: x = cols["y2"]
    elif "y" in cols: x = cols["y"]**2
    elif "A" in cols: x = cols["A"]**2
    else: raise ValueError("P2 CSV must have 'y2' or 'y' or 'A'.")
    if "T2_inv" in cols: y = cols["T2_inv"]
    elif "T2" in cols: y = 1.0/cols["T2"]
    else: raise ValueError("P2 CSV must have 'T2' or 'T2_inv'.")
    A = np.vstack([np.ones_like(x), x]).T
    b, m = np.linalg.lstsq(A, y, rcond=None)[0]
    eta_eff = m / ((alpha/(2*mu))**2)
    return dict(Gamma2=float(b), eta=float(eta_eff), slope=float(m), intercept=float(b))

def fit_p3(noarp_csv, arp_csv, alpha=0.6, mu=0.2, A_drive=0.6, omega=1.0):
    colsN = read_csv_columns(noarp_csv); colsA = read_csv_columns(arp_csv)
    D = colsN["Delta"]; Rno = colsN["R"]; Dar, Rar = colsA["Delta"], colsA["R"]
    Rar_interp = np.interp(D, Dar, Rar)
    data_diff = Rar_interp - Rno
    lam = 1.0 * mu / alpha  # template with Lambda=1
    dt=0.002; Ttot=40.0; Tskip=16.0
    def Omega_of_t(t): return A_drive*np.cos(omega*t)
    template = []
    for d in D:
        s0 = np.array([0,0,1,0,0], float)
        pN = Params(Delta=float(d), Omega=0.0, alpha=alpha, mu=mu, lam=0.0, Gamma2=0.015, eta=0.0)
        t=0.0; y=s0.copy(); zs_no=[]
        for i in range(int((Ttot)/dt)):
            y = rk4_step(deriv, y, t, dt, pN, Omega_of_t); t+=dt
            if t>=Tskip: zs_no.append(y[2])
        zs_no = np.array(zs_no, float)
        pA = Params(Delta=float(d), Omega=0.0, alpha=alpha, mu=mu, lam=lam, Gamma2=0.015, eta=0.0)
        t=0.0; y=s0.copy(); zs_ar=[]
        for i in range(int((Ttot)/dt)):
            y = rk4_step(deriv, y, t, dt, pA, Omega_of_t); t+=dt
            if t>=Tskip: zs_ar.append(y[2])
        zs_ar = np.array(zs_ar, float)
        times = np.arange(len(zs_no))*dt
        def lockin(sig, times):
            sig = sig - np.mean(sig)
            X = 2/len(times)*np.sum(sig*np.cos(omega*times))
            Y = 2/len(times)*np.sum(sig*np.sin(omega*times))
            return np.sqrt(X**2+Y**2)
        template.append(lockin(zs_ar, times) - lockin(zs_no, times))
    template = np.array(template,float)
    k = float(np.dot(template, data_diff) / max(np.dot(template, template), 1e-12))
    return dict(Lambda=float(k))

def main():
    ap = argparse.ArgumentParser(description="Fit Bell-chip ARP parameters from CSVs.")
    ap.add_argument("--p1", help="CSV with Delta,z_up,z_dn")
    ap.add_argument("--p2", help="CSV with y2|y|A and T2|T2_inv")
    ap.add_argument("--p3-no", dest="p3_no", help="CSV (no ARP) with Delta,R")
    ap.add_argument("--p3-arp", dest="p3_arp", help="CSV (with ARP) with Delta,R")
    ap.add_argument("--out", default="./fit_results")
    ap.add_argument("--alpha", type=float, default=0.6)
    ap.add_argument("--mu", type=float, default=0.2)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    results = {}
    if args.p1 and os.path.exists(args.p1):
        cols = read_csv_columns(args.p1)
        p1 = fit_p1(cols["Delta"], cols["z_up"], cols["z_dn"], alpha=args.alpha, mu=args.mu, Omega=1.0, samples=40)
        results["P1"] = p1
        # Plot fit vs data
        zu_fit, zd_fit = simulate_p1_curves(cols["Delta"], p1["Lambda"], args.alpha, args.mu, 1.0, p1["scale"], p1["offset"])
        plt.figure(); plt.plot(cols["Delta"], cols["z_up"], label="z_up data"); plt.plot(cols["Delta"], cols["z_dn"], label="z_dn data")
        plt.plot(cols["Delta"], zu_fit, label="z_up fit"); plt.plot(cols["Delta"], zd_fit, label="z_dn fit")
        plt.xlabel("Delta"); plt.ylabel("z*"); plt.title("P1 fit"); plt.legend(); plt.tight_layout()
        plt.savefig(os.path.join(args.out, "P1_fit.png"), dpi=150); plt.close()
    if args.p2 and os.path.exists(args.p2):
        p2 = fit_p2(args.p2, alpha=args.alpha, mu=args.mu); results["P2"] = p2
        cols = read_csv_columns(args.p2)
        if "y2" in cols: x = cols["y2"]
        elif "y" in cols: x = cols["y"]**2
        elif "A" in cols: x = cols["A"]**2
        else: x = None
        if "T2_inv" in cols: y = cols["T2_inv"]
        elif "T2" in cols: y = 1.0/cols["T2"]
        else: y = None
        if x is not None and y is not None:
            A = np.vstack([np.ones_like(x), x]).T; b,m = np.linalg.lstsq(A, y, rcond=None)[0]
            xx = np.linspace(x.min(), x.max(), 100); yy = b + m*xx
            plt.figure(); plt.scatter(x, y, s=30); plt.plot(xx, yy)
            plt.xlabel("y^2 (or proxy)"); plt.ylabel("T2^{-1}"); plt.title("P2 fit: linear model"); plt.tight_layout()
            plt.savefig(os.path.join(args.out, "P2_fit.png"), dpi=150); plt.close()
    if args.p3_no and args.p3_arp and os.path.exists(args.p3_no) and os.path.exists(args.p3_arp):
        results["P3"] = fit_p3(args.p3_no, args.p3_arp, alpha=args.alpha, mu=args.mu)
    with open(os.path.join(args.out, "fit_params.json"), "w") as f:
        json.dump(results, f, indent=2)
    print("Saved", os.path.join(args.out, "fit_params.json"))

if __name__ == "__main__":
    main()
