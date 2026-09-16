"""Phase-17 focused experiment runner (corrected schema).

Methods (plans/phase17_plan.md Task 5 minimum comparisons):
    enss           full ENSS: real Mamba2 substrate + inheritance + adaptation
    no_inherit     ENSS with scratch-init substrates (same adaptation budget)
    no_mamba2      ENSS with the mamba2 gene removed from the search space
    random         random search, equal evaluation + adaptation budget
    fixed_retrieval / fixed_recency / fixed_mamba2   fixed memory baselines
    no_pareto / no_memory                            extra ablations

Examples:
    # focused GSM8K validation (one seed)
    python src/scripts/run_experiment.py --method enss --benchmark gsm8k \
        --model Qwen/Qwen2.5-1.5B-Instruct --population 16 --generations 10 \
        --seed 0

Every run logs to experiments/<run_name>/{history.jsonl, results.json}.
"""

import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from genome.architecture import ArchitectureGenome
from genome.search_space import SearchSpace
from models.builder import build_agent
from evaluator.experiment_logger import ExperimentLogger
from evolution.adaptation import AdaptationConfig
from evolution.controller import EvolutionController
from evolution.fitness import calculate_fitness
from evolution.random_search import RandomSearchController

_ADAPT_YAML = os.path.join(os.path.dirname(__file__), "..", "..",
                           "configs", "phase17_adaptation.yaml")

FIXED_BASELINES = {
    "fixed_recency": ArchitectureGenome(memory="recency"),
    "fixed_retrieval": ArchitectureGenome(memory="retrieval"),
    "fixed_mamba2": ArchitectureGenome(memory="mamba2"),
    "fixed_hybrid": ArchitectureGenome(memory="hybrid"),
}

MATRIX_METHODS = ["fixed_recency", "fixed_retrieval", "fixed_mamba2",
                  "random", "no_inherit", "enss", "no_mamba2"]


def build_evaluator(args, method):
    if args.benchmark in ("gsm8k", "pubmedqa"):
        from evaluator.gsm8k import GSM8KEvaluator
        from evaluator.pubmedqa import PubMedQAEvaluator
        from evaluator.backends import QwenBackend, HFTransformersBackend
        if not args.model:
            raise SystemExit(
                "--benchmark %s requires --model <hf-model-name> "
                "(real inference backend; refusing to fabricate scores)."
                % args.benchmark
            )
        kwargs = {"device": args.device, "batch_size": args.batch_size}
        if "qwen" in args.model.lower():
            backend = QwenBackend(args.model, **kwargs)
        else:
            backend = HFTransformersBackend(args.model, **kwargs)
        model_tag = os.path.basename(str(args.model))
        # Per-method cache file shared ACROSS SEEDS where fingerprints match:
        # same-method runs are sequential in the card queue, so no race.
        cache_path = os.path.join(
            "experiments",
            "eval_cache_%s_%s_%s_limit%s.json"
            % (args.benchmark, model_tag, method, args.limit))
        cls = GSM8KEvaluator if args.benchmark == "gsm8k" \
            else PubMedQAEvaluator
        return cls(backend=backend, limit=args.limit,
                   data_path=args.data_path, cache_path=cache_path,
                   disable_memory=(method == "no_memory"))
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


def run_landscape(args, evaluator):
    """Phase-18 Task 2: exhaustive evaluation of every architecture.

    One deterministic evaluation per genome (adaptation included where the
    substrate is trainable), written as JSONL rows with raw objectives.
    This table is an analysis oracle, not a search method.
    """
    import json
    import time
    from evolution.adaptation import adapt_substrate
    from evolution.controller import (genome_signature,
                                      substrate_fingerprint)
    import hashlib
    import torch

    space = SearchSpace()
    adaptation = AdaptationConfig.from_yaml(_ADAPT_YAML)
    out_dir = os.path.join("experiments",
                           "landscape_%s" % args.benchmark)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "landscape.jsonl")

    done = set()
    if os.path.exists(out_path):
        with open(out_path) as f:
            for line in f:
                done.add(json.loads(line)["architecture_id"])
    combos = space.enumerate_architectures()
    print("landscape: %d architectures, %d already done"
          % (len(combos), len(done)))

    with open(out_path, "a", encoding="utf-8") as f:
        for combo in combos:
            genome = ArchitectureGenome(**combo)
            arch_id = genome_signature(genome)
            if arch_id in done:
                continue
            torch.manual_seed(
                int(hashlib.sha256(arch_id.encode()).hexdigest(),
                    16) % (2 ** 32))

            memory = None
            if not getattr(evaluator, "disable_memory", False):
                memory = evaluator.build_memory_bank(genome)
            substrate = getattr(memory, "substrate", None)
            fingerprint = None
            adaptation_record = {"trainable": False}
            if substrate is not None:
                adaptation_record = adapt_substrate(
                    memory, evaluator.calibration_samples(), adaptation)
                fingerprint = substrate_fingerprint(substrate)

            agent = build_agent(genome)
            start = time.time()
            metrics = evaluator.evaluate(
                genome, agent, memory_controller=memory,
                substrate_fingerprint=fingerprint)
            row = {
                "benchmark": args.benchmark,
                "architecture_id": arch_id,
                "genome": genome.to_dict(),
                "architecture": genome.describe(),
                "capability": metrics["capability"],
                "efficiency": metrics["efficiency"],
                "adaptability": metrics["adaptability"],
                "prompt_tokens_total": metrics.get("prompt_tokens_total"),
                "latency_sec": metrics.get("latency_sec"),
                "trainable_params": adaptation_record.get("trainable_params",
                                                          0),
                "adaptation_wall_time_sec":
                    adaptation_record.get("wall_time_sec", 0.0),
                "total_wall_time_sec": time.time() - start,
            }
            f.write(json.dumps(row) + "\n")
            f.flush()
            os.fsync(f.fileno())
            print("  [%d/%d] %s cap=%.3f" % (len(done) + 1, len(combos),
                                             genome.describe(),
                                             row["capability"]))
            done.add(arch_id)
    print("LANDSCAPE_DONE %s" % out_path)


def run_method(method, args, evaluator, weights):
    logger = ExperimentLogger(
        run_name="%s_%s_seed%d" % (method, args.benchmark, args.seed),
        config={"method": method, "benchmark": args.benchmark,
                "model": args.model, "population": args.population,
                "generations": args.generations, "seed": args.seed,
                "limit": args.limit, "schema": "phase17",
                "adaptation": "phase17_adaptation.yaml"},
    )

    if method in FIXED_BASELINES:
        return run_fixed(FIXED_BASELINES[method], evaluator, weights, logger)

    exclude = {"memory": ["mamba2"]} if method == "no_mamba2" else None
    space = SearchSpace(exclude=exclude)

    # Phase-17: every candidate gets the same fixed adaptation budget.
    adaptation = AdaptationConfig.from_yaml(_ADAPT_YAML)

    if method == "random":
        controller = RandomSearchController(
            space, evaluator, population_size=args.population,
            generations=args.generations, seed=args.seed,
            adaptation_config=adaptation)
    else:
        controller = EvolutionController(
            space, evaluator,
            population_size=args.population,
            generations=args.generations,
            seed=args.seed,
            use_inheritance=(method != "no_inherit"),
            use_pareto=(method != "no_pareto"),
            adaptation_config=adaptation,
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
        description="ENSS Phase-17 focused experiment runner")
    parser.add_argument("--method", type=str, default="enss",
                        choices=["random", "enss", "no_pareto", "no_inherit",
                                 "no_mamba2", "no_memory"]
                        + sorted(FIXED_BASELINES))
    parser.add_argument("--matrix", action="store_true")
    parser.add_argument("--landscape", action="store_true",
                        help="Phase-18: exhaustively evaluate all "
                             "architectures (analysis oracle)")
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

    if args.landscape:
        evaluator = build_evaluator(args, "landscape")
        run_landscape(args, evaluator)
        return

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
