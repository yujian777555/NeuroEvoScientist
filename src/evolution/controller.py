"""
Evolution Controller for ENSS (Phase-12 MVP).

Closes the loop:

    Architecture Genome -> Agent Builder -> Candidate Agent
        -> Evaluation -> Fitness -> Selection -> Mutation/Crossover
        -> New Generation

Selection: NSGA-III-style Pareto front + tournament; elites are preserved.
"""

import random

from genome.architecture import ArchitectureGenome
from models.builder import build_agent
from evolution.mutation import mutate
from evolution.crossover import crossover
from evolution.fitness import calculate_fitness
from evolution.nsga3 import Individual, NSGA3Selector


class EvaluatedAgent:
    """A genome bundled with its evaluation results."""

    def __init__(self, genome, metrics, fitness):
        self.genome = genome
        self.metrics = metrics
        self.fitness = fitness

    @property
    def objectives(self):
        return [
            self.metrics["capability"],
            self.metrics["efficiency"],
            self.metrics["adaptability"],
        ]


class EvolutionController:
    def __init__(self, search_space, evaluator, population_size=None,
                 generations=None, seed=0, elite_size=2, mutation_rate=0.3):
        self.search_space = search_space
        self.evaluator = evaluator
        self.population_size = population_size or search_space.population
        self.generations = generations or search_space.generations
        self.elite_size = elite_size
        self.mutation_rate = mutation_rate
        self.rng = random.Random(seed)
        self.selector = NSGA3Selector(self.population_size)
        self.weights = search_space.objective_weights

        self.population = [
            self._random_genome() for _ in range(self.population_size)
        ]
        self.history = []

    def _random_genome(self):
        return ArchitectureGenome(**self.search_space.sample(self.rng))

    def evaluate_population(self, genomes):
        evaluated = []
        for genome in genomes:
            agent = build_agent(genome)
            metrics = self.evaluator.evaluate(genome, agent)
            fitness = calculate_fitness(metrics, self.weights)
            evaluated.append(EvaluatedAgent(genome, metrics, fitness))
        return evaluated

    def _select_parents(self, evaluated):
        """Tournament selection over the population.

        The NSGA-III-style Pareto front is still computed (it will drive
        reference-point niching in later phases); for the MVP, scalar-fitness
        tournaments provide the selection pressure that converges the
        population.
        """
        individuals = [
            Individual(genome=e.genome, objectives=e.objectives)
            for e in evaluated
        ]
        self.selector.select(individuals)  # Pareto front (logging/future use)

        def tournament():
            contenders = self.rng.sample(evaluated, k=min(3, len(evaluated)))
            return max(contenders, key=lambda e: e.fitness).genome

        return [tournament() for _ in range(self.population_size)]

    def _reproduce(self, parent_a, parent_b):
        child = crossover(parent_a, parent_b, self.rng)
        if self.rng.random() < self.mutation_rate:
            child = mutate(child, self.search_space, self.rng)
        return child

    def step(self):
        """Advance one generation; returns the evaluated current population."""
        evaluated = self.evaluate_population(self.population)
        evaluated.sort(key=lambda e: e.fitness, reverse=True)
        self.history.append(evaluated)

        parents = self._select_parents(evaluated)
        n_offspring = self.population_size - self.elite_size
        offspring = []
        for i in range(n_offspring):
            a, b = parents[i], parents[(i + 1) % len(parents)]
            offspring.append(self._reproduce(a, b))

        elites = [e.genome for e in evaluated[: self.elite_size]]
        self.population = elites + offspring[:n_offspring]
        return evaluated

    def run(self, on_generation=None):
        """Run all generations; ``on_generation(gen_idx, evaluated)`` per step."""
        for gen in range(1, self.generations + 1):
            evaluated = self.step()
            if on_generation is not None:
                on_generation(gen, evaluated)
        final = self.evaluate_population(self.population)
        final.sort(key=lambda e: e.fitness, reverse=True)
        return final[0]
