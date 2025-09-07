# Wedge-Product Compressibility Proofs (Curve Alphabet Encoder)

## Setup
Let $V$ be the real vector space spanned by letter-curves $\{e_i\}_{i=1}^n$, viewed as $1$-vectors.
Let $\Lambda^\bullet V$ be the exterior algebra with the usual wedge $\wedge$.
Define the *projected wedge* (our system's product) by
\[
a \star b := \Pi_2(a \wedge b),
\]
where $\Pi_2:\Lambda^\bullet V \to \Lambda^2 V$ is the grade-2 projection.
All letter interactions are evaluated using $\star$.

## Lemma 1 (Grade-2 Closure)
For any $u,v\in \Lambda^1 V$ (letters), $u\star v \in \Lambda^2 V$.

**Proof.**  
Since $u,v\in \Lambda^1 V$, we have $u\wedge v \in \Lambda^2 V$ in the standard exterior algebra.  
Thus $\Pi_2(u\wedge v)=u\wedge v \in \Lambda^2 V$, hence $u\star v\in\Lambda^2 V$. ∎

## Lemma 2 (Antisymmetry)
For $u,v\in \Lambda^1 V$, $u\star v = -\,v\star u$.

**Proof.**  
Exterior antisymmetry gives $u\wedge v = -\,v\wedge u$. Applying $\Pi_2$ preserves sign:  
$u\star v=\Pi_2(u\wedge v) = -\,\Pi_2(v\wedge u)= -\,v\star u$. ∎

## Lemma 3 (Associativity under Grade-2 Projection)
For $u,v,w\in \Lambda^1 V$,
\[
\Pi_2\big((u\star v)\star w\big) = \Pi_2\big(u\star (v\star w)\big).
\]
Equivalently, $\star$ is associative *in the projected sense*:
\[
(u\star v)\star w \overset{\Pi_2}{=} u\star (v\star w).
\]

**Proof (sketch).**  
Compute in $\Lambda^\bullet V$ then project:
\[
(u\star v)\star w
= \Pi_2\big(\Pi_2(u\wedge v)\wedge w\big)
= \Pi_2\big((u\wedge v)\wedge w\big),
\]
because $(u\wedge v)\in\Lambda^2 V$ and wedging with $w\in\Lambda^1 V$ gives an element of $\Lambda^3 V$, on which $\Pi_2$ returns $0$.
Similarly,
\[
u\star (v\star w)
= \Pi_2\big(u\wedge \Pi_2(v\wedge w)\big)
= \Pi_2\big(u\wedge (v\wedge w)\big).
\]
By associativity of $\wedge$, $(u\wedge v)\wedge w = u\wedge(v\wedge w)\in\Lambda^3 V$, so both sides project to the same $\Pi_2$-value (namely $0$).
Thus associativity holds in the projected sense. ∎

## Proposition (Zero Grade-Entropy)
All interaction outputs lie in a single grade: $\operatorname{Im}(\star)\subseteq \Lambda^2 V$.
Hence the grade-distribution entropy is $H=0$.

**Proof.**  
By Lemma 1, for any letters $u,v$ we have $u\star v\in\Lambda^2 V$.  
Higher nests such as $(u\star v)\star w$ evaluate (before projection) to $\Lambda^3 V$ and then project to grade $2$ as $0$ (no drift to other grades).  
Thus no outputs occupy grades $0,1,3,\dots$; only grade $2$ is populated, yielding a degenerate (single-bin) distribution and $H=0$. ∎

## Corollary (Structural Compressibility)
Let $X=\{e_1,\dots,e_n\}$ be the alphabet (letters as $1$-vectors). Then all pairwise interactions are fully specified by an antisymmetric coefficient matrix
\[
B \in \mathbb{R}^{n\times n},\qquad
e_i \star e_j = B_{ij}(e_i\wedge e_j),\quad B_{ij}=-B_{ji}.
\]
Thus the number of independent parameters is $\tfrac{n(n-1)}{2}$ (upper-triangular part), and no higher-order ($\ge 3$) interaction tensors are required.

**Proof.**  
By Lemma 2, antisymmetry forces $B_{ij}=-B_{ji}$ and $B_{ii}=0$.  
All semantics reside in $\Lambda^2 V$, so there is no need to store $\Lambda^0,\Lambda^1,\Lambda^{\ge 3}$ components or mixed-grade couplings.  
Hence the representation reduces to the upper-triangular entries of $B$ only. ∎

## Compression Metrics (Immediate Consequences)
- **Bit budget for grade index:** $\log_2(1)=0$ bits (single-grade outcome).
- **Asymptotic storage:** $O(n^2)$ instead of $O(n^3)$ or higher (no tri-/multi-vector tensors).
- **Redundancy halving:** Antisymmetry halves pair storage (store $i<j$ only).
- **No combinatorial blowup:** $\star$-associativity under projection prevents growth into higher grades.

## Conclusion
Because the system’s product $\star$ (grade-2 projection of $\wedge$) enforces:  
(i) grade-2 closure,  
(ii) antisymmetry, and  
(iii) associativity in the projected sense,  
all contextual interactions live in a single, low-dimensional space $\Lambda^2 V$.  
This yields zero grade-entropy and a compact antisymmetric parameterization, guaranteeing strong compressibility without loss of intended pairwise semantics.
