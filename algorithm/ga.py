# ga.py

import random

def run_genetic_algorithm(cities):
    """
    cities: liste de (x, y).
    Retourne une permutation d'indices représentant un chemin.
    (Mock : on fait juste un ordre aléatoire pour l'exemple.)
    """
    n = len(cities)
    indices = list(range(n))
    random.shuffle(indices)
    return indices
