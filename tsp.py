import numpy as np

# Function to generate randomized TSP distance matrices
def generate_distances(num_cities, seed=42):
    np.random.seed(seed)
    distances = np.random.randint(10, 100, (num_cities, num_cities)).astype(float)
    distances = (distances + distances.T) / 2
    np.fill_diagonal(distances, np.inf)
    return distances

# Initialize conductances
def initialize_conductances(num_cities):
    return np.ones((num_cities, num_cities))

# Update conductances based on tour
def update_conductances(conductances, tour, distances, alpha, mu):
    for i in range(len(tour)-1):
        conductances[tour[i], tour[i+1]] += alpha / distances[tour[i], tour[i+1]]
        conductances[tour[i+1], tour[i]] = conductances[tour[i], tour[i+1]]
    conductances *= (1 - mu)
    return conductances

# Probabilistic ARP implementation
def probabilistic_arp_tsp(distances, conductances, iterations=100, initial_alpha=0.5, initial_mu=0.1):
    best_tour, best_distance = None, float('inf')
    alpha, mu = initial_alpha, initial_mu
    num_cities = len(distances)

    for _ in range(iterations):
        tour = [0]
        unvisited = set(range(1, num_cities))
        while unvisited:
            current = tour[-1]
            probabilities = np.array([conductances[current, city] / distances[current, city] for city in unvisited])
            probabilities = np.clip(probabilities, a_min=1e-10, a_max=None)
            probabilities /= probabilities.sum()

            next_city = np.random.choice(list(unvisited), p=probabilities)
            tour.append(next_city)
            unvisited.remove(next_city)

        tour.append(0)
        current_distance = sum(distances[tour[i], tour[i+1]] for i in range(len(tour)-1))

        if current_distance < best_distance:
            best_tour, best_distance = tour, current_distance
            alpha *= 1.05
            mu *= 0.95
        else:
            alpha *= 0.95
            mu *= 1.05

        conductances = update_conductances(conductances, tour, distances, alpha, mu)

    return best_tour, best_distance

# Run ARP TSP simulations for various city scenarios
for num_cities in [5, 10, 50]:
    distances = generate_distances(num_cities)
    conductances = initialize_conductances(num_cities)
    best_tour, best_distance = probabilistic_arp_tsp(distances, conductances)
    print(f"Cities: {num_cities}, Best Distance: {best_distance}")
