import networkx as nx
import matplotlib.pyplot as plt
import random
import numpy as np

# 1. Define the Octagon and Initial Distances
def create_octagon_graph():
    """
    Creates a regular octagon graph representing the TSP cities.
    Initializes edge distances based on the octagon geometry.

    Returns:
        nx.Graph: A NetworkX graph representing the octagon.
    """
    # Create an empty graph
    graph = nx.Graph()

    # Add nodes representing the 8 cities of the octagon
    for i in range(8):
        graph.add_node(i)

    # Add edges connecting the nodes in a cycle (representing the octagon shape)
    for i in range(8):
        graph.add_edge(i, (i + 1) % 8)

    # Calculate the coordinates of the nodes assuming a unit circle (for simplicity)
    # This helps in visualizing the octagon
    node_positions = {i: (np.cos(i * 2 * np.pi / 8), np.sin(i * 2 * np.pi / 8)) for i in range(8)}

    # Store the positions in the graph
    nx.set_node_attributes(graph, node_positions, 'position')

    # Initialize edge distances.  For simplicity, assume all edges of the octagon have length 1.
    #  and other edges (diagonal) have a distance that is the Euclidean distance
    for u, v in graph.edges():
        pos_u = node_positions[u]
        pos_v = node_positions[v]
        dist = np.sqrt((pos_u[0] - pos_v[0])**2 + (pos_u[1] - pos_v[1])**2)
        graph.edges[u, v]['distance'] = dist

    return graph

# 2. Path Generation and Length Calculation
def generate_random_path(graph):
    """
    Generates a random valid path (tour) that visits all cities exactly once
    and returns to the starting city.

    Args:
        graph (nx.Graph): The graph representing the cities.

    Returns:
        list: A list of city indices representing the path.
    """
    nodes = list(graph.nodes())
    start_node = random.choice(nodes)
    remaining_nodes = nodes[:]
    remaining_nodes.remove(start_node)
    path = [start_node]

    while remaining_nodes:
        next_node = random.choice(remaining_nodes)
        path.append(next_node)
        remaining_nodes.remove(next_node)
    path.append(start_node)  # Return to the starting city
    return path

def calculate_path_length(graph, path):
    """
    Calculates the total length (cost) of a given path.

    Args:
        graph (nx.Graph): The graph representing the cities and distances.
        path (list): A list of city indices representing the path.

    Returns:
        float: The total length of the path.
    """
    length = 0
    node_positions = nx.get_node_attributes(graph, 'position') # Get node positions
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i+1]
        if graph.has_edge(u, v):
            length += graph.edges[u, v]['distance']
        else:
            # Calculate Euclidean distance if edge doesn't exist
            pos_u = node_positions[u]
            pos_v = node_positions[v]
            dist = np.sqrt((pos_u[0] - pos_v[0])**2 + (pos_u[1] - pos_v[1])**2)
            length += dist
    return length

# 3. Curvature Initialization and Update
def initialize_curvature(graph):
    """
    Initializes the curvature of all edges in the graph to a default value (e.g., 1).

    Args:
        graph (nx.Graph): The graph representing the cities and connections.
    """
    for u, v in graph.edges():
        graph.edges[u, v]['curvature'] = 1.0  # Initial curvature

def update_curvature(graph, path, path_length, max_path_length, delta=0.2): # Increased delta
    """
    Updates the curvature of the edges based on the given path length.
    Edges in shorter paths have their curvature increased, and vice-versa.
    Uses a non-linear update rule.

    Args:
        graph (nx.Graph): The graph representing the cities and connections.
        path (list): The path that was taken
        path_length (float): The length of the path.
        max_path_length (float):  A scaling factor.
        delta (float): The learning rate (how much to adjust curvature).
    """
    for i in range(len(path) - 1):
        u = path[i]
        v = path[i+1]
        # Update curvature: shorter path = higher curvature, non-linear
        if graph.has_edge(u, v): #check if edge exists before updating.
            #  The closer path_length is to 0, the larger the exponent.
            exponent = 2.0 - (path_length / max_path_length)
            graph.edges[u, v]['curvature'] += delta * (max_path_length - path_length) ** exponent

def decay_curvature(graph, epsilon=0.01):
    """
    (Optional) Applies a small decay to all edge curvatures to simulate forgetting of less
    used paths.

    Args:
        graph (nx.Graph): The graph.
        epsilon (float): The decay rate.
    """
    for u, v in graph.edges():
        graph.edges[u, v]['curvature'] -= epsilon
        graph.edges[u, v]['curvature'] = max(0.1, graph.edges[u, v]['curvature']) # Ensure curvature doesn't go too low

# 4. Path Recall (Heuristic)
def recall_path(graph, start_node):
    """
    Recalls a path based on the edge curvatures, starting from a given node.
    Uses a greedy heuristic:  Always go to the neighbor with the highest curvature.

    Args:
        graph (nx.Graph): The graph representing the cities and connections.
        start_node: The node to start the path from.

    Returns:
        list: The recalled path.
    """
    path = [start_node]
    unvisited_nodes = set(graph.nodes())
    unvisited_nodes.remove(start_node)
    current_node = start_node

    while unvisited_nodes:
        # Get neighbors of the current node
        neighbors = list(graph.neighbors(current_node))
        # Find the neighbor with the highest curvature
        best_neighbor = None
        best_curvature = -1
        for neighbor in neighbors:
            if neighbor in unvisited_nodes:
                if graph.edges[current_node, neighbor]['curvature'] > best_curvature:
                    best_curvature = graph.edges[current_node, neighbor]['curvature']
                    best_neighbor = neighbor

        if best_neighbor is None:
            #  If no unvisited neighbors, break to avoid errors.
            break

        current_node = best_neighbor
        path.append(current_node)
        unvisited_nodes.remove(current_node)

    path.append(start_node) #return to start
    return path

# 5. Visualization
def visualize_graph(graph, paths, iteration, recalled_path=None):
    """
    Visualizes the graph, the paths generated, and the edge curvatures.

    Args:
        graph (nx.Graph): The graph representing the cities and connections.
        paths (list of lists):  A list of paths generated in each iteration.
        iteration (int): The current iteration number.
        recalled_path (list, optional): The recalled path to highlight.
    """
    plt.figure(figsize=(8, 6))
    plt.title(f"TSP Simulation on Adaptive Octagon - Iteration {iteration}")
    pos = nx.get_node_attributes(graph, 'position')

    # Draw the nodes
    nx.draw_networkx_nodes(graph, pos, node_color='lightblue', node_size=500)
    nx.draw_networkx_labels(graph, pos, font_size=10)

    # Draw the edges with varying thickness based on curvature
    max_curvature = max(graph.edges[u, v]['curvature'] for u, v in graph.edges())
    min_curvature = min(graph.edges[u, v]['curvature'] for u, v in graph.edges())
    # Ensure max_curvature is at least slightly larger than min_curvature
    if max_curvature == min_curvature:
        max_curvature = min_curvature + 0.1
    for u, v in graph.edges():
        curvature = graph.edges[u, v]['curvature']
        # Normalize curvature for visualization
        normalized_curvature = (curvature - min_curvature) / (max_curvature - min_curvature)
        # Use normalized curvature to control line thickness
        line_width = 1 + 3 * normalized_curvature  # Adjust multiplier for desired thickness range
        nx.draw_networkx_edges(graph, pos, edgelist=[(u, v)], width=line_width, edge_color='gray')

    # Draw the paths
    if paths:
        for i, path in enumerate(paths):
            path_edges = [(path[j], path[j+1]) for j in range(len(path) - 1)]
            # Use a different color for each path, cycle through a few colors
            path_colors = ['r', 'g', 'b', 'm', 'c']
            nx.draw_networkx_edges(graph, pos, edgelist=path_edges, edge_color=path_colors[i % len(path_colors)], width=2)

    if recalled_path:
        recalled_edges = [(recalled_path[j], recalled_path[j+1]) for j in range(len(recalled_path) - 1)]
        nx.draw_networkx_edges(graph, pos, edgelist=recalled_edges, edge_color='yellow', width=3) #highlight

    plt.show()

# 6. Simulation
def run_simulation(num_iterations=10, num_paths_per_iteration=5):
    """
    Runs the simulation for a specified number of iterations.

    Args:
        num_iterations (int): The number of iterations to run.
        num_paths_per_iteration (int): The number of paths to generate and evaluate
            in each iteration.
    """
    graph = create_octagon_graph()
    initialize_curvature(graph)
    all_paths = []
    max_path_length = 8 * 2 #  Scaling factor for curvature updates.

    for iteration in range(num_iterations):
        iteration_paths = []
        for _ in range(num_paths_per_iteration):
            path = generate_random_path(graph)
            path_length = calculate_path_length(graph, path)
            update_curvature(graph, path, path_length, max_path_length)
            iteration_paths.append(path)
        all_paths.append(iteration_paths)
        decay_curvature(graph) #optional
        visualize_graph(graph, iteration_paths, iteration)

        # Recall a path after a few iterations
        if iteration >= num_iterations // 2:
            start_node = random.choice(list(graph.nodes()))
            recalled_path = recall_path(graph, start_node)
            print(f"Recalled Path at iteration {iteration}: {recalled_path}")
            print(f"Length of recalled path: {calculate_path_length(graph, recalled_path)}")
            visualize_graph(graph, iteration_paths, iteration, recalled_path=recalled_path) #show the recalled path


    # Visualize the final state of the graph
    visualize_graph(graph, [], num_iterations)
    return graph #returning graph


if __name__ == "__main__":
    final_graph = run_simulation(num_iterations=15, num_paths_per_iteration=5)
    # You can further analyze the final_graph here if needed.
