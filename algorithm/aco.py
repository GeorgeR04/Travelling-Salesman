# aco.py

import random


def run_ant_colony(cities, initial_path=None):
    """
    cities: liste de (x, y).
    initial_path: éventuellement utilisé pour initialiser les phéromones (non géré dans ce mock).

    Retourne une permutation d'indices (ordre de visite).
    (Mock : ordre aléatoire.)
    """
    n = len(cities)
    indices = list(range(n))
    random.shuffle(indices)
    return indices
