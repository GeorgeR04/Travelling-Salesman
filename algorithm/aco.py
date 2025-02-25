# aco.py

import random
import math

def total_distance(path, cities):
    dist = 0.0
    for i in range(len(path) - 1):
        dist += math.dist(cities[path[i]], cities[path[i + 1]])
    dist += math.dist(cities[path[-1]], cities[path[0]])
    return dist

def run_ant_colony(cities, ant_count=20, iterations=50,
                   alpha=1.0, beta=5.0, evap=0.3,
                   initial_path=None):
    """
    Algorithme ACO simple, renvoie (best_path, best_dist).
    'initial_path' sert à poser un surplus de phéromones avant de commencer.
    """
    n = len(cities)
    # matrice de phéromones
    pheromones = [[0.1 for _ in range(n)] for _ in range(n)]

    # Si on a un chemin initial, on dépose plus de phéromones dessus
    if initial_path is not None:
        d_init = total_distance(initial_path, cities)
        deposit_init = 5.0 / d_init
        for i in range(len(initial_path) - 1):
            a = initial_path[i]
            b = initial_path[i + 1]
            pheromones[a][b] += deposit_init
            pheromones[b][a] += deposit_init
        # boucle
        a, b = initial_path[-1], initial_path[0]
        pheromones[a][b] += deposit_init
        pheromones[b][a] += deposit_init

    def select_next(current, unvisited):
        probs = []
        s = 0.0
        for city in unvisited:
            tau = pheromones[current][city] ** alpha
            d = math.dist(cities[current], cities[city])
            inv = (1.0 / d) ** beta if d > 0 else 0
            val = tau * inv
            probs.append((city, val))
            s += val
        if s <= 0:
            return random.choice(list(unvisited))

        r = random.random() * s
        cumul = 0.0
        for cty, val in probs:
            cumul += val
            if cumul >= r:
                return cty
        return probs[-1][0]  # fallback

    best_path = None
    best_dist = float("inf")

    for _ in range(iterations):
        solutions = []
        # Construction de chemins
        for _ant in range(ant_count):
            path = [0]
            unvisited = set(range(n)) - {0}
            current = 0
            while unvisited:
                nxt = select_next(current, unvisited)
                path.append(nxt)
                unvisited.remove(nxt)
                current = nxt
            dist_path = total_distance(path, cities)
            solutions.append((path, dist_path))

        # évaporation
        for i in range(n):
            for j in range(n):
                pheromones[i][j] *= (1 - evap)
                if pheromones[i][j] < 0.001:
                    pheromones[i][j] = 0.001

        # dépôt
        for sol, d in solutions:
            dep = 1.0 / d
            for k in range(len(sol) - 1):
                a = sol[k]
                b = sol[k + 1]
                pheromones[a][b] += dep
                pheromones[b][a] += dep
            # boucle
            a, b = sol[-1], sol[0]
            pheromones[a][b] += dep
            pheromones[b][a] += dep

        # Meilleur local
        for sol, dist_ in solutions:
            if dist_ < best_dist:
                best_dist = dist_
                best_path = sol

    return best_path, best_dist
