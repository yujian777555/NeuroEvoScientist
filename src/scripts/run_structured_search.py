"""Phase-20 structured cognitive co-design runner.

Runs the structured-genome search (local mutations, block crossover,
conditional genes, per-genome adaptation budgets) on a benchmark dev slice.

Usage (VM):
    python src/scripts/run_structured_search.py --method enss \
        --benchmark gsm8k --model Qwen/Qwen2.5-1.5B-Instruct \
        --device 0 --batch-size 32 --population 16 --generations 10 --seed 0

Methods: enss (structured evolution), random (diagnostic reference only —
no superiority claim; C3 closed), fixed_structured reps via --genome-json.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from genome.structured import StructuredGenome
from genome.structured_space import StructuredSearchSpace
from evaluator.experiment_logger import ExperimentLogger
from evolution.adaptation import AdaptationConfig
from evolution.controller import EvolutionController
from evolution.random_search import RandomSearchController
from evolution.structured_operators import (structured_crossover,
                                            structured_mutate)

_REPO = os.path.join(os.path.dirname(__file__), "..", "..")
_ADAPT_YAML = os.path.join(_REPO, "configs", "phase17_adaptation.yaml")

# dev slices per pre-registered protocol (configs/phase20_protocol.yaml)
DEV = {"gsm8k": {"start": 0, "limit": 100},
       "pubmedqa": {"start": 0, "limit": 100},
       "qasper": {"start": 0, "limit": 50}}


def build_evaluator(args):
    from evaluator.backends import QwenBackend, HFTransformersBackend
    kwargs = {"device": args.device, "batch_size": args.batch_size}
    backend = (QwenBackend(args.model, **kwargs)
               if "qwen" in args.model.lower()
               else HFTransformersBackend(args.model, **kwargs))
    rng = DEV[args.benchmark]
    cache_path = os.path.join(
        _REPO, "experiments",
        "eval_cache_p20_%s_%s_%s.json"
        % (args.benchmark, os.path.basename(str(args.model)), args.method))
    common = dict(
        backend=backend, start=rng["start"], limit=rng["limit"],
        cache_path=cache_path,
        disable_memory=(args.method == "no_memory"),
    )
    if args.benchmark == "gsm8k":
        from evaluator.gsm8k import GSM8KEvaluator
        return GSM8KEvaluator(data_path=args.data_path or None,
                              **common)
    if args.benchmark == "pubmedqa":
        from evaluator.pubmedqa import PubMedQAEvaluator
        return PubMedQAEvaluator(data_path=args.data_path or None, **common)
    from evaluator.qasper import QasperEvaluator
    return QasperEvaluator(data_path=args.data_path or None, **common)


def main():
    parser = argparse.ArgumentParser(description="Phase-20 structured search")
    parser.add_argument("--method", default="enss",
                        choices=["enss", "random", "no_memory"])
    parser.add_argument("--benchmark", default="gsm8k",
                        choices=["gsm8k", "pubmedqa", "qasper"])
    parser.add_argument("--model", required=True)
    parser.add_argument("--population", type=int, default=16)
    parser.add_argument("--generations", type=int, default=10)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--data-path", type=str, default=None)
    args = parser.parse_args()

    space = StructuredSearchSpace()
    evaluator = build_evaluator(args)
    adaptation = AdaptationConfig.from_yaml(_ADAPT_YAML)

    logger = ExperimentLogger(
        run_name="p20_%s_%s_%s_seed%d" % (args.method, args.benchmark,
                                          os.path.basename(args.model),
                                          args.seed),
        config={"method": args.method, "benchmark": args.benchmark,
                "model": args.model, "population": args.population,
                "generations": args.generations, "seed": args.seed,
                "schema": "phase20",
                "dev_slice": DEV[args.benchmark]},
    )

    if args.method == "random":
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
            use_inheritance=True, use_pareto=True,
            adaptation_config=adaptation,
            mutate_fn=structured_mutate,
            crossover_fn=structured_crossover,
        )

    best = controller.run(on_generation=logger.log_generation)
    logger.finalize(best)
    print("BEST:", best.genome.describe_full())
    print("fitness=%.4f cap=%.4f eff=%.4f" % (
        best.fitness, best.metrics["capability"], best.metrics["efficiency"]))
    print("STRUCTURED_DONE %s %s seed%d" % (args.method, args.benchmark,
                                          args.seed))


if __name__ == "__main__":
    main()
