"""Random search baseline for ENSS experiments (Phase-14).

"w/o Evolution" baseline: evaluates random genomes with the same evaluation
budget (population_size x generations) as ENSS, without any selection,
crossover, mutation pressure, or weight inheritance.
"""

import random

from genome.architecture import ArchitectureGenome
from models.builder import build_agent
from evolution.fitness import calculate_fitness
from evolution.controller import EvaluatedAgent


class RandomSearchController:
    """Same interface as EvolutionController.run(on_generation=...)."""

    def __init__(self, search_space, evaluator, population_size=None,
                 generations=None, seed=0):
        self.search_space = search_space
        self.evaluator = evaluator
        self.population_size = population_size or search_space.population
        self.generations = generations or search_space.generations
        self.rng = random.Random(seed)
        self.weights = search_space.objective_weights
        self.history = []

    def _evaluate(self, genome):
        agent = build_agent(genome)
        metrics = self.evaluator.evaluate(genome, agent)
        fitness = calculate_fitness(metrics, self.weights)
        return EvaluatedAgent(genome, metrics, fitness)

    def run(self, on_generation=None):
        best = None
        for gen in range(1, self.generations + 1):
            batch = [
                self._evaluate(ArchitectureGenome(
                    **self.search_space.sample(self.rng)))
                for _ in range(self.population_size)
            ]
            batch.sort(key=lambda e: e.fitness, reverse=True)
            if best is None or batch[0].fitness > best.fitness:
                best = batch[0]
            self.history.append(batch)
            if on_generation is not None:
                on_generation(gen, batch)
        return best
