# ga.py

import random
import math

def total_distance(path, cities):
    dist = 0.0
    for i in range(len(path) - 1):
        dist += math.dist(cities[path[i]], cities[path[i + 1]])
    # Retour à la ville initiale
    dist += math.dist(cities[path[-1]], cities[path[0]])
    return dist

def fitness(path, cities):
    d = total_distance(path, cities)
    return 1.0 / d if d > 0 else 1e9

def init_population(pop_size, n):
    """
    Génère pop_size permutations aléatoires, en forçant 0 en tête.
    """
    population = []
    for _ in range(pop_size):
        indiv = list(range(n))
        random.shuffle(indiv)
        # on force l'indice 0 en position 0
        idx0 = indiv.index(0)
        indiv[0], indiv[idx0] = indiv[idx0], indiv[0]
        population.append(indiv)
    return population

def selection(pop, cities):
    """
    Sélection par tournoi (taille=3).
    """
    best = None
    for _ in range(3):
        indiv = random.choice(pop)
        if best is None or fitness(indiv, cities) > fitness(best, cities):
            best = indiv
    return best

def crossover(p1, p2):
    """
    Ordered Crossover (simplifié), en évitant de toucher à l'indice 0.
    """
    size = len(p1)
    child = [None] * size

    start, end = sorted([random.randint(1, size - 1) for _ in range(2)])
    child[start:end] = p1[start:end]

    pos = end
    for gene in p2[1:]:  # on saute la ville 0
        if gene not in child:
            if pos >= size:
                pos = 1
            child[pos] = gene
            pos += 1

    child[0] = 0  # on force 0 au début
    return child

def mutate(path, rate=0.05):
    """
    Mutation par swap, en évitant la position 0 (ville 0).
    """
    for i in range(1, len(path)):
        if random.random() < rate:
            j = random.randint(1, len(path) - 1)
            path[i], path[j] = path[j], path[i]

def run_genetic_algorithm(cities, pop_size=30, max_gen=50, mutation_rate=0.05):
    """
    Renvoie (best_path, best_dist).
    best_path = liste d'indices (commençant par 0),
    best_dist = distance totale de ce chemin.
    """
    n = len(cities)
    pop = init_population(pop_size, n)

    best_indiv = None
    best_fit = -1

    for _ in range(max_gen):
        new_pop = []
        for _ in range(pop_size):
            p1 = selection(pop, cities)
            p2 = selection(pop, cities)
            child = crossover(p1, p2)
            mutate(child, mutation_rate)
            new_pop.append(child)
        pop = new_pop

        # mise à jour du meilleur
        for indiv in pop:
            f = fitness(indiv, cities)
            if f > best_fit:
                best_fit = f
                best_indiv = indiv[:]

    best_dist = 1.0 / best_fit
    return best_indiv, best_dist
