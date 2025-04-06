import random
import math

class AntColony:
    def __init__(self, cities, ant_count=20, iterations=50, alpha=1.0, beta=5.0, evap=0.3, initial_path=None, logger=None):
        self.cities = cities
        self.ant_count = ant_count
        self.iterations = iterations
        self.alpha = alpha
        self.beta = beta
        self.evap = evap
        self.n = len(cities)
        self.logger = logger
        self.pheromones = [[0.1] * self.n for _ in range(self.n)]

        if initial_path:
            self._deposit_pheromones(initial_path, 5.0 / self._total_distance(initial_path))

    # ==============
    # FR: Calcule la distance totale d'un chemin donné en visitant chaque ville dans l'ordre.
    #
    # EN: Calculates the total distance of a given path visiting each city in sequence.
    # =========
    def _total_distance(self, path):
        dist = 0
        for i in range(-1, len(path) - 1):
            city_a, city_b = self.cities[path[i]], self.cities[path[i+1]]
            dist += math.dist(city_a, city_b)
        return dist

    # ==============
    # FR: Sélectionne la prochaine ville à visiter selon une roulette probabiliste influencée par les phéromones et la distance.
    #
    # EN: Selects the next city to visit using a roulette-wheel based on pheromones and distance.
    # =========
    def _select_next(self, current, unvisited):
        probabilities = []
        total = 0.0

        for city in unvisited:
            tau = self.pheromones[current][city] ** self.alpha
            dist = math.dist(self.cities[current], self.cities[city])
            inv_dist = (1.0 / dist) ** self.beta if dist else 0
            prob = tau * inv_dist
            probabilities.append((city, prob))
            total += prob

        if total <= 0:
            return random.choice(list(unvisited))

        threshold = random.uniform(0, total)
        cumul = 0.0
        for city, prob in probabilities:
            cumul += prob
            if cumul >= threshold:
                return city

        return probabilities[-1][0]

    # ==============
    # FR: Fait évaporer une partie des phéromones sur tous les chemins.
    #
    # EN: Evaporates part of the pheromones across all paths.
    # =========
    def _evaporate_pheromones(self):
        for i in range(self.n):
            for j in range(self.n):
                self.pheromones[i][j] = max(self.pheromones[i][j] * (1 - self.evap), 0.001)

    # ==============
    # FR: Dépose une certaine quantité de phéromones sur un chemin parcouru.
    #
    # EN: Deposits a specified amount of pheromones along a given path.
    # =========
    def _deposit_pheromones(self, path, amount):
        for i in range(-1, len(path) - 1):
            a, b = path[i], path[i+1]
            self.pheromones[a][b] += amount
            self.pheromones[b][a] += amount

    # ==============
    # FR: Exécute l'algorithme de colonie de fourmis pour trouver un chemin optimal.
    #
    # EN: Executes the ant colony algorithm to find an optimal path.
    # =========
    def run(self):
        import time
        best_path = None
        best_dist = float('inf')

        for it in range(self.iterations):
            start_time = time.time()
            solutions = []
            for _ in range(self.ant_count):
                path = [0]
                unvisited = set(range(1, self.n))
                current = 0

                while unvisited:
                    next_city = self._select_next(current, unvisited)
                    path.append(next_city)
                    unvisited.remove(next_city)
                    current = next_city

                dist_path = self._total_distance(path)
                solutions.append((path, dist_path))

                if dist_path < best_dist:
                    best_path, best_dist = path, dist_path

            self._evaporate_pheromones()
            for path, dist_path in solutions:
                self._deposit_pheromones(path, 1.0 / dist_path)

            duration = time.time() - start_time
            if self.logger:
                self.logger.log("ACO", best_dist, duration, iteration=it)

        return best_path, best_dist

