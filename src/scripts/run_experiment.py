"""Phase-14 experiment runner: baseline matrix + ablations.

Methods:
    fixed        fixed hand-designed architectures (attention/mamba/hybrid
                 memory, direct reasoning, no compression)
    random       random search ("w/o Evolution" baseline)
    enss         full ENSS (Pareto selection + weight inheritance)
    no_pareto    evolution with scalar-fitness selection ("w/o NSGA Pareto")
    no_inherit   ENSS without weight inheritance
    no_mamba     ENSS with mamba removed from the search space

Examples:
    # single run
    python src/scripts/run_experiment.py --method enss --benchmark gsm8k \
        --model Qwen/Qwen2.5-1.5B-Instruct --population 32 --generations 20

    # full baseline matrix (A800 paper run)
    python src/scripts/run_experiment.py --matrix --benchmark gsm8k \
        --model Qwen/Qwen2.5-1.5B-Instruct --population 32 --generations 20

Every run logs to experiments/<run_name>/{history.jsonl, results.json}.
"""

import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from genome.architecture import ArchitectureGenome
from genome.search_space import SearchSpace
from models.builder import build_agent
from evaluator.experiment_logger import ExperimentLogger
from evolution.controller import EvolutionController
from evolution.fitness import calculate_fitness
from evolution.random_search import RandomSearchController

FIXED_BASELINES = {
    "fixed_attention": ArchitectureGenome(memory="attention"),
    "fixed_mamba": ArchitectureGenome(memory="mamba"),
    "fixed_hybrid": ArchitectureGenome(memory="hybrid"),
}

MATRIX_METHODS = ["fixed_attention", "fixed_mamba", "fixed_hybrid",
                  "random", "no_pareto", "enss"]


def build_evaluator(args, method):
    if args.benchmark == "gsm8k":
        from evaluator.gsm8k import GSM8KEvaluator
        from evaluator.backends import QwenBackend, HFTransformersBackend
        if not args.model:
            raise SystemExit(
                "--benchmark gsm8k requires --model <hf-model-name> "
                "(real inference backend; refusing to fabricate scores)."
            )
        kwargs = {"device": args.device, "batch_size": args.batch_size}
        if "qwen" in args.model.lower():
            backend = QwenBackend(args.model, **kwargs)
        else:
            backend = HFTransformersBackend(args.model, **kwargs)
        model_tag = os.path.basename(str(args.model))
        # Per-method cache file: matrix methods run as separate processes
        # (often on different GPUs), a shared JSON would race.
        cache_path = os.path.join(
            "experiments",
            "eval_cache_gsm8k_%s_%s_limit%s_seed%d.json"
            % (model_tag, method, args.limit, args.seed))
        return GSM8KEvaluator(backend=backend, limit=args.limit,
                              data_path=args.data_path,
                              cache_path=cache_path)
    from evaluator.benchmark import get_evaluator
    return get_evaluator(args.benchmark)


def run_fixed(genome, evaluator, weights, logger):
    agent = build_agent(genome)
    metrics = evaluator.evaluate(genome, agent)
    from evolution.controller import EvaluatedAgent
    best = EvaluatedAgent(genome, metrics,
                          calculate_fitness(metrics, weights))
    logger.log_generation(1, [best])
    logger.finalize(best)
    return best


def run_method(method, args, evaluator, weights):
    logger = ExperimentLogger(
        run_name="%s_%s_seed%d" % (method, args.benchmark, args.seed),
        config={"method": method, "benchmark": args.benchmark,
                "model": args.model, "population": args.population,
                "generations": args.generations, "seed": args.seed,
                "limit": args.limit},
    )

    if method in FIXED_BASELINES:
        return run_fixed(FIXED_BASELINES[method], evaluator, weights, logger)

    exclude = {"memory": ["mamba"]} if method == "no_mamba" else None
    space = SearchSpace(exclude=exclude)

    if method == "random":
        controller = RandomSearchController(
            space, evaluator, population_size=args.population,
            generations=args.generations, seed=args.seed)
    else:
        controller = EvolutionController(
            space, evaluator,
            population_size=args.population,
            generations=args.generations,
            seed=args.seed,
            use_inheritance=(method != "no_inherit"),
            use_pareto=(method != "no_pareto"),
        )

    def log(gen, evaluated):
        logger.log_generation(gen, evaluated)

    best = controller.run(on_generation=log)
    logger.finalize(best)
    return best


def write_matrix_table(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["method", "best_architecture", "fitness",
                         "capability", "efficiency", "adaptability"])
        for method, best in rows:
            writer.writerow([
                method, best.genome.describe(), "%.4f" % best.fitness,
                "%.4f" % best.metrics["capability"],
                "%.4f" % best.metrics["efficiency"],
                "%.4f" % best.metrics["adaptability"],
            ])


def main():
    parser = argparse.ArgumentParser(
        description="ENSS Phase-14 experiment runner")
    parser.add_argument("--method", type=str, default="enss",
                        choices=["fixed", "random", "enss", "no_pareto",
                                 "no_inherit", "no_mamba"]
                        + sorted(FIXED_BASELINES))
    parser.add_argument("--matrix", action="store_true",
                        help="run the full Phase-14 baseline matrix")
    parser.add_argument("--benchmark", type=str, default="mock")
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--population", type=int, default=16)
    parser.add_argument("--generations", type=int, default=10)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--data-path", type=str, default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", type=int, default=0,
                        help="GPU index within CUDA_VISIBLE_DEVICES "
                             "(pin the physical card via the env var)")
    parser.add_argument("--batch-size", type=int, default=16,
                        help="batched inference size for real backends")
    args = parser.parse_args()

    evaluator = build_evaluator(args, args.method)
    weights = SearchSpace().objective_weights

    methods = MATRIX_METHODS if args.matrix else [args.method]
    rows = []
    for method in methods:
        print(">>> method=%s benchmark=%s" % (method, args.benchmark))
        if args.matrix:
            evaluator = build_evaluator(args, method)
        best = run_method(method, args, evaluator, weights)
        print("    best: %s | fitness=%.4f\n"
              % (best.genome.describe(), best.fitness))
        rows.append((method, best))

    if args.matrix:
        table_path = os.path.join("experiments", "baseline_matrix_%s_seed%d.csv"
                                  % (args.benchmark, args.seed))
        write_matrix_table(rows, table_path)
        print("matrix table written to %s" % table_path)


if __name__ == "__main__":
    main()
