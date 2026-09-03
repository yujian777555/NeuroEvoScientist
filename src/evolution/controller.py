"""
Evolution Controller for ENSS (Phase-13).

Closes the loop:

    Architecture Genome -> Agent Builder -> Candidate Agent
        -> Evaluation -> Fitness -> NSGA Selection -> Mutation/Crossover
        (+ Weight Inheritance) -> New Generation

Selection is genuinely multi-objective: non-dominated sorting into Pareto
fronts + crowding-distance diversity preservation (NSGA3Selector). Scalar
fitness is kept for logging/reporting only, not for selection.

Weight inheritance: offspring built from a parent reuse all compatible
parent tensors (evolution/inheritance.py), cutting evaluation cost.
"""

import json
import random

from genome.architecture import ArchitectureGenome
from models.builder import build_agent
from evolution.mutation import mutate
from evolution.crossover import crossover
from evolution.fitness import calculate_fitness
from evolution.inheritance import inherit_state
from evolution.nsga3 import Individual, NSGA3Selector


def genome_signature(genome):
    return json.dumps(genome.to_dict(), sort_keys=True)


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

    def as_individual(self):
        return Individual(genome=self.genome, objectives=self.objectives,
                          payload=self)


class EvolutionController:
    def __init__(self, search_space, evaluator, population_size=None,
                 generations=None, seed=0, elite_size=2, mutation_rate=0.3,
                 use_inheritance=True):
        self.search_space = search_space
        self.evaluator = evaluator
        self.population_size = population_size or search_space.population
        self.generations = generations or search_space.generations
        self.elite_size = elite_size
        self.mutation_rate = mutation_rate
        self.use_inheritance = use_inheritance
        self.rng = random.Random(seed)
        self.selector = NSGA3Selector(self.population_size)
        self.weights = search_space.objective_weights

        self.population = [
            self._random_genome() for _ in range(self.population_size)
        ]
        self.state_bank = {}  # genome signature -> latest agent state_dict
        self.history = []
        self.n_inherited_tensors = 0

    def _random_genome(self):
        return ArchitectureGenome(**self.search_space.sample(self.rng))

    # -- evaluation -----------------------------------------------------------

    def evaluate_genome(self, genome, parent_genome=None):
        """Build + evaluate one candidate, optionally inheriting weights."""
        agent = build_agent(genome)

        if (self.use_inheritance and parent_genome is not None):
            parent_state = self.state_bank.get(genome_signature(parent_genome))
            if parent_state:
                inherited = inherit_state(parent_genome, parent_state, genome,
                                          child_state=agent.state_dict())
                if inherited:
                    agent.load_state_dict(inherited, strict=False)
                    self.n_inherited_tensors += len(inherited)

        metrics = self.evaluator.evaluate(genome, agent)
        fitness = calculate_fitness(metrics, self.weights)
        self.state_bank[genome_signature(genome)] = agent.state_dict()
        return EvaluatedAgent(genome, metrics, fitness)

    # -- selection ------------------------------------------------------------

    def _tournament(self, individuals):
        a, b = self.rng.sample(individuals, k=min(2, len(individuals)))
        return self.selector.tournament(a, b).payload

    # -- main loop --------------------------------------------------------------

    def _initial_evaluation(self):
        return [self.evaluate_genome(g) for g in self.population]

    def step(self, evaluated):
        """One NSGA-style generation: mate -> inherit -> evaluate -> select."""
        individuals = [e.as_individual() for e in evaluated]
        self.selector.select(individuals)  # assigns rank + crowding

        offspring = []
        while len(offspring) < self.population_size - self.elite_size:
            parent_a = self._tournament(individuals)
            parent_b = self._tournament(individuals)
            child = crossover(parent_a.genome, parent_b.genome, self.rng)
            if self.rng.random() < self.mutation_rate:
                child = mutate(child, self.search_space, self.rng)
            offspring.append((child, parent_a.genome))

        evaluated_offspring = [
            self.evaluate_genome(child, parent_genome=parent)
            for child, parent in offspring
        ]

        combined = [e.as_individual() for e in evaluated + evaluated_offspring]
        survivors = self.selector.select(combined, self.population_size)
        next_evaluated = [s.payload for s in survivors]

        # Elites: best scalar fitness survives unchanged at the front of the
        # next population (they are already in survivors via Pareto selection).
        next_evaluated.sort(key=lambda e: e.fitness, reverse=True)
        self.population = [e.genome for e in next_evaluated]
        self.history.append(next_evaluated)
        return next_evaluated

    def run(self, on_generation=None):
        """Run all generations; ``on_generation(gen_idx, evaluated)`` per gen."""
        evaluated = self._initial_evaluation()
        evaluated.sort(key=lambda e: e.fitness, reverse=True)
        self.history.append(evaluated)
        if on_generation is not None:
            on_generation(1, evaluated)

        for gen in range(2, self.generations + 1):
            evaluated = self.step(evaluated)
            if on_generation is not None:
                on_generation(gen, evaluated)

        return evaluated[0]
