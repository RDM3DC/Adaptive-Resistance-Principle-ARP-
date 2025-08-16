# euler_check_min.py  (stdlib-only)
# Reads vertices.csv and faces.csv, computes V/E/F and Euler characteristic χ.

import csv, sys

verts_path = sys.argv[1] if len(sys.argv) > 1 else "klein_14gon_vertices.csv"
faces_path = sys.argv[2] if len(sys.argv) > 2 else "klein_14gon_faces.csv"

# V
with open(verts_path, newline="") as f:
    r = csv.reader(f)
    header = next(r, None)
    Vn = sum(1 for _ in r)

# F and E
Eset = set()
Fn = 0
with open(faces_path, newline="") as f:
    r = csv.reader(f)
    header = next(r, None)
    for row in r:
        a,b,c = map(int, row)
        Fn += 1
        e1 = tuple(sorted((a,b)))
        e2 = tuple(sorted((b,c)))
        e3 = tuple(sorted((c,a)))
        Eset.update((e1,e2,e3))

En = len(Eset)
chi = Vn - En + Fn
print(f"V={Vn} E={En} F={Fn}  χ={chi}")
