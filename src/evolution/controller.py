"""
Evolution Controller for ENSS (Phase-17).

Closes the loop with corrected substrate semantics:

    Architecture Genome -> Memory Bank (train split, leakage-free)
        -> [Weight Inheritance into substrate] -> [Candidate Adaptation]
        -> Evaluation -> Raw Objectives -> NSGA Selection
        -> Mutation/Crossover -> New Generation

Weight inheritance (Phase-17): transfers the parent's POST-ADAPTATION
substrate weights to children with the same memory substrate, so what is
inherited is trained state, not random init. Every candidate receives the
same fixed adaptation budget (evolution/adaptation.py), making the
inheritance comparison controlled.

Selection is genuinely multi-objective: non-dominated sorting into Pareto
fronts + crowding-distance diversity preservation (NSGA3Selector). Scalar
fitness is kept for logging/reporting only, not for selection.
"""

import hashlib
import json
import random

import torch

from genome.architecture import ArchitectureGenome
from models.builder import build_agent
from evolution.mutation import mutate
from evolution.crossover import crossover
from evolution.fitness import calculate_fitness
from evolution.nsga3 import Individual, NSGA3Selector


def genome_signature(genome):
    return json.dumps(genome.to_dict(), sort_keys=True)


def substrate_fingerprint(substrate):
    """Content hash of a substrate state dict (separates inherited/adapted
    variants in the evaluation cache)."""
    h = hashlib.sha256()
    for name in sorted(substrate.state_dict()):
        h.update(name.encode())
        h.update(substrate.state_dict()[name].numpy().tobytes())
    return h.hexdigest()[:16]


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
                 use_inheritance=True, use_pareto=True,
                 adaptation_config=None, mutate_fn=None, crossover_fn=None):
        self.search_space = search_space
        self.evaluator = evaluator
        self.population_size = population_size or search_space.population
        self.generations = generations or search_space.generations
        self.elite_size = elite_size
        self.mutation_rate = mutation_rate
        self.use_inheritance = use_inheritance
        # use_pareto=False is the "evolution w/o Pareto" ablation/baseline:
        # selection falls back to scalar-fitness tournament + truncation.
        self.use_pareto = use_pareto
        # Phase-17: fixed per-candidate adaptation budget (None disables).
        self.adaptation_config = adaptation_config
        # Phase-20: pluggable operators (structured genome support).
        self.mutate_fn = mutate_fn or mutate
        self.crossover_fn = crossover_fn or crossover
        self.rng = random.Random(seed)
        self.selector = NSGA3Selector(self.population_size)
        self.weights = search_space.objective_weights

        self.population = [
            self._random_genome() for _ in range(self.population_size)
        ]
        # Post-adaptation substrate weights, keyed by substrate architecture
        # (memory gene + dims) — inheritance pool across the population.
        self.substrate_bank = {}
        self.history = []
        self.n_inherited_tensors = 0

    def _random_genome(self):
        # structured spaces return genome objects directly; the flat space
        # returns dicts to unpack
        sample = self.search_space.sample(self.rng)
        if isinstance(sample, dict):
            return ArchitectureGenome(**sample)
        return sample

    # -- evaluation -----------------------------------------------------------

    def evaluate_genome(self, genome, parent_genome=None):
        """Build + (inherit) + (adapt) + evaluate one candidate."""
        from evolution.adaptation import adapt_substrate

        # Deterministic per-genome init: substrate weights before any
        # inheritance/adaptation are a pure function of the genome,
        # so cache fingerprints stay reproducible across runs and seeds.
        torch.manual_seed(
            int(hashlib.sha256(genome_signature(genome).encode()).hexdigest(),
                16) % (2 ** 32))

        memory = None
        if (hasattr(self.evaluator, "build_memory_bank")
                and not getattr(self.evaluator, "disable_memory", False)):
            memory = self.evaluator.build_memory_bank(genome)

        substrate = getattr(memory, "substrate", None)
        fingerprint = None
        adaptation_record = {"trainable": False}

        if substrate is not None:
            key = "substrate:%s:%d" % (genome.memory, genome.state_size)
            if (self.use_inheritance and parent_genome is not None
                    and parent_genome.memory == genome.memory
                    and key in self.substrate_bank):
                substrate.load_state_dict(self.substrate_bank[key])
                self.n_inherited_tensors += len(self.substrate_bank[key])
                adaptation_record["inherited"] = True
            else:
                adaptation_record["inherited"] = False

            if self.adaptation_config is not None:
                # Phase-20: per-genome adaptation budget (structured genome);
                # falls back to the controller-level fixed config.
                if getattr(genome, "adaptation_enabled", True):
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
                    record = adapt_substrate(
                        memory, self.evaluator.calibration_samples(), cfg)
                    adaptation_record.update(record)
                    self.substrate_bank[key] = {
                        k: v.clone() for k, v in substrate.state_dict().items()
                    }
            fingerprint = substrate_fingerprint(substrate)

        agent = build_agent(genome)
        metrics = self.evaluator.evaluate(
            genome, agent, memory_controller=memory,
            substrate_fingerprint=fingerprint)
        metrics["adaptation"] = adaptation_record
        fitness = calculate_fitness(metrics, self.weights)
        return EvaluatedAgent(genome, metrics, fitness)

    # -- selection ------------------------------------------------------------

    def _tournament(self, individuals):
        a, b = self.rng.sample(individuals, k=min(2, len(individuals)))
        return self.selector.tournament(a, b).payload

    # -- main loop --------------------------------------------------------------

    def _initial_evaluation(self):
        return [self.evaluate_genome(g) for g in self.population]

    def step(self, evaluated):
        """One generation: mate -> inherit/adapt -> evaluate -> select.

        With ``use_pareto`` selection is NSGA multi-objective (fronts +
        crowding); otherwise it is scalar-fitness truncation (ablation).
        """
        individuals = [e.as_individual() for e in evaluated]
        self.selector.select(individuals)  # assigns rank + crowding

        def mate():
            if self.use_pareto:
                return self._tournament(individuals)
            a, b = self.rng.sample(evaluated, k=min(2, len(evaluated)))
            return a if a.fitness >= b.fitness else b

        offspring = []
        seen_hashes = set()
        try:
            from genome.structured import task_phenotype_hash
            bench_name = getattr(self.evaluator, "BENCHMARK", "")
            if bench_name:
                from genome.structured import StructuredGenome
                seen_hashes = {
                    task_phenotype_hash(g, bench_name)
                    for g in self.population
                    if isinstance(g, StructuredGenome)
                }
        except ImportError:
            seen_hashes = set()

        while len(offspring) < self.population_size - self.elite_size:
            parent_a = mate()
            parent_b = mate()
            child = self.crossover_fn(parent_a.genome, parent_b.genome,
                                      self.rng)
            if self.rng.random() < self.mutation_rate:
                child = self.mutate_fn(child, self.search_space, self.rng)
            # Phase-21: dedup identical effective phenotypes within a
            # generation (task-aware), so population slots aren't wasted.
            if seen_hashes:
                try:
                    from genome.structured import (StructuredGenome,
                                                   task_phenotype_hash)
                    if isinstance(child, StructuredGenome):
                        h = task_phenotype_hash(child, bench_name)
                        if h in seen_hashes:
                            continue
                        seen_hashes.add(h)
                except ImportError:
                    pass
            offspring.append((child, parent_a.genome))

        evaluated_offspring = [
            self.evaluate_genome(child, parent_genome=parent)
            for child, parent in offspring
        ]

        if self.use_pareto:
            combined = [e.as_individual()
                        for e in evaluated + evaluated_offspring]
            survivors = self.selector.select(combined, self.population_size)
            next_evaluated = [s.payload for s in survivors]
        else:
            combined = evaluated + evaluated_offspring
            combined.sort(key=lambda e: e.fitness, reverse=True)
            next_evaluated = combined[: self.population_size]

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
