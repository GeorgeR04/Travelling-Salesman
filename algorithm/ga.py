import random
import math

class GeneticAlgorithm:
    def __init__(self, cities, pop_size=30, max_gen=50, mutation_rate=0.05):
        self.cities = cities
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.mutation_rate = mutation_rate
        self.n = len(cities)

    def total_distance(self, path):
        # Ferme la boucle (path[-1] à path[0])
        dist = 0
        for i in range(-1, len(path) - 1):
            city_a, city_b = self.cities[path[i]], self.cities[path[i+1]]
            dist += math.dist(city_a, city_b)
        return dist

    def fitness(self, path):
        dist = self.total_distance(path)
        return 1.0 / dist if dist else float('inf')

    def _init_population(self):
        population = []
        for _ in range(self.pop_size):
            indiv = list(range(self.n))
            random.shuffle(indiv)

            # Force city 0 en première position (pour éviter redondances)
            idx0 = indiv.index(0)
            indiv[0], indiv[idx0] = indiv[idx0], indiv[0]
            population.append(indiv)
        return population

    def _selection(self, population):
        # Tournoi de taille 3
        tournament = random.sample(population, 3)
        return max(tournament, key=self.fitness)

    def _crossover(self, p1, p2):
        size = len(p1)
        child = [None] * size

        # On croise uniquement les gènes [start:end] (hors city 0)
        start, end = sorted(random.sample(range(1, size), 2))
        child[start:end] = p1[start:end]

        pos = end
        for gene in p2[1:]:  # on évite le city 0 fixe
            if gene not in child:
                if pos >= size:
                    pos = 1
                child[pos] = gene
                pos += 1

        child[0] = 0
        return child

    def _mutate(self, path):
        # Mutations simples par échange (sans toucher city 0)
        for i in range(1, len(path)):
            if random.random() < self.mutation_rate:
                j = random.randint(1, len(path) - 1)
                path[i], path[j] = path[j], path[i]

    def run(self):
        population = self._init_population()
        best_path, best_fit = None, -1

        for _ in range(self.max_gen):
            new_population = []
            for _ in range(self.pop_size):
                parent1 = self._selection(population)
                parent2 = self._selection(population)
                child = self._crossover(parent1, parent2)
                self._mutate(child)
                new_population.append(child)

            population = new_population

            for indiv in population:
                indiv_fit = self.fitness(indiv)
                if indiv_fit > best_fit:
                    best_fit = indiv_fit
                    best_path = indiv[:]

        best_distance = 1.0 / best_fit
        return best_path, best_distance
