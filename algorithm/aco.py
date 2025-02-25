import random

def run_ant_colony(cities, initial_path=None):
    """
    cities: liste de (x, y).
    initial_path: éventuellement utilisé pour init. (non géré dans ce mock).

    On renvoie un ordre de visite
    en commençant toujours par l'indice 0 (ville n°1).
    """
    n = len(cities)
    indices = list(range(n))
    random.shuffle(indices)

    # Forcer l'indice 0 à être en tête.
    if 0 in indices:
        idx0 = indices.index(0)
        indices[0], indices[idx0] = indices[idx0], indices[0]

    return indices
