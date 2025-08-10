# Adaptive Resistance Principle (ARP) Reference

## Core law (ARP)

\[
\textbf{Adaptive Resistance Principle (ARP):}\qquad 
\frac{dG(t)}{dt} = \alpha\,|I(t)| - \mu\,G(t),
\quad \alpha>0,\;\mu>0,\; G(t)\ge 0.
\]

- \( G(t) \): adaptive conductance (memory state)
- \( I(t) \): driving signal (typically current magnitude, non-negative)
- \( \alpha \): reinforcement rate
- \( \mu \): decay (forgetting) rate

## Closed-form solution (general \(I(t)\))

\[
\textbf{Closed-form:}\qquad 
G(t) = e^{-\mu t}\Big[\,G(0) + \alpha\!\int_{0}^{t} e^{\mu s}\,|I(s)|\,ds\Big].
\]

Equivalently, as a causal exponential smoothing (no checkpoints needed—just timestamps/history):

\[
G(t) = \big(e^{-\mu t} * \alpha\,|I(t)|\big) + G(0)e^{-\mu t},
\quad \text{with kernel } k(t)=e^{-\mu t}\mathbf{1}_{t\ge 0}.
\]

## Special cases you’ll actually use

### Constant input \(|I(t)| = I_0\)

\[
G(t) = G_\infty + \big(G(0)-G_\infty\big)e^{-\mu t},
\qquad G_\infty = \frac{\alpha I_0}{\mu},\quad \tau=\mu^{-1}.
\]

### Piecewise-constant input (step changes)

For intervals \([t_k,t_{k+1})\) with level \(I_k\):

\[
G(t) = G_\infty^{(k)} + \big(G(t_k^+) - G_\infty^{(k)}\big)e^{-\mu (t-t_k)},
\qquad G_\infty^{(k)}=\frac{\alpha I_k}{\mu}.
\]

### Stationary ergodic input with mean \(\mathbb{E}[|I|]\)

\[
\lim_{t\to\infty} G(t) = \frac{\alpha}{\mu}\,\mathbb{E}[|I|].
\]

## Transfer function view (LTI w.r.t. \(|I|\))

Treat \(u(t)=|I(t)|\) as input:

\[
\mathcal{L}\{G\}(s) = \frac{\alpha}{s+\mu}\,\mathcal{L}\{u\}(s) + \frac{G(0)}{s+\mu}.
\quad\Rightarrow\quad H(s)=\frac{\alpha}{s+\mu}.
\]

So ARP is an exponential low-pass tracker of \(|I|\) with cutoff \(\mu\).

## Discrete-time (forward Euler, step \(\Delta t\))

\[
G_{k+1} = (1-\mu\Delta t)G_k + \alpha\Delta t\,|I_k|.
\]

- Stability: \(0<\mu\Delta t<2\) (practically, \(\mu\Delta t\ll 1\)).
- Z-domain (with one-step input delay from Euler):

\[
\frac{G(z)}{U(z)} = \frac{\alpha\Delta t\,z^{-1}}{1-(1-\mu\Delta t)\,z^{-1}}.
\]

## Positivity, bounds, and monotonicity

If \(G(0)\ge 0\) and \(|I(t)|\ge 0\) then \(G(t)\ge 0\) for all \(t\).
If \(|I(t)|\le I_{\max}\):

\[
0 \le G(t) \le \frac{\alpha I_{\max}}{\mu}
\quad\text{and}\quad
G(t)\text{ moves monotonically toward the current piecewise }G_\infty.
\]

## Global exponential stability (constant input)

Let \(e(t)=G(t)-G_\infty\). Then

\[
\dot e(t) = -\mu e(t),\qquad V=e^2 \Rightarrow \dot V = -2\mu V \le 0,
\]

so \(G \to G_\infty\) globally and exponentially.

## Simple closed-loop example (Ohmic coupling)

If the environment is approximately Ohmic with voltage \(V(t)\) so that \(|I(t)|\approx |V(t)|\,G(t)\), then:

\[
\dot G = (\alpha|V(t)|-\mu)G.
\]

- For constant \(|V|\): \(G(t)=G(0)e^{(\alpha|V|-\mu)t}\).
- Threshold behavior: decay if \(|V|<\mu/\alpha\), growth if \(|V|>\mu/\alpha\).
  (In practice you add saturation/normalization to cap \(G\).)

## Multi-edge/network form

For edges \((i,j)\) with currents \(I_{ij}(t)\):

\[
\dot G_{ij}(t) = \alpha\,|I_{ij}(t)| - \mu\,G_{ij}(t).
\]

Vectorized with \(G\in\mathbb{R}^m_{\ge 0}\):

\[
\dot G = \alpha\,|I(x,G,t)| - \mu\,G,
\]

where \(I\) can depend on states \(x\) and the network physics. Fixed points satisfy
\(\mu G^\star = \alpha |I(x,G^\star)|\). Contraction holds if the sensitivity of \(I\) to \(G\) is small enough relative to \(\mu/\alpha\).

## MD-ARP (optional extension with C,L)

When you want adaptive impedance, let conductance \(G\), capacitance \(C\), inductance \(L\) adapt to their “driving magnitudes”:

\[
\dot G = \alpha_G\,|I| - \mu_G\,G,\qquad 
\dot C = \alpha_C\,|V| - \mu_C\,C,\qquad 
\dot L = \alpha_L\,|\dot I| - \mu_L\,L.
\]

Same closed-form per coordinate; all inherit the low-pass tracking and stability properties.

---

## TL;DR (what to remember)

- Law: \(\dot G=\alpha|I|-\mu G\).
- Solution: \(G(t)=e^{-\mu t}\big[G(0)+\alpha\!\int_0^t e^{\mu s}|I(s)|ds\big]\).
- Constant input: \(G_\infty=\alpha I_0/\mu\), time constant \(1/\mu\).
- Discrete: \(G_{k+1}=(1-\mu\Delta t)G_k+\alpha\Delta t|I_k|\).
- Stability: global, exponential to the instantaneous \(G_\infty\); positive and bounded.

