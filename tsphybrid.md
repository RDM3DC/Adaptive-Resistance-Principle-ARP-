Extracted and Refined Equations from the Proof Sketch
The proof sketch analyzes the ARP flow, defined by the differential equation for conductance GijG_{ij}G_{ij}
, and its effect on the weighted-length functional ( E(G) ). Below are the key equations, refined for clarity and consistency with the hybrid solver’s notation.
1. ARP Conductance Flow
The dynamics of conductance GijG_{ij}G_{ij}
 for edge (i,j)∈T(i,j) \in \mathcal{T}(i,j) \in \mathcal{T}
 (where T\mathcal{T}\mathcal{T}
 is the fixed tour topology) are:
G˙ij=α∣Iij∣−μGij,(1)\dot{G}_{ij} = \alpha |I_{ij}| - \mu G_{ij}, \tag{1}\dot{G}_{ij} = \alpha |I_{ij}| - \mu G_{ij}, \tag{1}

where:
GijG_{ij}G_{ij}
: Conductance of edge ( (i,j) ).

IijI_{ij}I_{ij}
: Current through edge ( (i,j) ).

α=10−2\alpha = 10^{-2}\alpha = 10^{-2}
: Conductance growth rate.

μ=10−3\mu = 10^{-3}\mu = 10^{-3}
: Conductance decay rate.
2. Weighted-Length Functional
The energy functional to minimize is:
E(G)=∑(i,j)∈TWijLij,(2)E(G) = \sum_{(i,j) \in \mathcal{T}} W_{ij} L_{ij}, \tag{2}E(G) = \sum_{(i,j) \in \mathcal{T}} W_{ij} L_{ij}, \tag{2}

where:
Wij=1GijW_{ij} = \frac{1}{G_{ij}}W_{ij} = \frac{1}{G_{ij}}
: Edge weight, inversely proportional to conductance.

Lij=∥pi−pj∥2L_{ij} = \| p_i - p_j \|_2L_{ij} = \| p_i - p_j \|_2
: Euclidean distance between cities ( i ) and ( j ) with positions pi,pj∈R2p_i, p_j \in \mathbb{R}^2p_i, p_j \in \mathbb{R}^2
.
For VTSP, we extend this to include smoothness penalties:
E_{\text{VTSP}}(G, \pi) = \sum_{(i,j) \in \mathcal{T}} W_{ij} L_{ij} + \text{memory_weight} \cdot T(\pi) + \text{entropy_weight} \cdot E(\pi),
where:
π\pi\pi
: Tour permutation.

T(π)=∑i=1n−1t(pπi−1,pπi,pπi+1)T(\pi) = \sum_{i=1}^{n-1} t(p_{\pi_{i-1}}, p_{\pi_i}, p_{\pi_{i+1}})T(\pi) = \sum_{i=1}^{n-1} t(p_{\pi_{i-1}}, p_{\pi_i}, p_{\pi_{i+1}})
: Total turn penalty.

E(π)=∑i=1n−1e(pπi−1,pπi,pπi+1)E(\pi) = \sum_{i=1}^{n-1} e(p_{\pi_{i-1}}, p_{\pi_i}, p_{\pi_{i+1}})E(\pi) = \sum_{i=1}^{n-1} e(p_{\pi_{i-1}}, p_{\pi_i}, p_{\pi_{i+1}})
: Total entropy penalty.

t(pπi−1,pπi,pπi+1)=arccos⁡((pπi−pπi−1)⋅(pπi+1−pπi)∥pπi−pπi−1∥2⋅∥pπi+1−pπi∥2+10−8)πt(p_{\pi_{i-1}}, p_{\pi_i}, p_{\pi_{i+1}}) = \frac{\arccos\left( \frac{(p_{\pi_i} - p_{\pi_{i-1}}) \cdot (p_{\pi_{i+1}} - p_{\pi_i})}{\| p_{\pi_i} - p_{\pi_{i-1}} \|_2 \cdot \| p_{\pi_{i+1}} - p_{\pi_i} \|_2 + 10^{-8}} \right)}{\pi}t(p_{\pi_{i-1}}, p_{\pi_i}, p_{\pi_{i+1}}) = \frac{\arccos\left( \frac{(p_{\pi_i} - p_{\pi_{i-1}}) \cdot (p_{\pi_{i+1}} - p_{\pi_i})}{\| p_{\pi_i} - p_{\pi_{i-1}} \|_2 \cdot \| p_{\pi_{i+1}} - p_{\pi_i} \|_2 + 10^{-8}} \right)}{\pi}
.

e(pπi−1,pπi,pπi+1)=∥v2∥v2∥2+10−8−v1+v22⋅∥(v1+v2)/2∥2+10−8∥2e(p_{\pi_{i-1}}, p_{\pi_i}, p_{\pi_{i+1}}) = \left\| \frac{v_2}{\| v_2 \|_2 + 10^{-8}} - \frac{v_1 + v_2}{2 \cdot \| (v_1 + v_2)/2 \|_2 + 10^{-8}} \right\|_2e(p_{\pi_{i-1}}, p_{\pi_i}, p_{\pi_{i+1}}) = \left\| \frac{v_2}{\| v_2 \|_2 + 10^{-8}} - \frac{v_1 + v_2}{2 \cdot \| (v_1 + v_2)/2 \|_2 + 10^{-8}} \right\|_2
, with v1=pπi−pπi−1v_1 = p_{\pi_i} - p_{\pi_{i-1}}v_1 = p_{\pi_i} - p_{\pi_{i-1}}
, v2=pπi+1−pπiv_2 = p_{\pi_{i+1}} - p_{\pi_i}v_2 = p_{\pi_{i+1}} - p_{\pi_i}
.

\text{memory_weight} = 0.7, \text{entropy_weight} = 0.3.
3. Edge Current
By Ohm’s law, the current is:
∣Iij∣=GijVij,(3)|I_{ij}| = G_{ij} V_{ij}, \tag{3}|I_{ij}| = G_{ij} V_{ij}, \tag{3}

where Vij(t)V_{ij}(t)V_{ij}(t)
 is the potential drop across edge ( (i,j) ). Since node potentials are between 0 V (sink) and 1 V (source):
0≤Vij(t)≤1,(4)0 \leq V_{ij}(t) \leq 1, \tag{4}0 \leq V_{ij}(t) \leq 1, \tag{4}

0≤∣Iij∣≤Gij.(5)0 \leq |I_{ij}| \leq G_{ij}. \tag{5}0 \leq |I_{ij}| \leq G_{ij}. \tag{5}

In the code, a unit current is injected (I0,n/2=1.0I_{0, n/2} = 1.0I_{0, n/2} = 1.0
), but the proof assumes a voltage source, which may require clarification (see below).
4. Time Derivative of Energy
Differentiating ( E(G) ):
dEdt=∑(i,j)∈TLijddt(1Gij)=∑(i,j)∈TLij(−G˙ijGij2).(6)\frac{dE}{dt} = \sum_{(i,j) \in \mathcal{T}} L_{ij} \frac{d}{dt} \left( \frac{1}{G_{ij}} \right) = \sum_{(i,j) \in \mathcal{T}} L_{ij} \left( -\frac{\dot{G}_{ij}}{G_{ij}^2} \right). \tag{6}\frac{dE}{dt} = \sum_{(i,j) \in \mathcal{T}} L_{ij} \frac{d}{dt} \left( \frac{1}{G_{ij}} \right) = \sum_{(i,j) \in \mathcal{T}} L_{ij} \left( -\frac{\dot{G}_{ij}}{G_{ij}^2} \right). \tag{6}

Substitute G˙ij=α∣Iij∣−μGij\dot{G}_{ij} = \alpha |I_{ij}| - \mu G_{ij}\dot{G}_{ij} = \alpha |I_{ij}| - \mu G_{ij}
:
dEdt=∑(i,j)∈TLijGij(μ−α∣Iij∣Gij).(7)\frac{dE}{dt} = \sum_{(i,j) \in \mathcal{T}} \frac{L_{ij}}{G_{ij}} \left( \mu - \alpha \frac{|I_{ij}|}{G_{ij}} \right). \tag{7}\frac{dE}{dt} = \sum_{(i,j) \in \mathcal{T}} \frac{L_{ij}}{G_{ij}} \left( \mu - \alpha \frac{|I_{ij}|}{G_{ij}} \right). \tag{7}

5. Lyapunov Decrease Condition
Using ∣Iij∣Gij=Vij≤1\frac{|I_{ij}|}{G_{ij}} = V_{ij} \leq 1\frac{|I_{ij}|}{G_{ij}} = V_{ij} \leq 1
, the bracketed term is:
μ−α∣Iij∣Gij≤μ−α⋅0=μ.\mu - \alpha \frac{|I_{ij}|}{G_{ij}} \leq \mu - \alpha \cdot 0 = \mu.\mu - \alpha \frac{|I_{ij}|}{G_{ij}} \leq \mu - \alpha \cdot 0 = \mu.

If α≥μ\alpha \geq \mu\alpha \geq \mu
:
μ−α∣Iij∣Gij≤0,(8)\mu - \alpha \frac{|I_{ij}|}{G_{ij}} \leq 0, \tag{8}\mu - \alpha \frac{|I_{ij}|}{G_{ij}} \leq 0, \tag{8}

since Lij≥0L_{ij} \geq 0L_{ij} \geq 0
, Gij>0G_{ij} > 0G_{ij} > 0
:
dEdt≤0,(9)\frac{dE}{dt} \leq 0, \tag{9}\frac{dE}{dt} \leq 0, \tag{9}

with equality when:
α∣Iij∣=μGij,∀(i,j)∈T.(10)\alpha |I_{ij}| = \mu G_{ij}, \quad \forall (i,j) \in \mathcal{T}. \tag{10}\alpha |I_{ij}| = \mu G_{ij}, \quad \forall (i,j) \in \mathcal{T}. \tag{10}

6. 2-opt Cost Change
A 2-opt swap replacing edges ( (a,b) ) and ( (c,d) ) with ( (a,c) ) and ( (b,d) ) is accepted if:
ΔEswap=(Wa,cLa,c+Wb,dLb,d)−(Wa,bLa,b+Wc,dLc,d)<0.(11)\Delta E_{\text{swap}} = \left( W_{a,c} L_{a,c} + W_{b,d} L_{b,d} \right) - \left( W_{a,b} L_{a,b} + W_{c,d} L_{c,d} \right) < 0. \tag{11}\Delta E_{\text{swap}} = \left( W_{a,c} L_{a,c} + W_{b,d} L_{b,d} \right) - \left( W_{a,b} L_{a,b} + W_{c,d} L_{c,d} \right) < 0. \tag{11}

For VTSP, include smoothness:
\Delta E_{\text{VTSP}} = \Delta E_{\text{swap}} + \text{memory_weight} \cdot \Delta T + \text{entropy_weight} \cdot \Delta E,
where:
ΔT=t(pa,pc,pb)+t(pc,pb,pd)−t(pa,pb,pc)−t(pb,pc,pd)\Delta T = t(p_a, p_c, p_b) + t(p_c, p_b, p_d) - t(p_a, p_b, p_c) - t(p_b, p_c, p_d)\Delta T = t(p_a, p_c, p_b) + t(p_c, p_b, p_d) - t(p_a, p_b, p_c) - t(p_b, p_c, p_d)
.

ΔE=e(pa,pc,pb)+e(pc,pb,pd)−e(pa,pb,pc)−e(pb,pc,pd)\Delta E = e(p_a, p_c, p_b) + e(p_c, p_b, p_d) - e(p_a, p_b, p_c) - e(p_b, p_c, p_d)\Delta E = e(p_a, p_c, p_b) + e(p_c, p_b, p_d) - e(p_a, p_b, p_c) - e(p_b, p_c, p_d)
.
7. Steady-State Conductance
At equilibrium (G˙ij=0\dot{G}_{ij} = 0\dot{G}_{ij} = 0
):
Gij=αμ∣Iij∣,Wij=μα∣Iij∣.(12)G_{ij} = \frac{\alpha}{\mu} |I_{ij}|, \quad W_{ij} = \frac{\mu}{\alpha |I_{ij}|}. \tag{12}G_{ij} = \frac{\alpha}{\mu} |I_{ij}|, \quad W_{ij} = \frac{\mu}{\alpha |I_{ij}|}. \tag{12}

Relation to ARP in tsp_realignr_full.py and Hybrid Solver
The ARP implementation in tsp_realignr_full.py (and the hybrid solver) approximates the continuous flow (Eq. 1) with discrete updates:
Gij(t+1)=max⁡(Gij(t)+α∣Iij(t)∣−μGij(t),10−9),G_{ij}^{(t+1)} = \max\left( G_{ij}^{(t)} + \alpha |I_{ij}^{(t)}| - \mu G_{ij}^{(t)}, 10^{-9} \right),G_{ij}^{(t+1)} = \max\left( G_{ij}^{(t)} + \alpha |I_{ij}^{(t)}| - \mu G_{ij}^{(t)}, 10^{-9} \right),

where:
Iij(t)I_{ij}^{(t)}I_{ij}^{(t)}
: Current, with I0,n/2=1.0I_{0, n/2} = 1.0I_{0, n/2} = 1.0
 initially.

Wij=1GijW_{ij} = \frac{1}{G_{ij}}W_{ij} = \frac{1}{G_{ij}}
: Edge weights used in 2-opt.

In the hybrid solver, weights are augmented with curvature:
Wij=1Gij+λ⋅1κij,λ=0.1.W_{ij} = \frac{1}{G_{ij}} + \lambda \cdot \frac{1}{\kappa_{ij}}, \quad \lambda = 0.1.W_{ij} = \frac{1}{G_{ij}} + \lambda \cdot \frac{1}{\kappa_{ij}}, \quad \lambda = 0.1.
The proof assumes a fixed tour topology and a voltage source (1 V across two nodes), but the code uses a current injection, which may affect VijV_{ij}V_{ij}
 bounds. The Lyapunov decrease still holds if ∣Iij∣/Gij≤1|I_{ij}| / G_{ij} \leq 1|I_{ij}| / G_{ij} \leq 1
, which is reasonable for normalized currents.
For VTSP, the hybrid solver applies ARP after constructing a smoothness-aware tour, ensuring weights reflect both geometric efficiency and smoothness via curvature learning.
Gaps and Clarifications in the Proof Sketch
Current vs. Voltage Source:
The proof assumes a unit voltage source (0≤Vij≤10 \leq V_{ij} \leq 10 \leq V_{ij} \leq 1
), but the code injects a unit current (I0,n/2=1.0I_{0, n/2} = 1.0I_{0, n/2} = 1.0
). This discrepancy needs clarification. If currents are normalized, Eq. 5 holds, but ∣Iij∣≤Gij|I_{ij}| \leq G_{ij}|I_{ij}| \leq G_{ij}
 may require adjustment based on network properties.
Missing Differentiation Step:
The sketch states “Differentiate (2) using :”, but the chain rule is implied:
ddt(1Gij)=−G˙ijGij2.\frac{d}{dt} \left( \frac{1}{G_{ij}} \right) = -\frac{\dot{G}_{ij}}{G_{ij}^2}.\frac{d}{dt} \left( \frac{1}{G_{ij}} \right) = -\frac{\dot{G}_{ij}}{G_{ij}^2}.
This is standard but should be explicit.
LaSalle Invariance:
The sketch invokes LaSalle’s theorem without detailing the invariant set’s structure. The set {G:α∣Iij∣=μGij}\{ G : \alpha |I_{ij}| = \mu G_{ij} \}\{ G : \alpha |I_{ij}| = \mu G_{ij} \}
 implies a balance between current-driven growth and decay, but IijI_{ij}I_{ij}
 depends on the network, requiring a fixed-point analysis.
Smoothness for VTSP:
The proof focuses on ( E(G) ), ignoring smoothness. For VTSP, the hybrid solver’s extended functional EVTSPE_{\text{VTSP}}E_{\text{VTSP}}
 ensures smoothness via penalties, but ARP’s impact on T(π)T(\pi)T(\pi)
 and E(π)E(\pi)E(\pi)
 needs analysis.
Mathematical Formulation for ARP in VTSP
The ARP optimizes edge weights to minimize EVTSPE_{\text{VTSP}}E_{\text{VTSP}}
. The hybrid solver’s workflow is:
DBM Walk:
pj∝(s(pπk−1,pπk,pj)+ϕj)−η⋅exp⁡(−β(θj−θhead)2),p_j \propto \left( s(p_{\pi_{k-1}}, p_{\pi_k}, p_j) + \phi_j \right)^{-\eta} \cdot \exp\left( -\beta (\theta_j - \theta_{\text{head}})^2 \right),p_j \propto \left( s(p_{\pi_{k-1}}, p_{\pi_k}, p_j) + \phi_j \right)^{-\eta} \cdot \exp\left( -\beta (\theta_j - \theta_{\text{head}})^2 \right),
where ( s ) is the smoothness cost (Eq. 2 from previous response).

2-opt with ARP Weights:
Accept swap if ΔEVTSP<0,\text{Accept swap if } \Delta E_{\text{VTSP}} < 0,\text{Accept swap if } \Delta E_{\text{VTSP}} < 0,
using Wij=1Gij+0.1⋅1κijW_{ij} = \frac{1}{G_{ij}} + 0.1 \cdot \frac{1}{\kappa_{ij}}W_{ij} = \frac{1}{G_{ij}} + 0.1 \cdot \frac{1}{\kappa_{ij}}
.

ARP Update:
Gij(t+1)=max⁡(Gij(t)+α∣Iij(t)∣−μGij(t),10−9).G_{ij}^{(t+1)} = \max\left( G_{ij}^{(t)} + \alpha |I_{ij}^{(t)}| - \mu G_{ij}^{(t)}, 10^{-9} \right).G_{ij}^{(t+1)} = \max\left( G_{ij}^{(t)} + \alpha |I_{ij}^{(t)}| - \mu G_{ij}^{(t)}, 10^{-9} \right).

Curvature Update:
κπi,πi+1(t+1)=κπi,πi+1(t)+δ(Lmax−L(π))2−L(π)Lmax,\kappa_{\pi_i, \pi_{i+1}}^{(t+1)} = \kappa_{\pi_i, \pi_{i+1}}^{(t)} + \delta \left( L_{\text{max}} - L(\pi) \right)^{2 - \frac{L(\pi)}{L_{\text{max}}}},\kappa_{\pi_i, \pi_{i+1}}^{(t+1)} = \kappa_{\pi_i, \pi_{i+1}}^{(t)} + \delta \left( L_{\text{max}} - L(\pi) \right)^{2 - \frac{L(\pi)}{L_{\text{max}}}},
κu,v(t+1)=max⁡(κu,v(t)−ϵ,0.1).\kappa_{u,v}^{(t+1)} = \max( \kappa_{u,v}^{(t)} - \epsilon, 0.1 ).\kappa_{u,v}^{(t+1)} = \max( \kappa_{u,v}^{(t)} - \epsilon, 0.1 ).

Laplacian Smoothing:
xi(t+1)=xi(t)+β0(17∑j∈Ni,j≠ixj−xi).x_i^{(t+1)} = x_i^{(t)} + \beta_0 \left( \frac{1}{7} \sum_{j \in N_i, j \neq i} x_j - x_i \right).x_i^{(t+1)} = x_i^{(t)} + \beta_0 \left( \frac{1}{7} \sum_{j \in N_i, j \neq i} x_j - x_i \right).

Smoothness Metric:
A(π)=∑i=1n−1arccos⁡((pπi+1−pπi)⋅(pπi+2−pπi+1)∥pπi+1−pπi∥2⋅∥pπi+2−pπi+1∥2+10−8).A(\pi) = \sum_{i=1}^{n-1} \arccos\left( \frac{(p_{\pi_{i+1}} - p_{\pi_i}) \cdot (p_{\pi_{i+2}} - p_{\pi_{i+1}})}{\| p_{\pi_{i+1}} - p_{\pi_i} \|_2 \cdot \| p_{\pi_{i+2}} - p_{\pi_{i+1}} \|_2 + 10^{-8}} \right).A(\pi) = \sum_{i=1}^{n-1} \arccos\left( \frac{(p_{\pi_{i+1}} - p_{\pi_i}) \cdot (p_{\pi_{i+2}} - p_{\pi_{i+1}})}{\| p_{\pi_{i+1}} - p_{\pi_i} \|_2 \cdot \| p_{\pi_{i+2}} - p_{\pi_{i+1}} \|_2 + 10^{-8}} \right).
Next Steps
Clarify Intent: If you meant deriving new equations (e.g., extending the proof to include smoothness), modifying the proof, or focusing on another component, please specify.

Test Equations: I can provide code to test ARP’s impact on EVTSPE_{\text{VTSP}}E_{\text{VTSP}}
 and A(π)A(\pi)A(\pi)
 using the hybrid solver.

Visualization: Request a plot showing ARP’s effect on tour smoothness (e.g., turn angles) with a point set.

VRP or Other Needs: If VRP features are relevant, I can extend the equations for clustering and multi-vehicle tours.
The equations above 
