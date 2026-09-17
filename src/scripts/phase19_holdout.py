"""Phase-19 holdout evaluation runner (frozen protocol).

Evaluates the locked Phase-18 configurations on genuinely untouched
held-out subsets, with per-item prediction logging for statistics:

- GSM8K:    test[100:1319]  (dev history test[0:100] excluded)
- PubMedQA: samples[100:500] (calibration remains samples[500:1000])

Configurations come from results/phase19_selection_lock.json — locked
before any holdout inference; no post-hoc substitution.

Usage (VM):
    python src/scripts/phase19_holdout.py --benchmark gsm8k \
        --model Qwen/Qwen2.5-1.5B-Instruct --device 0 --batch-size 32
"""

import argparse
import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from genome.architecture import ArchitectureGenome
from models.builder import build_agent
from evaluator.gsm8k import GSM8KEvaluator
from evaluator.pubmedqa import PubMedQAEvaluator
from evaluator.memory import build_memory_controller
from evolution.adaptation import AdaptationConfig, adapt_substrate

_REPO = os.path.join(os.path.dirname(__file__), "..", "..")
LOCK = os.path.join(_REPO, "results", "phase19_selection_lock.json")
RESULTS = os.path.join(_REPO, "results", "phase19_holdout_results.csv")
PREDICTIONS = os.path.join(_REPO, "results", "phase19_item_predictions.jsonl")

# Holdout ranges (Phase-19 Task 2)
HOLDOUT = {"gsm8k": {"start": 100, "limit": None},
           "pubmedqa": {"start": 100, "limit": 400}}


def _done_keys():
    if not os.path.exists(RESULTS):
        return set()
    with open(RESULTS) as f:
        return {tuple(r)[:3] for r in csv.reader(f) if r and r[0] != "config"}


def main():
    parser = argparse.ArgumentParser(description="Phase-19 holdout runner")
    parser.add_argument("--benchmark", required=True,
                        choices=["gsm8k", "pubmedqa"])
    parser.add_argument("--model", required=True)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--data-path", type=str, default=None)
    parser.add_argument("--calibration-path", type=str, default=None)
    args = parser.parse_args()

    lock = json.load(open(LOCK))
    configs = lock["configurations"]

    from evaluator.backends import QwenBackend, HFTransformersBackend
    if "qwen" in args.model.lower():
        backend = QwenBackend(args.model, device=args.device,
                              batch_size=args.batch_size)
    else:
        backend = HFTransformersBackend(args.model, device=args.device,
                                        batch_size=args.batch_size)

    rng_holdout = HOLDOUT[args.benchmark]
    model_tag = os.path.basename(str(args.model))
    done = _done_keys()

    for cfg in configs:
        name = cfg["name"]
        key = (name, args.benchmark, model_tag)
        if key in done:
            print("skip (done):", key)
            continue

        genome = ArchitectureGenome(**cfg["genome"])
        disable_memory = cfg.get("disable_memory", False)

        cls = GSM8KEvaluator if args.benchmark == "gsm8k" \
            else PubMedQAEvaluator
        evaluator = cls(
            backend=backend,
            start=rng_holdout["start"], limit=rng_holdout["limit"],
            data_path=args.data_path,
            calibration_path=args.calibration_path,
            cache_path=os.path.join(
                _REPO, "experiments",
                "eval_cache_phase19_%s_%s_%s.json"
                % (args.benchmark, model_tag, name.replace(" ", "_"))),
            disable_memory=disable_memory,
            predictions_path=PREDICTIONS,
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
        new = not os.path.exists(RESULTS)
        with open(RESULTS, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["config", "benchmark", "model", "architecture",
                            "capability", "efficiency", "adaptability",
                            "prompt_tokens_total", "latency_sec",
                            "wall_time_sec", "adaptation_post_loss"])
            w.writerow(row)
        print("done:", key, "cap=%.4f" % metrics["capability"])

    print("HOLDOUT_RUN_DONE", args.benchmark, model_tag)


if __name__ == "__main__":
    main()
