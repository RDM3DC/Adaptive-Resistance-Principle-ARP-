# gb_check_constantK_min.py  (stdlib-only)
# Constant-curvature Gauss–Bonnet check for {3,7} on the Klein quartic.
# For {3,7}, each triangle has angles 2π/7, so area = (π - 3*(2π/7))/κ^2 = π/(7 κ^2).
# With F=56, total area = 8π/κ^2, so -∫K dA = κ^2 * 8π/κ^2 = 8π = -2πχ (χ=-4).

import math, sys

kappa = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
F = 56
A_face = math.pi/(7.0*kappa*kappa)
A_total = F*A_face
lhs = kappa*kappa*A_total
rhs = 8.0*math.pi
print(f"kappa={kappa}  A_face={A_face:.6f}  A_total={A_total:.6f}  -∫K dA={lhs:.6f}  target={rhs:.6f}  diff={lhs-rhs:.3e}")
