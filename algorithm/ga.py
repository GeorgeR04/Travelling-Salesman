import random


def run_genetic_algorithm(cities):
    """
    cities: liste de (x, y).
    Retourne une permutation d'indices représentant un chemin
    en commençant toujours par l'indice 0 (ville n°1).
    """
    n = len(cities)
    indices = list(range(n))
    random.shuffle(indices)

    # On force l'indice 0 à être au début.
    if 0 in indices:
        idx0 = indices.index(0)
        indices[0], indices[idx0] = indices[idx0], indices[0]

    return indices
