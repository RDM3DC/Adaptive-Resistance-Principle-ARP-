Curve Memory in 3D (CMA-3D)
Overview

Curve Memory (CMA) is a compact, rigid-motion-invariant representation of curves.
In 2D, a curve is uniquely determined (up to rigid motion) by its arclength parameterization and curvature:

𝜅
(
𝑠
)
=
∥
𝑑
𝑇
𝑑
𝑠
∥
κ(s)=
	​

ds
dT
	​

	​


where 
𝑇
(
𝑠
)
T(s) is the unit tangent vector at arclength 
𝑠
s.

For 3D space curves, we extend this to CMA-3D by including torsion. Any sufficiently smooth space curve 
𝑟
(
𝑠
)
r(s) is fully determined (up to rigid motion) by:

Curvature 
𝜅
(
𝑠
)
κ(s)

Torsion 
𝜏
(
𝑠
)
τ(s)

These are related by the Frenet–Serret equations:

𝑑
𝑇
𝑑
𝑠
	
=
𝜅
(
𝑠
)
 
𝑁
(
𝑠
)




𝑑
𝑁
𝑑
𝑠
	
=
−
𝜅
(
𝑠
)
 
𝑇
(
𝑠
)
+
𝜏
(
𝑠
)
 
𝐵
(
𝑠
)




𝑑
𝐵
𝑑
𝑠
	
=
−
𝜏
(
𝑠
)
 
𝑁
(
𝑠
)
ds
dT
	​

ds
dN
	​

ds
dB
	​

	​

=κ(s)N(s)
=−κ(s)T(s)+τ(s)B(s)
=−τ(s)N(s)
	​


where:

𝑇
(
𝑠
)
T(s) = unit tangent

𝑁
(
𝑠
)
N(s) = unit normal

𝐵
(
𝑠
)
=
𝑇
(
𝑠
)
×
𝑁
(
𝑠
)
B(s)=T(s)×N(s) = unit binormal

Thus the CMA-3D representation of a curve is the tuple:

𝑀
=
(
𝐿
,
  
𝑢
,
  
𝜅
(
𝑢
)
,
  
𝜏
(
𝑢
)
)
M=(L,u,κ(u),τ(u))

where:

𝐿
L = total curve length

𝑢
=
𝑠
/
𝐿
∈
[
0
,
1
]
u=s/L∈[0,1] = normalized arclength

𝜅
(
𝑢
)
κ(u) = curvature function over normalized arclength

𝜏
(
𝑢
)
τ(u) = torsion function over normalized arclength

This representation is:

Rigid-motion invariant (independent of translation/rotation)

Scale aware (through 
𝐿
L)

Lossless in principle (the curve can be reconstructed from it)

Discrete Formulation

For a discrete polyline 
{
𝑝
𝑖
}
𝑖
=
0
𝑁
{p
i
	​

}
i=0
N
	​

:

Segment lengths and arclengths

ℓ
𝑖
=
∥
𝑝
𝑖
+
1
−
𝑝
𝑖
∥
,
𝑠
𝑗
=
∑
𝑖
=
0
𝑗
−
1
ℓ
𝑖
,
𝐿
=
𝑠
𝑁
ℓ
i
	​

=∥p
i+1
	​

−p
i
	​

∥,s
j
	​

=
i=0
∑
j−1
	​

ℓ
i
	​

,L=s
N
	​


Tangents

𝑡
𝑖
=
𝑝
𝑖
+
1
−
𝑝
𝑖
ℓ
𝑖
t
i
	​

=
ℓ
i
	​

p
i+1
	​

−p
i
	​

	​


Discrete curvature at vertex 
𝑖
i:

𝜅
𝑖
≈
∥
𝑡
𝑖
−
𝑡
𝑖
−
1
∥
1
2
(
ℓ
𝑖
−
1
+
ℓ
𝑖
)
κ
i
	​

≈
2
1
	​

(ℓ
i−1
	​

+ℓ
i
	​

)
∥t
i
	​

−t
i−1
	​

∥
	​


Discrete torsion at vertex 
𝑖
i:
Define binormals:

𝑏
𝑖
=
𝑡
𝑖
×
𝑡
𝑖
−
1
∥
𝑡
𝑖
×
𝑡
𝑖
−
1
∥
b
i
	​

=
∥t
i
	​

×t
i−1
	​

∥
t
i
	​

×t
i−1
	​

	​


Then torsion is the signed angle change of binormals per arclength:

𝜏
𝑖
≈
sign
⁡
(
(
𝑏
𝑖
−
1
×
𝑏
𝑖
)
⋅
𝑡
𝑖
)
  
∠
(
𝑏
𝑖
−
1
,
𝑏
𝑖
)
1
2
(
ℓ
𝑖
−
1
+
ℓ
𝑖
)
τ
i
	​

≈
2
1
	​

(ℓ
i−1
	​

+ℓ
i
	​

)
sign((b
i−1
	​

×b
i
	​

)⋅t
i
	​

)∠(b
i−1
	​

,b
i
	​

)
	​

Reconstruction from Memory

Given 
(
𝜅
(
𝑠
)
,
𝜏
(
𝑠
)
)
(κ(s),τ(s)), one can reconstruct the curve up to a rigid motion by integrating Frenet–Serret:

Initialize point 
𝑟
(
0
)
r(0) and frame 
(
𝑇
,
𝑁
,
𝐵
)
(T,N,B).

March forward with step size 
Δ
𝑠
Δs:

Rotate 
𝑇
,
𝑁
T,N in the 
𝑇
T–
𝑁
N plane by angle 
𝜅
Δ
𝑠
κΔs.

Twist 
𝑁
,
𝐵
N,B around 
𝑇
T by angle 
𝜏
Δ
𝑠
τΔs.

Advance:

𝑟
(
𝑠
+
Δ
𝑠
)
=
𝑟
(
𝑠
)
+
𝑇
(
𝑠
)
 
Δ
𝑠
r(s+Δs)=r(s)+T(s)Δs

Repeat until 
𝑠
=
𝐿
s=L.

This reconstructs a canonical representative of the curve defined by the memory.

Global Quantities

From the stored memory we can compute invariants:

Total curvature:

∫
0
𝐿
𝜅
(
𝑠
)
 
𝑑
𝑠
∫
0
L
	​

κ(s)ds

Total torsion:

∫
0
𝐿
∣
𝜏
(
𝑠
)
∣
 
𝑑
𝑠
∫
0
L
	​

∣τ(s)∣ds

Writhe/Twist approximations for closed curves.

Multi-Scale Curve Memory

Instead of storing full 
𝜅
(
𝑢
)
,
𝜏
(
𝑢
)
κ(u),τ(u), CMA-3D supports multi-scale downsampling:

Build pyramids of 
𝜅
,
𝜏
κ,τ at reduced resolution.

Store statistics (mean, std, min, max).

Allows variable level of detail (LOD):

Low resolution for search/indexing.

High resolution for reconstruction.

Benefits

Compression: reduce curve data size by 10–60× with <0.5% RMS error on smooth curves.

Comparison: invariant signatures make it easy to compare curves regardless of pose.

Reconstruction: regenerate curves at arbitrary sampling density.

Integration: directly usable in CAD pipelines (tube sweeps, ribbons, lofts).

Learning: curvature/torsion sequences can be fed into ML models.

Example (Helix)

For a helix:

𝑟
(
𝑡
)
=
(
cos
⁡
𝑡
,
  
sin
⁡
𝑡
,
  
𝑐
𝑡
)
r(t)=(cost,sint,ct)

The invariants are constant:

𝜅
=
1
1
+
𝑐
2
,
𝜏
=
𝑐
1
+
𝑐
2
κ=
1+c
2
1
	​

,τ=
1+c
2
c
	​


So the CMA-3D memory of a helix is simply the pair of constants 
(
𝜅
,
𝜏
)
(κ,τ) repeated along arclength.

Summary

CMA-3D = Curve Memory in 3D is the representation:

𝑀
=
(
𝐿
,
  
𝑢
,
  
𝜅
(
𝑢
)
,
  
𝜏
(
𝑢
)
)
M=(L,u,κ(u),τ(u))

It is:

Compact

Rigid-motion invariant

Reconstructable

Extendable to multi-scale analysis

This forms the basis for efficient curve storage, comparison, and regeneration in AdaptiveCAD and related frameworks.
