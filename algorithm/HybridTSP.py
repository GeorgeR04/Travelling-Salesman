import time
from ga import GeneticAlgorithm
from aco import AntColony

class HybridTSP:
    def __init__(self, cities, logger=None, ga_params=None, aco_params=None):
        self.cities = cities
        self.logger = logger
        self.ga_params = ga_params or {}
        self.aco_params = aco_params or {}

    def run(self):
        start_time = time.time()

        ga = GeneticAlgorithm(
            self.cities,
            logger=self.logger,
            **self.ga_params
        )
        best_path_ga, best_distance_ga = ga.run()

        aco = AntColony(
            self.cities,
            initial_path=best_path_ga,
            logger=self.logger,
            **self.aco_params
        )
        best_path_aco, best_distance_aco = aco.run()

        duration = time.time() - start_time
        if self.logger:
            self.logger.log("Hybride", best_distance_aco, duration)

        return best_path_aco, best_distance_aco
