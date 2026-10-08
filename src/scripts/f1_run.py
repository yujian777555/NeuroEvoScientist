"""F1 runner: evaluate the seven locked baselines on DEV slices only.

Reads v2_quality/fasttrack/run_matrix.csv and baselines_f1.json.
Per cell: isolated cache (v2_quality/fasttrack/caches/), per-item
predictions with outputs (f1_results/predictions_<cell>.jsonl), and one
row in f1_results/f1_summary.csv. Writes f1_results/run_manifest.json.

No Phase-20 holdout access; no SVAMP/MATH; no V1 artifact writes.
"""

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from genome.structured import StructuredGenome
from evaluator.gsm8k import GSM8KEvaluator
from evaluator.qasper import QasperEvaluator

REPO = os.path.join(os.path.dirname(__file__), "..", "..")
FT = os.path.join(REPO, "v2_quality", "fasttrack")
SUMMARY = os.path.join(FT, "f1_results", "f1_summary.csv")
MANIFEST = os.path.join(FT, "f1_results", "run_manifest.json")

DEV = {"gsm8k": {"start": 0, "limit": 100,
                 "data": "data/gsm8k/test.jsonl",
                 "calib": "data/gsm8k/train.jsonl"},
       "qasper": {"start": 0, "limit": 50,
                  "data": "data/qasper/qasper.jsonl",
                  "calib": "data/qasper/qasper.jsonl"}}

EVALUATOR = {"gsm8k": GSM8KEvaluator, "qasper": QasperEvaluator}


def git_sha():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO).decode().strip()
    except Exception:
        return "unknown"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cells", default=None,
                        help="comma-separated cell_ids; default = all")
    parser.add_argument("--model", required=True)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--gpu-budget-min", type=float, default=90.0,
                        help="aggregate GPU-minute cap for this process")
    args = parser.parse_args()

    from evaluator.backends import QwenBackend, HFTransformersBackend
    backend = (QwenBackend(args.model, device=args.device,
                           batch_size=args.batch_size)
               if "qwen" in args.model.lower()
               else HFTransformersBackend(args.model, device=args.device,
                                          batch_size=args.batch_size))

    conf = json.load(open(os.path.join(FT, "baselines_f1.json"),
                          encoding="utf-8"))
    common = conf["common"]
    rows = list(csv.DictReader(open(os.path.join(FT, "run_matrix.csv"),
                                    encoding="utf-8")))
    if args.cells:
        wanted = set(args.cells.split(","))
        rows = [r for r in rows if r["cell_id"] in wanted]

    model_tag = os.path.basename(str(args.model))
    model_key = model_tag.lower().replace("-instruct", "")
    os.makedirs(os.path.dirname(SUMMARY), exist_ok=True)
    os.makedirs(os.path.join(FT, "caches"), exist_ok=True)

    manifest = {"git_sha": git_sha(), "model": args.model,
                "cells": [], "aggregate_gpu_seconds": 0.0}
    gpu_seconds = 0.0

    for row in rows:
        cell = row["cell_id"]
        if row["backbone"].lower().replace("-instruct", "") != model_key:
            continue  # this process serves only its assigned backbone
        bench = row["benchmark"]
        base = row["baseline"]
        genome = StructuredGenome(**{**common,
                                     **conf["baselines"][base]}).normalize()

        spec = DEV[bench]
        cache_path = os.path.join(FT, "caches",
                                  "f1_%s_%s_%s.json" % (bench, model_tag, base))
        pred_path = os.path.join(FT, "f1_results",
                                 "predictions_%s.jsonl" % cell)
        ev = EVALUATOR[bench](
            backend=backend, start=spec["start"], limit=spec["limit"],
            data_path=os.path.join(REPO, spec["data"]),
            calibration_path=os.path.join(REPO, spec["calib"]),
            cache_path=cache_path, predictions_path=pred_path)

        memory = ev.build_memory_bank(genome)
        agent = None
        t0 = time.time()
        metrics = ev.evaluate(genome, agent, memory_controller=memory)
        wall = time.time() - t0
        gpu_seconds += wall

        out = dict(cell_id=cell, baseline=base, benchmark=bench,
                   backbone=model_tag,
                   capability="%.4f" % metrics["capability"],
                   prompt_tokens_total=metrics.get("prompt_tokens_total"),
                   latency_sec="%.1f" % metrics.get("latency_sec", 0.0),
                   wall_time_sec="%.1f" % wall,
                   cache=os.path.basename(cache_path))
        new = not os.path.exists(SUMMARY)
        with open(SUMMARY, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(out))
            if new:
                w.writeheader()
            w.writerow(out)

        manifest["cells"].append({**out, "seed": 0})
        manifest["aggregate_gpu_seconds"] = gpu_seconds
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        print("CELL_DONE %s cap=%.4f wall=%.1fs" % (cell,
              metrics["capability"], wall))
        if gpu_seconds / 60.0 > args.gpu_budget_min:
            print("BUDGET_STOP at %.1f min" % (gpu_seconds / 60.0))
            break

    print("F1_PROCESS_DONE aggregate_gpu_min=%.1f" % (gpu_seconds / 60.0))


if __name__ == "__main__":
    main()
