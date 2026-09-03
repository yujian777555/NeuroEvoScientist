"""ENSS entry point (Phase-13).

Usage:
    # CI smoke test on the synthetic signal
    python src/scripts/run_enss.py --benchmark mock

    # Real GSM8K evolution (requires a local HF model, e.g. on A800)
    python src/scripts/run_enss.py --benchmark gsm8k \
        --model mistralai/Mistral-7B-v0.1 --limit 200

Runs the full evolutionary loop over the 64-architecture search space with
NSGA multi-objective selection and weight inheritance, printing
per-generation progress plus the final best agent.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from genome.search_space import SearchSpace
from evaluator.benchmark import get_evaluator
from evolution.controller import EvolutionController


def build_evaluator(args):
    if args.benchmark == "gsm8k":
        from evaluator.gsm8k import GSM8KEvaluator, HFTransformersBackend
        if not args.model:
            raise SystemExit(
                "--benchmark gsm8k requires --model <hf-model-name> "
                "(real inference backend; refusing to fabricate scores)."
            )
        backend = HFTransformersBackend(args.model)
        return GSM8KEvaluator(backend=backend, limit=args.limit,
                              data_path=args.data_path)
    return get_evaluator(args.benchmark)


def main():
    parser = argparse.ArgumentParser(
        description="Evolutionary Neural Substrate Search (ENSS)")
    parser.add_argument("--population", type=int, default=16)
    parser.add_argument("--generations", type=int, default=10)
    parser.add_argument("--benchmark", type=str, default="mock",
                        help="mock (CI only) | gsm8k")
    parser.add_argument("--model", type=str, default=None,
                        help="HF model name for the gsm8k inference backend")
    parser.add_argument("--limit", type=int, default=None,
                        help="cap on benchmark problems")
    parser.add_argument("--data-path", type=str, default=None,
                        help="explicit benchmark JSONL path")
    parser.add_argument("--no-inheritance", action="store_true",
                        help="disable weight inheritance")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    search_space = SearchSpace()
    evaluator = build_evaluator(args)
    controller = EvolutionController(
        search_space,
        evaluator,
        population_size=args.population,
        generations=args.generations,
        seed=args.seed,
        use_inheritance=not args.no_inheritance,
    )

    print("ENSS - Evolutionary Neural Substrate Search (Phase-13)")
    print("Benchmark: %s | Population: %d | Generations: %d | Inheritance: %s"
          % (args.benchmark, args.population, args.generations,
             not args.no_inheritance))
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
    print("Inherited tensors transferred: %d" % controller.n_inherited_tensors)


if __name__ == "__main__":
    main()
