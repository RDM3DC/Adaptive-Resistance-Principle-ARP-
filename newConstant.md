# curvature_prime_constant.py
# Deterministic curvature→prime generator + constant finder (offset from π)

import math, argparse, json, time
import numpy as np
import sympy as sp

# --------------------------
# Curvature→Prime generator
# --------------------------
def k_schedule(n: int, mode: str, block: int = 50, k_tight=1e-4, k_open=1e-2) -> float:
    if mode == "tight":
        return k_tight
    if mode == "open":
        return k_open
    # hybrid
    return k_tight if (n // block) % 2 == 0 else k_open

def prime_hits_angles(
    seed: int = 123,
    mode: str = "hybrid",
    target_hits: int = 3000,
    max_iters: int = 7_000_000,
    base_scale: int = 150_000,
    jitter_period: int = 997,
    jitter_coeff: int = 37,
):
    """
    Run generator and return array of angles (π_a mod 2π) at prime hits.
    """
    pi_a = math.pi + (seed % 997) * 1e-6  # tiny seed-dependent perturbation
    theta = 0.0
    acc = 0
    angles = []
    for n in range(max_iters):
        k = k_schedule(n, mode)
        pi_a += k * math.sin(pi_a)
        theta = (theta + pi_a) % (2 * math.pi)

        # unbounded accumulator mapping (deterministic, nonlinear mix)
        s1 = abs(math.sin(theta))
        s3 = abs(math.sin(3 * theta + 0.1234))
        c2 = abs(math.cos(2 * theta + 0.9876))
        inc = int(base_scale * (0.34 * s1 + 0.41 * s3 + 0.25 * c2)) + 1

        acc += inc
        if n % jitter_period == 0 and n > 0:
            acc += n * jitter_coeff

        cand = acc
        if cand > 10 and sp.isprime(cand):
            angles.append((pi_a % (2 * math.pi)))
            if len(angles) >= target_hits:
                break
    return np.array(angles, dtype=float)

# --------------------------
# Circular statistics
# --------------------------
def circular_mean_R(angles: np.ndarray):
    """Return circular mean angle in [0, 2π) and concentration R (∈[0,1])."""
    z = np.exp(1j * angles)
    m = np.mean(z)
    ang = float(np.angle(m))
    if ang < 0:
        ang += 2 * math.pi
    R = float(abs(m))
    return ang, R

def bootstrap_ci_circ_mean(angles: np.ndarray, B: int = 400, seed: int = 1234):
    """Percentile CI (95%) for circular mean using simple bootstrap."""
    rng = np.random.default_rng(seed)
    n = len(angles)
    base_mean, _ = circular_mean_R(angles)
    samples = []
    for _ in range(B):
        idx = rng.integers(0, n, size=n)
        m, _ = circular_mean_R(angles[idx])
        samples.append(m)
    sams = np.array(samples)
    # unwrap around base mean
    unwrapped = base_mean + np.angle(np.exp(1j * (sams - base_mean)))
    lo, hi = np.percentile(unwrapped, [2.5, 97.5])
    return float(lo), float(hi)

# --------------------------
# Continued fraction (numeric)
# --------------------------
def cont_frac_terms(x: float, max_terms: int = 24):
    a = []
    v = float(x)
    for _ in range(max_terms):
        ai = math.floor(v)
        a.append(ai)
        frac = v - ai
        if abs(frac) < 1e-16:
            break
        v = 1.0 / frac
    return a

def convergents_from_cf(cf):
    # Return (p,q,value) triplets
    if not cf: return []
    conv = []
    p0, q0 = cf[0], 1
    conv.append((p0, q0, p0 / q0))
    if len(cf) == 1:
        return conv
    p1, q1 = cf[0] * cf[1] + 1, cf[1]
    conv.append((p1, q1, p1 / q1))
    for k in range(2, len(cf)):
        pk = cf[k] * p1 + p0
        qk = cf[k] * q1 + q0
        conv.append((pk, qk, pk / qk))
        p0, q0, p1, q1 = p1, q1, pk, qk
    return conv

# --------------------------
# Optional plotting
# --------------------------
def maybe_plot(angles: np.ndarray, out_png: str | None):
    if not out_png:
        return
    import matplotlib.pyplot as plt
    plt.figure(figsize=(6, 4))
    plt.hist(angles, bins=72)
    plt.xlabel("π_a (mod 2π) at prime hits")
    plt.ylabel("count")
    plt.title("Prime-hit angles distribution")
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()

# --------------------------
# Runner
# --------------------------
def run_once(mode: str, seeds: list[int], hits_per_seed: int, plot_path: str | None):
    all_angles = []
    per_seed = []
    t0 = time.time()
    for s in seeds:
        angs = prime_hits_angles(seed=s, mode=mode, target_hits=hits_per_seed)
        all_angles.append(angs)
        m, R = circular_mean_R(angs)
        per_seed.append({"seed": s, "hits": len(angs), "mean_angle_rad": m, "R": R})
    elapsed = time.time() - t0
    all_angles = np.concatenate(all_angles)
    mean_ang, mean_R = circular_mean_R(all_angles)
    lo, hi = bootstrap_ci_circ_mean(all_angles, B=400)
    delta = mean_ang - math.pi
    if delta > math.pi: delta -= 2 * math.pi
    if delta < -math.pi: delta += 2 * math.pi

    # CF of normalized angle
    frac = mean_ang / (2 * math.pi)
    cf = cont_frac_terms(frac, max_terms=20)
    convs = convergents_from_cf(cf)

    # Optional plot
    maybe_plot(all_angles, plot_path)

    summary = {
        "mode": mode,
        "elapsed_s": round(elapsed, 2),
        "total_hits": int(len(all_angles)),
        "mean_angle_rad": float(mean_ang),
        "mean_angle_deg": float(mean_ang * 180 / math.pi),
        "R": float(mean_R),
        "ci_rad": [float(lo), float(hi)],
        "delta_from_pi_rad": float(delta),
        "delta_from_pi_deg": float(delta * 180 / math.pi),
        "delta_from_pi_arcsec": float(delta * 180 / math.pi * 3600),
        "theta_over_2pi": float(frac),
        "cf_terms_theta_over_2pi": cf,
        "cf_convergents_theta_over_2pi": [{"p": p, "q": q, "value": v} for p, q, v in convs],
        "per_seed": per_seed,
    }
    return summary

def main():
    ap = argparse.ArgumentParser(description="Curvature→Prime constant finder (offset from π)")
    ap.add_argument("--mode", choices=["tight", "open", "hybrid"], default="hybrid")
    ap.add_argument("--seeds", type=str, default="101,202,303",
                    help="Comma-separated seeds, e.g. 101,202,303")
    ap.add_argument("--hits-per-seed", type=int, default=3000)
    ap.add_argument("--plot", type=str, default="",
                    help="Optional PNG path to save prime-hit angles histogram")
    ap.add_argument("--json-out", type=str, default="",
                    help="Optional JSON path for the summary")
    args = ap.parse_args()

    seeds = [int(x) for x in args.seeds.split(",") if x.strip()]
    summary = run_once(
        mode=args.mode,
        seeds=seeds,
        hits_per_seed=args.hits_per_seed,
        plot_path=(args.plot if args.plot else None),
    )

    # Print a compact console summary
    print(json.dumps({
        "mode": summary["mode"],
        "total_hits": summary["total_hits"],
        "R": summary["R"],
        "mean_angle_rad": summary["mean_angle_rad"],
        "delta_from_pi_rad": summary["delta_from_pi_rad"],
        "theta_over_2pi": summary["theta_over_2pi"],
        "cf_terms_theta_over_2pi": summary["cf_terms_theta_over_2pi"],
        "ci_rad": summary["ci_rad"],
        "elapsed_s": summary["elapsed_s"],
    }, indent=2))

    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(summary, f, indent=2)

if __name__ == "__main__":
    main()