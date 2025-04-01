import json
import os

class StatsLogger:
    def __init__(self, file_path="stats.json"):
        self.file_path = file_path
        self.data = self._load_stats()

    def _load_stats(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erreur lors du chargement des stats: {e}")
        # Structure par défaut
        return {
            "GA": {"distances": [], "times": [], "extra": []},
            "ACO": {"distances": [], "times": [], "extra": []},
            "Hybride": {"distances": [], "times": [], "extra": []},
        }

    def _save_stats(self):
        try:
            with open(self.file_path, "w") as f:
                json.dump(self.data, f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des stats: {e}")

    def reset(self):
        self.data = {
            "GA": {"distances": [], "times": [], "extra": []},
            "ACO": {"distances": [], "times": [], "extra": []},
            "Hybride": {"distances": [], "times": [], "extra": []},
        }
        self._save_stats()

    def log(self, algo_name, distance=None, timestamp=None, **kwargs):
        if algo_name not in self.data:
            self.data[algo_name] = {"distances": [], "times": [], "extra": []}
        if distance is not None:
            self.data[algo_name]["distances"].append(distance)
        if timestamp is not None:
            self.data[algo_name]["times"].append(timestamp)
        if kwargs:
            self.data[algo_name]["extra"].append(kwargs)
        self._save_stats()

    def get(self, algo_name):
        return self.data.get(algo_name, {})

    def get_all(self):
        return self.data
