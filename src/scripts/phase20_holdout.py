"""Phase-20 holdout evaluation runner (structured genomes, 3 benchmarks).

Evaluates the frozen per-task architectures (results/phase20_selection_lock.json,
locked BEFORE any holdout inference) on held-out subsets:

- GSM8K:    test[100:1319]
- PubMedQA: samples[100:500]
- QASPER:   items[50:150]   (pre-registered split)

Usage (VM):
    python src/scripts/phase20_holdout.py --benchmark qasper \
        --model Qwen/Qwen2.5-1.5B-Instruct --device 0 --batch-size 32
"""

import argparse
import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from genome.structured import StructuredGenome
from models.builder import build_agent
from evaluator.gsm8k import GSM8KEvaluator
from evaluator.pubmedqa import PubMedQAEvaluator
from evaluator.qasper import QasperEvaluator
from evolution.adaptation import AdaptationConfig, adapt_substrate

_REPO = os.path.join(os.path.dirname(__file__), "..", "..")
LOCK = os.path.join(_REPO, "results", "phase20_selection_lock.json")
RESULTS = os.path.join(_REPO, "results", "phase20_holdout_results.csv")
PREDICTIONS = os.path.join(_REPO, "results", "phase20_item_predictions.jsonl")

HOLDOUT = {"gsm8k": {"start": 100, "limit": None},
           "pubmedqa": {"start": 100, "limit": 400},
           "qasper": {"start": 50, "limit": 100}}


def _done_keys():
    if not os.path.exists(RESULTS):
        return set()
    with open(RESULTS) as f:
        return {tuple(r)[:3] for r in csv.reader(f) if r and r[0] != "config"}


def build_evaluator_cls(bench):
    return {"gsm8k": GSM8KEvaluator, "pubmedqa": PubMedQAEvaluator,
            "qasper": QasperEvaluator}[bench]


def main():
    parser = argparse.ArgumentParser(description="Phase-20 holdout runner")
    parser.add_argument("--benchmark", required=True,
                        choices=["gsm8k", "pubmedqa", "qasper"])
    parser.add_argument("--model", required=True)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--data-path", type=str, default=None)
    parser.add_argument("--calibration-path", type=str, default=None)
    parser.add_argument("--limit", type=int, default=None,
                        help="override holdout size (mechanism runs)")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--out-results", type=str, default=None)
    parser.add_argument("--out-predictions", type=str, default=None)
    parser.add_argument("--configs", type=str, default=None,
                        help="comma-separated subset of locked config names")
    parser.add_argument("--lock", type=str, default=None,
                        help="override selection lock path")
    args = parser.parse_args()

    lock = json.load(open(args.lock or LOCK))
    configs = lock["configurations"]
    if args.configs:
        wanted = set(args.configs.split(","))
        configs = [c for c in configs if c["name"] in wanted]

    from evaluator.backends import QwenBackend, HFTransformersBackend
    if "qwen" in args.model.lower():
        backend = QwenBackend(args.model, device=args.device,
                              batch_size=args.batch_size)
    else:
        backend = HFTransformersBackend(args.model, device=args.device,
                                        batch_size=args.batch_size)

    rng_holdout = HOLDOUT[args.benchmark]
    model_tag = os.path.basename(str(args.model))
    results_path = args.out_results or RESULTS
    predictions_path = args.out_predictions or PREDICTIONS
    if args.no_cache:
        done = set()
    else:
        done = _done_keys() if not args.out_results else (
            {tuple(r)[:3] for r in csv.reader(open(args.out_results))
             if r and r[0] != "config"}
            if os.path.exists(args.out_results) else set())

    for cfg in configs:
        name = cfg["name"]
        key = (name, args.benchmark, model_tag)
        if key in done:
            print("skip (done):", key)
            continue

        genome = StructuredGenome(**cfg["genome"]).normalize()
        disable_memory = cfg.get("disable_memory", False)

        cls = build_evaluator_cls(args.benchmark)
        evaluator = cls(
            backend=backend,
            start=rng_holdout["start"],
            limit=args.limit or rng_holdout["limit"],
            data_path=args.data_path,
            calibration_path=args.calibration_path,
            cache_path=None if args.no_cache else os.path.join(
                _REPO, "experiments",
                "eval_cache_phase20_%s_%s_%s.json"
                % (args.benchmark, model_tag, name.replace(" ", "_"))),
            disable_memory=disable_memory,
            predictions_path=predictions_path,
        )

        memory = None
        adaptation_record = {"trainable": False}
        if not disable_memory:
            memory = evaluator.build_memory_bank(genome)
            substrate = getattr(memory, "substrate", None)
            if substrate is not None:
                adaptation_record = adapt_substrate(
                    memory, evaluator.calibration_samples(),
                    AdaptationConfig.from_yaml(os.path.join(
                        _REPO, "configs", "phase17_adaptation.yaml")))
                memory.invalidate_state_cache()

        agent = build_agent(genome)
        t0 = time.time()
        metrics = evaluator.evaluate(genome, agent,
                                     memory_controller=memory)
        wall = time.time() - t0

        row = [name, args.benchmark, model_tag,
               genome.describe(),
               "%.4f" % metrics["capability"],
               "%.4f" % metrics["efficiency"],
               "%.4f" % metrics["adaptability"],
               metrics.get("prompt_tokens_total"),
               "%.1f" % metrics.get("latency_sec", 0.0),
               "%.1f" % wall,
               json.dumps(adaptation_record.get("post_loss"))]
        new = not os.path.exists(results_path)
        with open(results_path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["config", "benchmark", "model", "architecture",
                            "capability", "efficiency", "adaptability",
                            "prompt_tokens_total", "latency_sec",
                            "wall_time_sec", "adaptation_post_loss"])
            w.writerow(row)
        print("done:", key, "cap=%.4f" % metrics["capability"])

    print("P20_HOLDOUT_DONE", args.benchmark, model_tag)


if __name__ == "__main__":
    main()
