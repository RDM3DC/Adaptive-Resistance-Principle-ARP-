# gb_check_adaptive_min.py  (stdlib-only)
# Sums K*A from two CSVs (face_areas.csv with header 'area', K_face.csv with header 'K_face').
# Usage: python gb_check_adaptive_min.py face_areas.csv K_face.csv

import csv, sys, math

areas_csv = sys.argv[1]
K_csv     = sys.argv[2]

A = []
with open(areas_csv, newline="") as f:
    r = csv.reader(f); header = next(r, None)
    for row in r:
        A.append(float(row[0]))

K = []
with open(K_csv, newline="") as f:
    r = csv.reader(f); header = next(r, None)
    for row in r:
        K.append(float(row[0]))

if len(A) != len(K):
    raise SystemExit(f"Length mismatch: areas={len(A)} vs K={len(K)}")

S = sum(k*a for k,a in zip(K,A))
print(f"∑ K_f A_f = {S:.6f}   target = {-8.0*math.pi:.6f}   diff = {S + 8.0*math.pi:.3e}")
