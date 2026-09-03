"""
Evolution Controller.

Maintains population and evolves neural substrates.
"""

from typing import List

from genome.architecture import ArchitectureGenome
from evolution.mutation import mutate


class EvolutionController:
    def __init__(self, population_size=32):
        self.population = [ArchitectureGenome() for _ in range(population_size)]

    def evolve(self):
        offspring = []
        for agent in self.population:
            offspring.append(mutate(agent))
        self.population = offspring
        return self.population
