"""ENSS Phase-12 MVP entry point.

Usage:
    python src/scripts/run_enss.py [--population 16] [--generations 10]
                                   [--benchmark mock] [--seed 0]

Runs the full evolutionary loop over the 8-architecture search space and
prints per-generation progress plus the final best agent.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from genome.search_space import SearchSpace
from evaluator.benchmark import get_evaluator
from evolution.controller import EvolutionController


def main():
    parser = argparse.ArgumentParser(description="Evolutionary Neural Substrate Search (MVP)")
    parser.add_argument("--population", type=int, default=16)
    parser.add_argument("--generations", type=int, default=10)
    parser.add_argument("--benchmark", type=str, default="mock")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    search_space = SearchSpace()
    evaluator = get_evaluator(args.benchmark)
    controller = EvolutionController(
        search_space,
        evaluator,
        population_size=args.population,
        generations=args.generations,
        seed=args.seed,
    )

    print("ENSS - Evolutionary Neural Substrate Search (Phase-12 MVP)")
    print("Benchmark: %s | Population: %d | Generations: %d"
          % (args.benchmark, args.population, args.generations))
    print("Search space: %d architectures"
          % len(search_space.enumerate_architectures()))
    print()

    def report(gen, evaluated):
        best = evaluated[0]
        mean_fitness = sum(e.fitness for e in evaluated) / len(evaluated)
        print("Generation %d" % gen)
        print("Agent:")
        print(best.genome.describe())
        print("Fitness:")
        print("%.2f (mean: %.2f)" % (best.fitness, mean_fitness))
        print()

    best = controller.run(on_generation=report)

    print("=" * 40)
    print("Best Agent:")
    print(best.genome.describe())
    print("Fitness:")
    print("%.2f" % best.fitness)
    print("Metrics: capability=%.2f efficiency=%.2f adaptability=%.2f" % (
        best.metrics["capability"],
        best.metrics["efficiency"],
        best.metrics["adaptability"],
    ))


if __name__ == "__main__":
    main()
