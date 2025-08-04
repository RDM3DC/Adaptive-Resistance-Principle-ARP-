
# (Rewriting fully to ensure file is present)
# prime_resonance.py

import math
import json
import argparse
from dataclasses import dataclass, asdict
from typing import List, Tuple, Dict, Optional

try:
    import sympy as sp
except Exception as e:
    raise RuntimeError("This module requires `sympy`. Install with `pip install sympy`.")

@dataclass
class PrimeResonanceResult:
    mode: str
    count: int
    last_iter: int
    min_prime: Optional[int]
    max_prime: Optional[int]
    primes: List[int]
    samples: List[Tuple[int, int]]

K_VALUES: Dict[str, float] = {
    "tight_closure": 1e-4,
    "open_resonance": 1e-2,
    "hybrid": 5e-3,
}

DELTA1 = 0.1234
DELTA2 = 0.9876

def _k_schedule(mode: str, n: int, H: int = 50) -> float:
    if mode == "hybrid":
        return K_VALUES["tight_closure"] if (n // H) % 2 == 0 else K_VALUES["open_resonance"]
    return K_VALUES[mode]

def generate_primes(
    mode: str = "hybrid",
    max_iters: int = 30000,
    target_count: int = 150,
    base_scale: int = 250_000,
    sample_keep: int = 50,
    jitter_period: int = 997,
    jitter_coeff: int = 37,
) -> PrimeResonanceResult:
    pi_a = math.pi
    theta = 0.0
    acc = 0
    primes_found: List[int] = []
    samples: List[Tuple[int, int]] = []
    n = -1
    for n in range(max_iters):
        k_n = _k_schedule(mode, n)
        pi_a += k_n * math.sin(pi_a)
        theta = (theta + pi_a) % (2 * math.pi)
        s1 = abs(math.sin(theta))
        s3 = abs(math.sin(3 * theta + DELTA1))
        c2 = abs(math.cos(2 * theta + DELTA2))
        inc = int(base_scale * (0.34 * s1 + 0.41 * s3 + 0.25 * c2)) + 1
        acc += inc
        if n % jitter_period == 0 and n > 0:
            acc += n * jitter_coeff
        candidate = acc
        if candidate > 10 and sp.isprime(candidate):
            primes_found.append(candidate)
            samples.append((n, candidate))
            if len(primes_found) >= target_count:
                break
    return PrimeResonanceResult(
        mode=mode,
        count=len(primes_found),
        last_iter=n,
        min_prime=min(primes_found) if primes_found else None,
        max_prime=max(primes_found) if primes_found else None,
        primes=primes_found[:sample_keep],
        samples=samples[:min(sample_keep, len(samples))],
    )

def _main():
    p = argparse.ArgumentParser(description="Adaptive Pi Prime Resonance (unbounded accumulator)")
    p.add_argument("--mode", type=str, default="hybrid", choices=list(K_VALUES.keys()))
    p.add_argument("--max-iters", type=int, default=30000)
    p.add_argument("--target", type=int, default=150)
    p.add_argument("--scale", type=int, default=250_000)
    p.add_argument("--json-out", type=str, default="")
    args = p.parse_args()
    res = generate_primes(mode=args.mode, max_iters=args.max_iters, target_count=args.target, base_scale=args.scale)
    print(json.dumps(asdict(res), indent=2))
    if args.json_out:
        with open(args.json_out, "w") as f:
            json.dump(asdict(res), f, indent=2)

if __name__ == "__main__":
    _main()