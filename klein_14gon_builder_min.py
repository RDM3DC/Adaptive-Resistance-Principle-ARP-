# klein_14gon_builder_min.py  (stdlib-only)
# Builds a numeric 14-gon fundamental domain in the Poincaré disk and a simple fan triangulation.
# Outputs:
#   - klein_14gon_vertices.csv  (x,y,z; z=0)
#   - klein_14gon_faces.csv     (i,j,k; 0-based triangle indices)

import math, csv

# 1) Numeric radius per hyperbolic regular 14-gon (your symbolic formula evaluated with math)
rho = math.tanh(math.acosh(math.cos(math.pi/7.0) / math.sin(math.pi/14.0)))  # ~0.969

# 2) 14 vertices on the unit circle scaled by rho, centered at the origin, plus a center vertex
verts = []
for k in range(14):
    angle = 2.0*math.pi*k/14.0
    x = rho*math.cos(angle)
    y = rho*math.sin(angle)
    verts.append((x,y,0.0))
CENTER = len(verts)
verts.append((0.0,0.0,0.0))  # index 14

# 3) Fan triangulation: (CENTER, i, i+1)
faces = []
for i in range(14):
    faces.append((CENTER, i, (i+1)%14))

# 4) Write CSVs
with open("klein_14gon_vertices.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["x","y","z"]); w.writerows(verts)
with open("klein_14gon_faces.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["i","j","k"]); w.writerows(faces)

print("Wrote klein_14gon_vertices.csv and klein_14gon_faces.csv")
