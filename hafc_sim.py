
"""HAFC Simulator v2 — Hybrid Adaptive Field Computer.

Upgraded from the original toy simulator to a full EGATL-backed engine.

Modes
-----
lattice (default)
    2-D QWZ admittance lattice with entropy-gated ARP, adaptive pi_a,
    damage/recovery protocol, pi_f loop signatures, and plaquette tracking.

maze
    Classic 5x5 maze on a simple resistive graph (backward compat).

classic
    Tiny 6-node two-path graph (backward compat).

Run
---
    python hafc_sim.py                       # lattice 6x6, damage at t=12
    python hafc_sim.py --nx 8 --ny 8 --T 40  # bigger lattice
    python hafc_sim.py --mode maze           # classic maze solver
    python hafc_sim.py --ablation            # 3-way ablation comparison
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

# Put workspace root on path so ``from solver.egatl import ...`` works
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solver.egatl import (
    EGATLParams,
    EntropyParams,
    RulerParams,
    build_qwz_lattice,
    run_recovery_protocol,
    summarize_recovery,
    compare_ablations,
    effective_transfer,
    boundary_current_fraction,
    top_edge_fraction,
    proxy_chern_series,
    plaquette_signatures,
    boundary_signature_series,
    top_edge_signature_series,
    plaquette_signature_series,
    bott_index_series,
    qwz_bulk_chern_series,
)

# ================================================================== #
#  Phase-Lift primitives (standalone, no lattice dependency)           #
# ================================================================== #

def wrap_to_pi(angle: float) -> float:
    """Wrap any real angle to (-pi, pi]."""
    a = (angle + math.pi) % (2 * math.pi) - math.pi
    if a <= -math.pi:
        a += 2 * math.pi
    return a


@dataclass
class PhaseLiftState:
    theta_prev: float
    theta_R: float
    theta_R0: float
    w: int
    b: int  # +/-1

    @staticmethod
    def init_from_theta(theta0: float) -> "PhaseLiftState":
        return PhaseLiftState(theta_prev=theta0, theta_R=theta0,
                              theta_R0=theta0, w=0, b=1)


def phase_lift_step(
    st: PhaseLiftState, theta: float, pi_a: float,
) -> Tuple[PhaseLiftState, float, float, int, int, int]:
    r = wrap_to_pi(theta - st.theta_prev)
    r_clip = float(np.clip(r, -pi_a, +pi_a))
    theta_R = st.theta_R + r_clip
    w = int(np.round((theta_R - st.theta_R0) / (2 * math.pi)))
    b = 1 if (w % 2 == 0) else -1
    flip = 1 if (b != st.b) else 0
    st2 = PhaseLiftState(theta_prev=theta, theta_R=theta_R,
                         theta_R0=st.theta_R0, w=w, b=b)
    return st2, r, r_clip, w, b, flip


# ================================================================== #
#  Simple-graph support (backward compat: maze / classic modes)        #
# ================================================================== #

@dataclass
class Graph:
    n: int
    edges: List[Tuple[int, int]]

    def incidence(self) -> np.ndarray:
        m = len(self.edges)
        B = np.zeros((m, self.n), dtype=float)
        for e, (u, v) in enumerate(self.edges):
            B[e, u] = 1.0
            B[e, v] = -1.0
        return B


@dataclass
class ARPParams:
    alpha_G: float = 1.0
    mu_G: float = 0.4
    G_min: float = 1e-3
    G_budget: Optional[float] = None


@dataclass
class PiAParams:
    pi0: float = math.pi
    alpha_pi: float = 0.6
    mu_pi: float = 0.25
    pi_min: float = 0.25
    pi_max: float = 2.75 * math.pi


def solve_resistive_flows(
    graph: Graph, G: np.ndarray, source: int, sink: int, I_in: float = 1.0,
) -> Tuple[np.ndarray, np.ndarray]:
    n = graph.n
    B = graph.incidence()
    m = B.shape[0]
    L = B.T @ (G.reshape(m, 1) * B)
    b = np.zeros(n)
    b[source] = I_in
    b[sink] = -I_in
    mask = np.ones(n, dtype=bool)
    mask[sink] = False
    phi = np.zeros(n)
    phi[mask] = np.linalg.solve(L[mask][:, mask], b[mask])
    I = np.array([G[e] * (phi[u] - phi[v]) for e, (u, v) in enumerate(graph.edges)])
    return phi, I


def simulate_graph(
    graph: Graph, source: int, sink: int,
    T: float = 40.0, dt: float = 0.05, seed: int = 7,
    arp: ARPParams = ARPParams(), pia: PiAParams = PiAParams(),
    omega: float = 0.65, noise_sigma: float = 0.10, kappa_flip: float = 0.35,
) -> Dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    m = len(graph.edges)
    K = int(np.ceil(T / dt)) + 1
    t = np.linspace(0.0, T, K)
    G = np.ones(m)
    pi_a = pia.pi0
    st = PhaseLiftState.init_from_theta(0.0)

    G_hist = np.zeros((K, m))
    I_hist = np.zeros((K, m))
    phi_hist = np.zeros((K, graph.n))
    pi_hist = np.zeros(K)
    theta_hist = np.zeros(K)
    thetaR_hist = np.zeros(K)
    w_hist = np.zeros(K, dtype=int)
    b_hist = np.zeros(K, dtype=int)
    flip_hist = np.zeros(K, dtype=int)
    S_hist = np.zeros(K)

    for k in range(K):
        phi, I = solve_resistive_flows(graph, G, source, sink)
        activity = float(np.mean(np.abs(I)))
        z = (1.0 + 0.25 * activity) * np.exp(1j * omega * t[k]) + \
            noise_sigma * (rng.normal() + 1j * rng.normal())
        theta = float(np.angle(z))
        st, r, r_clip, w, b, flip = phase_lift_step(st, theta, pi_a)
        S = activity + kappa_flip * flip

        dG = arp.alpha_G * np.abs(I) - arp.mu_G * G
        G = np.maximum(arp.G_min, G + dt * dG)
        if arp.G_budget is not None:
            total = float(np.sum(G))
            if total > arp.G_budget > 0:
                G *= arp.G_budget / total

        dpi = pia.alpha_pi * S - pia.mu_pi * (pi_a - pia.pi0)
        pi_a = float(np.clip(pi_a + dt * dpi, pia.pi_min, pia.pi_max))

        G_hist[k] = G; I_hist[k] = I; phi_hist[k] = phi
        pi_hist[k] = pi_a; theta_hist[k] = theta
        thetaR_hist[k] = st.theta_R; w_hist[k] = w
        b_hist[k] = b; flip_hist[k] = flip; S_hist[k] = S

    rb = np.zeros(K)
    if K > 1:
        rb[1:] = np.cumsum(flip_hist[1:]) / np.arange(1, K)

    return dict(t=t, G=G_hist, I=I_hist, phi=phi_hist, pi_a=pi_hist,
                theta=theta_hist, theta_R=thetaR_hist, w=w_hist, b=b_hist,
                flip=flip_hist, S=S_hist, r_b=rb,
                edges=np.array(graph.edges, dtype=int))


# ================================================================== #
#  Built-in graphs                                                     #
# ================================================================== #

def default_toy_graph() -> Tuple[Graph, int, int, Dict[int, str]]:
    edges = [(0,1),(1,2),(2,5),(0,3),(3,4),(4,5),(1,3),(2,4)]
    return Graph(n=6, edges=edges), 0, 5, {0:"s",5:"t",1:"a1",2:"a2",3:"b1",4:"b2"}


def maze_graph_5x5():
    rows, cols = 5, 5
    edges = [
        (0,1),(1,2),(2,3),(3,4),(0,5),(2,7),(4,9),
        (5,6),(7,8),(8,9),(5,10),(6,11),(7,12),
        (10,11),(11,12),(12,13),(13,14),
        (10,15),(11,16),(12,17),(13,18),(14,19),
        (15,16),(16,17),(17,18),(18,19),(15,20),(19,24),
        (20,21),(21,22),(22,23),(23,24),
    ]
    pos = {r*cols+c: (float(c), float(-r)) for r in range(rows) for c in range(cols)}
    return Graph(n=25, edges=edges), 0, 24, {0:"Source",24:"Sink"}, pos


# ================================================================== #
#  EGATL lattice mode                                                  #
# ================================================================== #

def run_lattice(args):
    """Full EGATL simulation with damage/recovery."""
    eg = EGATLParams(
        alpha0=2.5, S_c=0.3, dS=0.5, mu0=0.25, S0=2.0,
        lambda_s=0.05, g_min=0.01, g_max=5.0,
        g_imag_max=3.0, budget_re=120.0,
    )
    ent = EntropyParams(S_init=1.5, S_eq=1.0, gamma=0.20,
                        kappa_slip=0.10, Tij=1.0)
    ruler = RulerParams(pi0=math.pi, pi_init=math.pi,
                        alpha_pi=0.15, mu_pi=0.15,
                        pi_min=0.5, pi_max=12.0)

    print(f"[HAFC v2] EGATL lattice {args.nx}x{args.ny}, "
          f"T={args.T}, damage at t={args.damage_time}")

    lattice, out = run_recovery_protocol(
        nx=args.nx, ny=args.ny, T=args.T, dt=args.dt,
        seed=args.seed, damage_time=args.damage_time,
        mass=args.mass, damage_factor=1e-4,
        eg=eg, ent=ent, ruler=ruler,
    )

    t = out["t"]
    K = len(t)

    # --- compute observables ---
    Yeff = np.array([
        effective_transfer(out["phi"][k], lattice.source_cell, lattice.sink_cell)
        for k in range(K)
    ])
    Bfrac = np.array([
        boundary_current_fraction(out["I_norm"][k], lattice.bonds)
        for k in range(K)
    ])
    Tfrac = np.array([
        top_edge_fraction(out["I_norm"][k], lattice) for k in range(K)
    ])
    Sig_bnd = boundary_signature_series(out["g"], lattice, out["pi_a"])
    Sig_top = top_edge_signature_series(out["g"], lattice, out["pi_a"])
    Sig_plaq = plaquette_signature_series(out["g"], lattice, out["pi_a"])
    Chern = proxy_chern_series(out["g"], lattice)
    QWZChern = qwz_bulk_chern_series(
        out["g"], lattice, out["pi_a"], out["S"], mass0=args.mass,
    )
    Bott = bott_index_series(
        out["g"], lattice, out["pi_a"], out["S"], mass0=args.mass,
    )

    # --- summary report ---
    summ = summarize_recovery(out, lattice, args.damage_time)

    print(f"\n[HAFC v2] {K} steps, {lattice.n_bonds} bonds, "
          f"{len(lattice.plaquettes)} plaquettes")
    print("\n" + "=" * 66)
    print("   RECOVERY SUMMARY")
    print("=" * 66)
    print(f"\n  {'Metric':<28s} {'Pre':>10s} {'Post':>10s} {'Recovery':>10s}")
    print("  " + "-" * 60)
    rows = [
        ("Y_eff (transfer)", "transfer_pre", "transfer_post", "transfer_recovery"),
        ("Boundary current", "boundary_pre", "boundary_post", None),
        ("Top-edge current", "top_edge_pre", "top_edge_post", None),
        ("Sig boundary", "sig_boundary_pre", "sig_boundary_post", "sig_boundary_recovery"),
        ("Sig top-edge", "sig_top_edge_pre", "sig_top_edge_post", "sig_top_edge_recovery"),
        ("Sig plaquette", "sig_plaquette_pre", "sig_plaquette_post", "sig_plaquette_recovery"),
    ]
    for label, pk, postk, rk in rows:
        pre_v = summ.get(pk, 0)
        post_v = summ.get(postk, 0)
        rec_v = summ.get(rk, 0) if rk else post_v / max(1e-12, pre_v)
        print(f"  {label:<28s} {pre_v:10.4f} {post_v:10.4f} {rec_v:10.4f}")

    print("\n  Topological readout")
    print(f"    Chern proxy       : {summ['chern_pre']:10.4f} -> {summ['chern_post']:10.4f}   Δ={summ['chern_delta']:+.4f}")
    print(f"    QWZ bulk Chern    : {summ['qzw_chern_pre']:10.4f} -> {summ['qzw_chern_post']:10.4f}   Δ={summ['qzw_chern_delta']:+.4f}")
    print(f"    QWZ Bott          : {summ['bott_pre']:10.4f} -> {summ['bott_post']:10.4f}   Δ={summ['bott_delta']:+.4f}")
    print(f"    Bott int. error   : {summ['bott_integer_error_pre']:10.4f} -> {summ['bott_integer_error_post']:10.4f}")

    print(f"\n  Final S = {summ['final_S']:.4f}   "
          f"Final pi_a = {summ['final_pi_a']:.4f}   "
          f"GMRES fails = {summ['gmres_fails']}")

    # --- plaquette snapshots ---
    dmg_step = int(args.damage_time / args.dt)
    late_step = min(K - 1, dmg_step + int(6.0 / args.dt))
    plaq_pre = plaquette_signatures(
        out["g"][max(0, dmg_step - 1)], lattice,
        float(out["pi_a"][max(0, dmg_step - 1)]))
    plaq_dmg = plaquette_signatures(
        out["g"][min(K - 1, dmg_step + 2)], lattice,
        float(out["pi_a"][min(K - 1, dmg_step + 2)]))
    plaq_post = plaquette_signatures(
        out["g"][late_step], lattice, float(out["pi_a"][late_step]))

    print(f"\n  Plaquette snapshots (mean / std / min):")
    for label, arr in [("Pre-damage", plaq_pre), ("Damage+2dt", plaq_dmg),
                       ("Post-settle", plaq_post)]:
        print(f"    {label:<14s}: {arr.mean():.4f} / {arr.std():.4f} / {arr.min():.4f}")

    # --- dashboard ---
    if not args.no_plot:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            _dashboard_lattice(
                t, args.damage_time, Yeff, Bfrac, Tfrac,
                Sig_bnd, Sig_top, Sig_plaq, Chern, QWZChern, Bott,
                out["S"], out["pi_a"], plaq_pre, plaq_dmg,
                lattice,
            )
            print("\n  Dashboard saved: hafc_v2_dashboard.png")
        except ImportError:
            print("\n  (matplotlib not available)")

    return lattice, out, summ


def _dashboard_lattice(t, damage_time, Yeff, Bfrac, Tfrac,
                       Sig_bnd, Sig_top, Sig_plaq, Chern, QWZChern, Bott,
                       S_hist, pi_a_hist, plaq_pre, plaq_dmg,
                       lattice):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(4, 2, figsize=(15, 14))
    fig.suptitle("HAFC v2 — EGATL Damage / Recovery", fontsize=14, fontweight="bold")
    dmg = dict(color="red", ls="--", alpha=0.5, label="damage")

    ax = axes[0, 0]
    ax.plot(t, Yeff, color="steelblue", lw=1.5)
    ax.axvline(damage_time, **dmg)
    ax.set_ylabel("Y_eff"); ax.set_title("Effective Transfer"); ax.grid(alpha=0.3)

    ax = axes[0, 1]
    ax.plot(t, Bfrac, color="forestgreen", lw=1.3, label="boundary")
    ax.plot(t, Tfrac, color="orange", lw=1.3, label="top-edge")
    ax.axvline(damage_time, **dmg)
    ax.set_ylabel("fraction"); ax.set_title("Current Distribution")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    ax = axes[1, 0]
    ax.plot(t, Sig_bnd, color="royalblue", lw=1.6, label="boundary")
    ax.plot(t, Sig_top, color="crimson", lw=1.6, label="top-edge")
    ax.axvline(damage_time, **dmg)
    ax.set_ylabel("signature"); ax.set_title("pi_f Loop Signatures")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    ax = axes[1, 1]
    ax.plot(t, Sig_plaq, color="darkorchid", lw=1.6)
    ax.axvline(damage_time, **dmg)
    ax.set_ylabel("mean sig"); ax.set_title("Plaquette Signature"); ax.grid(alpha=0.3)

    ax = axes[2, 0]
    ax.plot(t, Chern, color="teal", lw=1.4, label="Chern proxy")
    ax.plot(t, QWZChern, color="navy", lw=1.2, label="QWZ bulk Chern")
    ax.plot(t, Bott, color="black", lw=1.2, label="QWZ Bott")
    ax.axvline(damage_time, **dmg)
    ax.set_ylabel("topology"); ax.set_title("Topological Readout")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)

    ax = axes[2, 1]
    ax.plot(t, S_hist, color="sienna", lw=1.3, label="S")
    ax.plot(t, pi_a_hist, color="purple", lw=1.3, label="pi_a")
    ax.axvline(damage_time, **dmg)
    ax.set_ylabel("value"); ax.set_title("Entropy & Ruler"); ax.legend(fontsize=8); ax.grid(alpha=0.3)

    npx, npy = lattice.nx - 1, lattice.ny - 1
    for idx, (label, arr, cmap) in enumerate([
        ("Pre-damage", plaq_pre, "viridis"),
        ("Damage+2dt", plaq_dmg, "inferno"),
    ]):
        ax = axes[3, idx]
        grid = arr.reshape(npy, npx)
        im = ax.imshow(grid, origin="lower", cmap=cmap,
                       vmin=0, vmax=max(1.2, grid.max()),
                       aspect="equal", extent=[0, npx, 0, npy])
        ax.set_title(f"Plaquettes: {label}"); ax.set_xlabel("x"); ax.set_ylabel("y")
        plt.colorbar(im, ax=ax, shrink=0.7, label="S_p")

    plt.tight_layout()
    plt.savefig("hafc_v2_dashboard.png", dpi=150)
    plt.close()


# ================================================================== #
#  Graph-mode dashboards                                               #
# ================================================================== #

def quick_dashboard(out: Dict[str, np.ndarray], title: str = "HAFC Simulator") -> None:
    import matplotlib.pyplot as plt

    t = out["t"]
    fig, axes = plt.subplots(3, 2, figsize=(14, 10), sharex=True)
    fig.suptitle(title, fontsize=14)

    ax = axes[0, 0]; G = out["G"]; edges = out["edges"]
    for e in range(G.shape[1]):
        ax.plot(t, G[:, e], label=f"{edges[e][0]}-{edges[e][1]}")
    ax.set_ylabel("G"); ax.set_title("Conductances")
    if G.shape[1] <= 12: ax.legend(fontsize=6, ncol=2)

    ax = axes[0, 1]; ax.plot(t, out["pi_a"], color="purple")
    ax.set_ylabel("pi_a"); ax.set_title("Adaptive pi_a")

    ax = axes[1, 0]
    ax.plot(t, out["theta"], alpha=0.4, label="raw")
    ax.plot(t, out["theta_R"], label="lifted")
    ax.set_ylabel("phase"); ax.set_title("Phase tracking"); ax.legend(fontsize=7)

    ax = axes[1, 1]; ax.plot(t, out["w"], color="teal")
    ax.set_ylabel("w"); ax.set_title("Winding number")

    ax = axes[2, 0]; ax.step(t, out["b"], where="post", color="crimson")
    ax.set_ylabel("b"); ax.set_xlabel("time"); ax.set_title("Parity b=(-1)^w")

    ax = axes[2, 1]; ax.plot(t, out["r_b"], color="orange")
    ax.set_ylabel("rate"); ax.set_xlabel("time"); ax.set_title("Flip rate")

    plt.tight_layout(); plt.show()


def draw_maze_solution(graph, pos, G_final, title="Maze (G weights)", node_size=60.0):
    import matplotlib.pyplot as plt
    g = np.asarray(G_final, dtype=float)
    span = max(1e-12, g.max() - g.min())
    gn = (g - g.min()) / span
    plt.figure(figsize=(7, 7)); plt.title(title)
    for (u, v), gv in zip(graph.edges, gn):
        x1, y1 = pos[u]; x2, y2 = pos[v]
        plt.plot([x1, x2], [y1, y2], lw=0.5+5*gv, alpha=0.15+0.85*gv, color="steelblue")
    xs = [pos[i][0] for i in range(graph.n)]
    ys = [pos[i][1] for i in range(graph.n)]
    plt.scatter(xs, ys, s=node_size, zorder=5, color="black")
    plt.text(pos[0][0]+0.1, pos[0][1]+0.1, "S", fontsize=12, fontweight="bold", color="green")
    plt.text(pos[24][0]+0.1, pos[24][1]+0.1, "T", fontsize=12, fontweight="bold", color="red")
    plt.axis("equal"); plt.axis("off"); plt.tight_layout(); plt.show()


# ================================================================== #
#  CLI                                                                 #
# ================================================================== #

def main() -> None:
    ap = argparse.ArgumentParser(description="HAFC Simulator v2")
    ap.add_argument("--mode", choices=["lattice", "maze", "classic"],
                    default="lattice")
    ap.add_argument("--nx", type=int, default=6)
    ap.add_argument("--ny", type=int, default=6)
    ap.add_argument("--T", type=float, default=30.0)
    ap.add_argument("--dt", type=float, default=0.1)
    ap.add_argument("--damage-time", type=float, default=12.0)
    ap.add_argument("--mass", type=float, default=-1.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-plot", action="store_true")
    ap.add_argument("--ablation", action="store_true",
                    help="Run 3-way ablation (lattice mode only)")
    args = ap.parse_args()

    if args.mode == "lattice":
        run_lattice(args)
        if args.ablation:
            print("\n" + "=" * 66)
            print("   ABLATION COMPARISON")
            print("=" * 66)
            results = compare_ablations(
                nx=args.nx, ny=args.ny, T=args.T, dt=args.dt,
                seed=args.seed, damage_time=args.damage_time,
                mass=args.mass,
            )
            for name, (_, _, summ) in results.items():
                print(f"\n  --- {name} ---")
                for key in ["transfer_recovery", "sig_boundary_recovery",
                             "sig_top_edge_recovery", "sig_plaquette_recovery",
                             "qzw_chern_post", "bott_post", "bott_integer_error_post"]:
                    v = summ.get(key, None)
                    print(f"    {key}: {v:.4f}" if isinstance(v, float) else f"    {key}: N/A")

    elif args.mode == "maze":
        graph, s, t, names, pos = maze_graph_5x5()
        out = simulate_graph(
            graph, s, t, T=100.0, dt=0.05,
            arp=ARPParams(alpha_G=1.2, mu_G=0.5, G_budget=15.0),
            pia=PiAParams(pi0=math.pi, alpha_pi=0.7, mu_pi=0.30),
        )
        G_final = out["G"][-1]
        print("\nSurviving Edges (high G):")
        thr = 0.25 * float(np.max(G_final))
        for (u, v), g in sorted(zip(out["edges"], G_final), key=lambda x: -x[1]):
            if g >= thr:
                print(f"  {u:02d}-{v:02d}: G={g:.4f}")
        if not args.no_plot:
            quick_dashboard(out, title="HAFC v2 — 5x5 Maze")
            draw_maze_solution(graph, pos, G_final)

    else:  # classic
        graph, s, t, names = default_toy_graph()
        out = simulate_graph(graph, s, t, T=40.0, dt=0.05)
        if not args.no_plot:
            quick_dashboard(out, title="HAFC v2 — Classic 6-node")


if __name__ == "__main__":
    main()
