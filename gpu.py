# Full Multi-GPU ER Fluid Simulation with Optimized Visualization

# Required installation command:
# pip install torch torchvision torchaudio networkx matplotlib numpy

import torch
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import os

# Optimize GPU memory management
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
torch.cuda.empty_cache()

# Check GPU availability
device_count = torch.cuda.device_count()
if device_count < 2:
    raise RuntimeError("Two GPUs required for this simulation.")

devices = [torch.device(f'cuda:{i}') for i in range(device_count)]

# Adjust nodes according to GPU capability
num_nodes = 11500
positions = torch.rand((num_nodes, 2), device=devices[0]) * 100
positions_chunks = positions.chunk(device_count)

resistance_chunks = []
for i, pos_chunk in enumerate(positions_chunks):
    pos_chunk = pos_chunk.to(devices[i])
    coords_diff = pos_chunk.unsqueeze(1) - positions.to(devices[i]).unsqueeze(0)
    dists = torch.norm(coords_diff, dim=2)
    resistance_chunks.append(dists.to(devices[0]))

resistance = torch.cat(resistance_chunks, dim=0)
resistance[range(num_nodes), range(num_nodes)] = float('inf')

# ER fluid simulation
def simulate_dynamic_er_fluid(resistance, voltage, iterations=50, alpha=0.001):
    num_nodes = resistance.shape[0]
    for iteration in range(iterations):
        conductance = 1.0 / resistance
        conductance[range(num_nodes), range(num_nodes)] = 0

        G_matrix = -conductance
        G_matrix[range(num_nodes), range(num_nodes)] = conductance.sum(dim=1)

        I_vector = torch.zeros(num_nodes, device=devices[0])
        I_vector[0] = voltage
        I_vector[-1] = -voltage

        try:
            voltages = torch.linalg.solve(G_matrix, I_vector)
        except RuntimeError as e:
            print(f"Linear algebra error at iteration {iteration}: {e}")
            break

        volt_diff = voltages.unsqueeze(0) - voltages.unsqueeze(1)
        current = torch.abs(volt_diff) / resistance

        resistance *= (1 - alpha * current)
        resistance = resistance.clamp(min=0.01, max=1000)

simulate_dynamic_er_fluid(resistance, voltage=5, iterations=50, alpha=0.001)

# Move to CPU for MST
resistance_cpu = resistance.cpu().numpy()
G_nx = nx.from_numpy_array(resistance_cpu)
mst = nx.minimum_spanning_tree(G_nx, weight='weight')

# Optimized visualization
positions_cpu = positions.cpu().numpy()
mst_edges = np.array(list(mst.edges()))
mst_positions = positions_cpu[mst_edges]

plt.figure(figsize=(12, 10))

# Plot MST efficiently
for edge in mst_positions:
    plt.plot(edge[:, 0], edge[:, 1], 'g-', linewidth=0.5, alpha=0.7)

# Plot nodes quickly
plt.scatter(positions_cpu[:, 0], positions_cpu[:, 1], s=2, c='skyblue', alpha=0.6)

plt.title("Optimized ER Fluid Analog Computation Visualization")
plt.xlabel("X Coordinate")
plt.ylabel("Y Coordinate")
plt.grid(False)

# Save and show
plt.savefig("optimized_er_fluid_solution.png", dpi=300)
print("Visualization saved as optimized_er_fluid_solution.png")
plt.show()
