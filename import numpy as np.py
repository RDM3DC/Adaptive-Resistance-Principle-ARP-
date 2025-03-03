import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

# Generate a large number of cities randomly
num_nodes = 500  # Adjust this number based on your computer's capabilities
positions = {i: (np.random.uniform(0, 100), np.random.uniform(0, 100)) for i in range(num_nodes)}
city_labels = {i: str(i) for i in range(num_nodes)}

# Create complete graph
G = nx.complete_graph(num_nodes)

# Assign initial resistance based on Euclidean distance
for i, j in G.edges():
    dist = np.linalg.norm(np.array(positions[i]) - np.array(positions[j]))
    G[i][j]['resistance'] = dist

# Dynamic ER fluid simulation function with proper Kirchhoff's laws
def simulate_dynamic_er_fluid(G, voltage, iterations=50, alpha=0.001):
    for iteration in range(iterations):
        # Construct conductance matrix
        G_matrix = np.zeros((num_nodes, num_nodes))
        I_vector = np.zeros(num_nodes)

        # Inject current at first node, extract from last node
        I_vector[0] = voltage
        I_vector[-1] = -voltage

        # Populate conductance matrix
        for i in range(num_nodes):
            for j in range(num_nodes):
                if i != j and G.has_edge(i, j):
                    conductance = 1 / G[i][j]['resistance']
                    G_matrix[i, j] -= conductance
                    G_matrix[i, i] += conductance

        # Solve voltages using Kirchhoff's laws
        try:
            voltages = np.linalg.solve(G_matrix, I_vector)
        except np.linalg.LinAlgError as e:
            print(f"Linear algebra error at iteration {iteration}: {e}")
            break

        # Update resistances based on currents
        for i, j in G.edges():
            current = abs(voltages[i] - voltages[j]) / G[i][j]['resistance']
            G[i][j]['resistance'] *= (1 - alpha * current)
            G[i][j]['resistance'] = np.clip(G[i][j]['resistance'], 0.01, 1000)

# Run the simulation explicitly
simulate_dynamic_er_fluid(G, voltage=5, iterations=50, alpha=0.001)

# Find approximate optimal path based on minimum resistance
mst = nx.minimum_spanning_tree(G, weight='resistance')

# Visualization with improved labeling (optional for large graphs)
plt.figure(figsize=(12, 10))
nx.draw(G, positions, labels=city_labels, node_size=50, node_color='skyblue', font_size=6, font_weight='bold')
nx.draw_networkx_edges(mst, positions, edge_color='green', width=1, style='solid', label="Optimal Path")

plt.title("Large-Scale ER Fluid Analog Computation Simulator")
plt.legend()
plt.show()
