import random
import math

class AntColony:
    def __init__(self, cities, ant_count=20, iterations=50,
                 alpha=1.0, beta=5.0, evap=0.3, initial_path=None):
        self.cities = cities
        self.ant_count = ant_count
        self.iterations = iterations
        self.alpha = alpha
        self.beta = beta
        self.evap = evap
        self.n = len(cities)

        # Pheromones init
        self.pheromones = [[0.1] * self.n for _ in range(self.n)]

        # Dépôt initial de phéromones si path fourni
        if initial_path:
            self._deposit_pheromones(initial_path, 5.0 / self._total_distance(initial_path))

    def _total_distance(self, path):
        dist = 0
        for i in range(-1, len(path) - 1):
            city_a, city_b = self.cities[path[i]], self.cities[path[i+1]]
            dist += math.dist(city_a, city_b)
        return dist

    def _select_next(self, current, unvisited):
        """Choix de la ville suivante par roulette-wheel."""
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

    def _evaporate_pheromones(self):
        for i in range(self.n):
            for j in range(self.n):
                self.pheromones[i][j] = max(self.pheromones[i][j] * (1 - self.evap), 0.001)

    def _deposit_pheromones(self, path, amount):
        for i in range(-1, len(path) - 1):
            a, b = path[i], path[i+1]
            self.pheromones[a][b] += amount
            self.pheromones[b][a] += amount

    def run(self):
        best_path = None
        best_dist = float('inf')

        for _ in range(self.iterations):
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

            # Évaporation globale
            self._evaporate_pheromones()

            # Dépôt sur chaque solution
            for path, dist_path in solutions:
                self._deposit_pheromones(path, 1.0 / dist_path)

        return best_path, best_dist
