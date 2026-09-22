"""Random search baseline for ENSS experiments (Phase-14..17).

"w/o Evolution" baseline: evaluates random genomes with the same evaluation
budget (population_size x generations) as ENSS, without any selection,
crossover, mutation pressure, or weight inheritance.

Phase-17: candidates receive the same fixed adaptation budget as
evolutionary candidates (equal-budget fairness), with freshly initialized
substrates (no inheritance pool).
"""

import hashlib
import random

import torch

from genome.architecture import ArchitectureGenome
from models.builder import build_agent
from evolution.fitness import calculate_fitness
from evolution.controller import EvaluatedAgent, genome_signature


class RandomSearchController:
    """Same interface as EvolutionController.run(on_generation=...)."""

    def __init__(self, search_space, evaluator, population_size=None,
                 generations=None, seed=0, adaptation_config=None):
        self.search_space = search_space
        self.evaluator = evaluator
        self.population_size = population_size or search_space.population
        self.generations = generations or search_space.generations
        self.rng = random.Random(seed)
        self.weights = search_space.objective_weights
        self.adaptation_config = adaptation_config
        self.history = []

    def _evaluate(self, genome):
        from evolution.adaptation import adapt_substrate
        from evolution.controller import substrate_fingerprint

        torch.manual_seed(
            int(hashlib.sha256(genome_signature(genome).encode()).hexdigest(),
                16) % (2 ** 32))

        memory = None
        if (hasattr(self.evaluator, "build_memory_bank")
                and not getattr(self.evaluator, "disable_memory", False)):
            memory = self.evaluator.build_memory_bank(genome)

        substrate = getattr(memory, "substrate", None)
        fingerprint = None
        # Phase-20: respect per-genome adaptation genes when present.
        adapt_ok = getattr(genome, "adaptation_enabled", True)
        if (substrate is not None and self.adaptation_config is not None
                and adapt_ok):
            from evolution.adaptation import AdaptationConfig
            cfg = self.adaptation_config
            steps = getattr(genome, "adaptation_steps", None)
            if steps is not None:
                cfg = AdaptationConfig(
                    calibration_samples=cfg.calibration_samples,
                    adaptation_steps=steps,
                    learning_rate=cfg.learning_rate,
                    weight_decay=cfg.weight_decay,
                    sequence_window=cfg.sequence_window,
                    seed=cfg.seed)
            adapt_substrate(memory, self.evaluator.calibration_samples(), cfg)
            fingerprint = substrate_fingerprint(substrate)

        agent = build_agent(genome)
        metrics = self.evaluator.evaluate(
            genome, agent, memory_controller=memory,
            substrate_fingerprint=fingerprint)
        fitness = calculate_fitness(metrics, self.weights)
        return EvaluatedAgent(genome, metrics, fitness)

    def run(self, on_generation=None):
        best = None
        for gen in range(1, self.generations + 1):
            batch = []
            for _ in range(self.population_size):
                sample = self.search_space.sample(self.rng)
                genome = sample if not isinstance(sample, dict) \
                    else ArchitectureGenome(**sample)
                batch.append(self._evaluate(genome))
            batch.sort(key=lambda e: e.fitness, reverse=True)
            if best is None or batch[0].fitness > best.fitness:
                best = batch[0]
            self.history.append(batch)
            if on_generation is not None:
                on_generation(gen, batch)
        return best
