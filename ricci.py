"""adaptive_gr.core  (v0.2)

A single self‑contained module that now bundles three layers:

1. Metric      – tensor algebra helpers (same as v0.1)


2. StressTensor – prefab constructors for common T_{μν}


3. feedback()   – produce  𝔽_{μν}  for several selectable laws



This keeps everything in one file so the prototype remains easy to copy into a notebook.  Later we can split into sub‑modules.

Only NumPy is required; swap import numpy as np → import jax.numpy as np and you get GPU + autodiff. """ from future import annotations

import numpy as np from numpy.typing import ArrayLike Array = np.ndarray

=============================================================================

1. Metric class  (unchanged except minor clean‑ups)

=============================================================================

def _inv_and_det(g: Array): D = g.shape[-1] gf = g.reshape(-1, D, D) inv = np.linalg.inv(gf) det = np.linalg.det(gf) return inv.reshape(g.shape), det.reshape(g.shape[:-2])

class Metric: def init(self, g: ArrayLike): g = np.asarray(g, dtype=float) if g.shape[-1] != g.shape[-2]: raise ValueError("Metric last two axes must be square") self.g = g self.ndim = g.shape[-1] self.g_inv, self.det = _inv_and_det(g)

# -- Γ^ρ_{μν}
def christoffel(self) -> Array:
    g_inv, g = self.g_inv, self.g
    grads = np.stack(np.gradient(g, *[1.0]*self.ndim,
                                 axis=tuple(range(-3, -3-self.ndim, -1))), -4)
    term1 = grads.swapaxes(-4, -3)
    term2 = grads
    term3 = grads.swapaxes(-3, -2)
    Gamma = 0.5 * (g_inv[..., None, :, :] * (term1 + term2 - term3)).sum(-1)
    return Gamma

# -- R_{μν}
def ricci(self) -> Array:
    Gamma = self.christoffel()
    term1 = np.stack(np.gradient(Gamma.swapaxes(-4, -3),
                                 *[1.0]*self.ndim,
                                 axis=tuple(range(-3, -3-self.ndim, -1))), -4).trace(-4, -3)
    Gamma_tr = Gamma.trace(-3, -1)
    term2 = np.gradient(Gamma_tr, *[1.0]*self.ndim,
                        axis=tuple(range(-2, -2-self.ndim, -1)))
    term2 = np.moveaxis(term2, 0, -1)
    return term1 - term2

# -- G_{μν}
def einstein(self) -> Array:
    R = self.ricci()
    R_scalar = (self.g_inv * R).sum(axis=(-2, -1))
    return R - 0.5 * self.g * R_scalar[..., None, None]

=============================================================================

2. Stress‑energy prefab helpers

=============================================================================

class StressTensor: """Namespace of static helpers that return arrays T_{μν}."""

@staticmethod
def perfect_fluid(rho: float, p: float, metric: Metric) -> Array:
    """Return T_{μν} for an FLRW‑like comoving perfect fluid (u^μ=(1,0,0,0))."""
    g = metric.g
    u = np.zeros(g.shape[-1])
    u[0] = 1.0 / np.sqrt(-g[...,0,0])
    outer = np.outer(u, u)
    T = (rho + p) * outer + p * g
    return T

@staticmethod
def scalar_field(phi: Array, dphi: Array, V: float, metric: Metric) -> Array:
    g_inv = metric.g_inv
    grad_phi_sq = (g_inv * np.outer(dphi, dphi)).sum((-2, -1))
    T = np.outer(dphi, dphi) - 0.5 * metric.g * (grad_phi_sq + 2*V)
    return T

=============================================================================

3. Feedback law  𝔽_{μν}  (trace‑squared and norm‑squared)

=============================================================================

def feedback(metric: Metric, T: Array, law: str = "trace2", alpha: float = 1.0) -> Array: """Return 𝔽_{μν} given metric and stress tensor.

Parameters
----------
law   : "trace2" | "norm2"
alpha : coupling prefactor
"""
g = metric.g
if law == "trace2":
    Tr = (metric.g_inv * T).sum((-2, -1))
    F = -2*alpha*Tr[...,None,None]*T + alpha*Tr[...,None,None]**2 * g
elif law == "norm2":
    norm = (metric.g_inv[...,None,None] * metric.g_inv[...,None,:,None] * T[...,None,:,:] * T[...,None,:,:].swapaxes(-1,-2)).sum((-2,-1))
    F = -2*alpha*np.einsum('...μσ,...νσ->...μν', T, T) + 0.5*alpha*norm[...,None,None]*g
else:
    raise ValueError("Unknown feedback law")
return F

=============================================================================

4. Tiny demo if run as script  (2‑D breathing metric)

=============================================================================

if name == "main": import matplotlib.pyplot as plt # 2‑D conformal metric g = a(t)^2 δ_{ij} t = np.linspace(0, 5, 400) a = 1 + 0.3np.sin(2np.pi0.4t) g_t = np.stack([np.diag([ai, ai]) for ai in a])   # shape (T,2,2) M = Metric(g_t) R_trace = M.ricci().trace(-2,-1) plt.plot(t, R_trace, label="Ricci trace (2‑D toy)") plt.xlabel("t") plt.legend(); plt.show()

