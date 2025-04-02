import numpy as np import math import matplotlib.pyplot as plt import pandas as pd from scipy.spatial.distance import pdist, squareform from scipy.sparse import lil_matrix, csr_matrix from scipy.sparse.linalg import cg

---------------------------- Helper Functions ----------------------------

def generate_points(num_cities=100, seed=42): np.random.seed(seed) return np.random.rand(num_cities, 2) * 100

def build_knn_graph(coords, k=10): n = len(coords) dist_mat = squareform(pdist(coords)) edges = set() for i in range(n): nearest = np.argsort(dist_mat[i])[1:k+1] for j in nearest: a, b = min(i,j), max(i,j) edges.add((a,b)) return list(edges), dist_mat

def build_sparse_laplacian(n, edges, G): M = lil_matrix((n, n), dtype=np.float64) row_sums = np.zeros(n) for (i, j) in edges: gij = G.get((i, j), 0.0) row_sums[i] += gij row_sums[j] += gij for i in range(n): M[i, i] = row_sums[i] for (i, j) in edges: gij = G.get((i, j), 0.0) M[i, j] = -gij M[j, i] = -gij return csr_matrix(M)

def solve_voltages_sparse(M, source, sink, Iin, Iout): n = M.shape[0] b = np.zeros(n) b[source] = Iin b[sink] = -Iout anchor = n-1 if n-1 not in (source, sink) else n-2 keep = [i for i in range(n) if i != anchor] M_sub = M[keep][:, keep] b_sub = b[keep] V_sub, _ = cg(M_sub, b_sub, maxiter=1000, tol=1e-8) V = np.zeros(n) for idx, node in enumerate(keep): V[node] = V_sub[idx] return V

def nearest_neighbor_tsp(dist_matrix): n = dist_matrix.shape[0] unvisited = set(range(n)) current = 0 tour = [current] unvisited.remove(current) while unvisited: next_city = min(unvisited, key=lambda city: dist_matrix[current, city]) tour.append(next_city) unvisited.remove(next_city) current = next_city tour.append(tour[0]) return tour

def extract_route_from_G(G_dict, n, dist_mat, start=0): visited = set([start]) route = [start] current = start while len(visited) < n: nbrs = [j for (i, j) in G_dict if i == current and j not in visited] nbrs += [i for (i, j) in G_dict if j == current and i not in visited] if not nbrs: # patch: find nearest unvisited unvisited = list(set(range(n)) - visited) next_city = min(unvisited, key=lambda x: dist_mat[current][x]) else: next_city = max(nbrs, key=lambda x: G_dict.get((min(current,x), max(current,x)), 0)) route.append(next_city) visited.add(next_city) current = next_city route.append(start)  # close the loop return route

def compute_route_length(route, dist_mat): return sum(dist_mat[route[i], route[i+1]] for i in range(len(route)-1))

def plot_route(coords, route, seed_order): xs, ys = coords[:,0], coords[:,1] plt.figure(figsize=(10, 10))

# Full route
for i in range(len(route)-1):
    a, b = route[i], route[i+1]
    plt.plot([xs[a], xs[b]], [ys[a], ys[b]], 'r-', linewidth=1.5)

# Seed overlay (from first 20 cities)
for i in range(len(seed_order)-1):
    a, b = seed_order[i], seed_order[i+1]
    plt.plot([xs[a], xs[b]], [ys[a], ys[b]], 'g--', linewidth=2)

plt.plot(xs[route[0]], ys[route[0]], 'bo', label='Start')
plt.plot(xs[route[-2]], ys[route[-2]], 'yo', label='End')
plt.title("AIN + Seed TSP Route")
plt.legend()
plt.axis('equal')
plt.grid(True)
plt.show()

---------------------- Run Hybrid AIN + TSP ----------------------

num_cities = 100 coords = generate_points(num_cities) edges, dist_mat = build_knn_graph(coords, k=10)

Initialize G

G_dict = {(i, j): 1e-3 for (i, j) in edges}

Seed TSP tour on first 20 cities

seed_dist = dist_mat[:20, :20] seed_order = nearest_neighbor_tsp(seed_dist) for i in range(len(seed_order)-1): a, b = seed_order[i], seed_order[i+1] key = (min(a,b), max(a,b)) if key in G_dict: G_dict[key] = 0.2

AIN evolution

alpha, mu_ratio = 0.01, 1.9184 mu = alpha / mu_ratio I_0 = 191.84 / 5 source, sink = 0, num_cities - 1 for it in range(200): I_ext = I_0 if it < 5 else 1.0 M = build_sparse_laplacian(num_cities, edges, G_dict) V = solve_voltages_sparse(M, source, sink, I_ext, I_ext) for (i, j) in edges: gij = G_dict[(i, j)] dv = V[i] - V[j] I_ij = abs(dv) * gij G_dict[(i, j)] = max(0.0, gij + (alpha * I_ij - mu * gij))

Extract and patch final route

route = extract_route_from_G(G_dict, num_cities, dist_mat) route_len = compute_route_length(route, dist_mat)

Plot

plot_route(coords, route, seed_order)

Export CSV

df = pd.DataFrame([coords[i] for i in route], columns=['x', 'y']) df['city_index'] = route df['step'] = list(range(len(route))) df.to_csv("ain_100_city_route.csv", index=False)  # Save locally

