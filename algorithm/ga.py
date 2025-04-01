import random
import math
import concurrent.futures
import time

class GeneticAlgorithm:
    def __init__(self, cities, pop_size=50, max_gen=50, mutation_rate=0.05, elitism_count=10, logger=None):
        self.cities = cities
        self.pop_size = pop_size
        self.max_gen = max_gen
        self.mutation_rate = mutation_rate
        self.n = len(cities)
        self.elitism_count = elitism_count
        self.logger = logger

    def total_distance(self, path):
        # Calcul de la distance totale en fermant la boucle (retour à la ville de départ)
        dist = 0
        for i in range(-1, len(path) - 1):
            city_a, city_b = self.cities[path[i]], self.cities[path[i+1]]
            dist += math.dist(city_a, city_b)
        return dist

    def fitness(self, path):
        # Le fitness est l'inverse de la distance totale
        dist = self.total_distance(path)
        return 1.0 / dist if dist > 0 else float('inf')

    def _init_population(self):
        population = []
        for _ in range(self.pop_size):
            indiv = list(range(self.n))
            random.shuffle(indiv)
            # Fixer la ville 0 en première position pour éviter les redondances
            idx0 = indiv.index(0)
            indiv[0], indiv[idx0] = indiv[idx0], indiv[0]
            population.append(indiv)
        return population

    def _selection(self, population):
        # Sélection par tournoi de taille 3
        tournament = random.sample(population, 3)
        return max(tournament, key=self.fitness)

    def _crossover(self, p1, p2):
        size = len(p1)
        child = [None] * size
        # Choix de deux points de découpe (hors indice 0)
        start, end = sorted(random.sample(range(1, size), 2))
        child[start:end] = p1[start:end]

        pos = end
        for gene in p2[1:]:  # On ignore la ville 0 qui reste fixe
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


    def _create_child(self, population):
        parent1 = self._selection(population)
        parent2 = self._selection(population)
        child = self._crossover(parent1, parent2)
        self._mutate(child)
        return child

    def run_step_by_step(self):
        import time
        import concurrent.futures
        population = self._init_population()
        best_path = None
        best_fit = -1
        for gen in range(self.max_gen):
            start_time = time.time()
            population_sorted = sorted(population, key=self.fitness, reverse=True)
            elites = population_sorted[:self.elitism_count]

            num_children = self.pop_size - self.elitism_count
            with concurrent.futures.ThreadPoolExecutor() as executor:
                children = list(executor.map(lambda _: self._create_child(population), range(num_children)))

            population = elites + children

            for indiv in population:
                indiv_fit = self.fitness(indiv)
                if indiv_fit > best_fit:
                    best_fit = indiv_fit
                    best_path = indiv[:]

            duration = time.time() - start_time
            if self.logger:
                self.logger.log("GA", 1.0 / best_fit, duration, generation=gen)

            # Yield the results of the current generation
            yield {
                "generation": gen + 1,  # Generation number starting from 1
                "best_path": best_path,
                "best_distance": 1.0 / best_fit,
                "duration": duration
            }

    def run(self):
        population = self._init_population()
        best_path = None
        best_fit = -1

        for gen in range(self.max_gen):
            start_time = time.time()
            population_sorted = sorted(population, key=self.fitness, reverse=True)
            elites = population_sorted[:self.elitism_count]

            num_children = self.pop_size - self.elitism_count
            with concurrent.futures.ThreadPoolExecutor() as executor:
                children = list(executor.map(lambda _: self._create_child(population), range(num_children)))

            population = elites + children

            for indiv in population:
                indiv_fit = self.fitness(indiv)
                if indiv_fit > best_fit:
                    best_fit = indiv_fit
                    best_path = indiv[:]

            duration = time.time() - start_time
            if self.logger:
                self.logger.log("GA", 1.0 / best_fit, duration, generation=gen)

            print(f"Génération {gen + 1} - Meilleure distance: {1.0 / best_fit:.2f}")

        best_distance = 1.0 / best_fit
        return best_path, best_distance



