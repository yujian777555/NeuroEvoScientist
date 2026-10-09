"""F2 runner: single-shot SVAMP confirmation of the three locked configs.

Runs REF / B2 / B1 (frozen in v2_quality/fasttrack/baselines_f1.json) on the
FULL locked SVAMP test split (300 items) with Qwen2.5-1.5B-Instruct.

Hard rules (Planner F2 authorization):
- data via v2_quality.svamp_adapter.load_locked_test_rows() ONLY — the
  committed confirmation_lock.json is validated before any inference;
- calibration/memory bank comes from GSM8K TRAIN ONLY (same as V1/F1);
  SVAMP train is never read;
- isolated caches (caches/f2_*) and predictions (f2_results/); no V1 paths;
- ONE manifest covering all 3 cells: git sha, model revision, dataset shas,
  lock hash, adapter sha, cache identity, phenotype hash, seed, per-cell
  error count, GPU-second accounting, token totals;
- aggregate GPU-minute cap; on breach or cell failure: STOP + INCOMPLETE.
"""

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
import time
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from genome.structured import StructuredGenome
from evaluator.gsm8k import GSM8KEvaluator, extract_gsm8k_answer
from evaluator.memory import _effective_to_dict
from v2_quality.svamp_adapter import (load_locked_test_rows,
                                      to_prompt_question,
                                      extract_model_answer, score)

REPO = os.path.join(os.path.dirname(__file__), "..", "..")
FT = os.path.join(REPO, "v2_quality", "fasttrack")
RESULTS = os.path.join(FT, "f2_results")
MANIFEST = os.path.join(RESULTS, "run_manifest.json")
GSM8K_TRAIN = os.path.join(REPO, "data", "gsm8k", "train.jsonl")

CONFIGS = ["REF", "B2", "B1"]  # locked order: primary contrast REF vs B2 first


def _sha256_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _git_sha():
    env = os.environ.get("F2_GIT_SHA")
    if env:
        return env
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO).decode().strip()
    except Exception:
        return "unknown"


def _model_revision(default):
    """Best-effort: snapshot dir name in the offline HF cache."""
    hf = os.environ.get("HF_HOME")
    if hf:
        snap = os.path.join(hf, "hub",
                            "models--Qwen--Qwen2.5-1.5B-Instruct", "snapshots")
        if os.path.isdir(snap):
            entries = [d for d in os.listdir(snap) if not d.startswith(".")]
            if len(entries) == 1:
                return entries[0]
    return default


class SvampConfirmEval(GSM8KEvaluator):
    """GSM8K pipeline on locked SVAMP items (Body+Question prompts)."""

    BENCHMARK = "svamp_confirm"  # separate cache namespace from all V1/F1 keys

    def load_samples(self):
        if self._samples is None:
            rows = load_locked_test_rows()  # validates committed lock
            self._samples = [{"svamp_id": str(r["ID"]),
                              "question": to_prompt_question(r),
                              "answer": "#### %s" % (r["Answer"],)}
                             for r in rows]
        return self._samples

    def _write_predictions(self, samples, task_scores, genome, outputs=None):
        """Full raw completions (no truncation) + adapter cross-check."""
        os.makedirs(os.path.dirname(os.path.abspath(self.predictions_path)),
                    exist_ok=True)
        with open(self.predictions_path, "a", encoding="utf-8") as f:
            for i, (sample, correct) in enumerate(zip(samples, task_scores)):
                out = outputs[i] if outputs else None
                gold = extract_model_answer(sample["answer"])
                pred = extract_model_answer(out) if out is not None else None
                f.write(json.dumps({
                    "benchmark": "svamp",
                    "svamp_id": sample["svamp_id"],
                    "item_index": i,
                    "architecture": genome.describe(),
                    "model": getattr(self.backend, "model_name", "unknown"),
                    "genome": _effective_to_dict(genome, self.BENCHMARK),
                    "correct": correct,
                    "adapter_pred": pred,
                    "adapter_gold": gold,
                    "adapter_score": score(pred, gold),
                    "output": out,
                }) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--gpu-budget-min", type=float, default=55.0,
                        help="aggregate GPU-minute cap (F2 hard cap = 60)")
    args = parser.parse_args()

    random.seed(0)
    try:
        import torch
        torch.manual_seed(0)
    except ImportError:
        pass

    from evaluator.backends import QwenBackend
    backend = QwenBackend(args.model, device=args.device,
                          batch_size=args.batch_size)

    conf = json.load(open(os.path.join(FT, "baselines_f1.json"),
                          encoding="utf-8"))
    lock = json.load(open(os.path.join(FT, "confirmation_lock.json"),
                          encoding="utf-8"))
    common = conf["common"]

    os.makedirs(RESULTS, exist_ok=True)
    os.makedirs(os.path.join(FT, "caches"), exist_ok=True)

    manifest = {
        "stage": "F2",
        "git_sha": _git_sha(),
        "model": args.model,
        "model_revision": _model_revision(lock["model_revision"]),
        "dataset": lock["dataset"],
        "dataset_hf_revision": lock["hf_revision"],
        "dataset_files_sha256": lock["files"],
        "test_ids_sha256": lock["test_ids_sha256"],
        "n_items": lock["n_items"],
        "adapter_version": "svamp-adapter-v1",
        "adapter_source_sha256": _sha256_file(os.path.join(
            REPO, "v2_quality", "svamp_adapter.py")),
        "seed": 0,
        "cells": [],
        "aggregate_gpu_seconds": 0.0,
        "status": "RUNNING",
    }

    def flush():
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    flush()
    gpu_seconds = 0.0

    for name in CONFIGS:
        genome = StructuredGenome(**{**common,
                                     **conf["baselines"][name]}).normalize()
        phenotype = hashlib.sha256(json.dumps(
            _effective_to_dict(genome, "svamp_confirm"),
            sort_keys=True).encode()).hexdigest()
        cache_path = os.path.join(
            FT, "caches", "f2_svamp_%s_%s.json"
            % (os.path.basename(str(args.model)), name))
        pred_path = os.path.join(RESULTS, "predictions_f2_%s.jsonl" % name)

        cell = {"config": name, "phenotype_sha256": phenotype,
                "cache": os.path.basename(cache_path),
                "predictions": os.path.basename(pred_path),
                "seed": 0, "error_count": 0, "errors": []}
        t0 = time.time()
        try:
            ev = SvampConfirmEval(
                backend=backend, data_path=None,  # samples from locked rows
                calibration_path=GSM8K_TRAIN,   # GSM8K TRAIN ONLY
                cache_path=cache_path, predictions_path=pred_path)
            memory = ev.build_memory_bank(genome)
            metrics = ev.evaluate(genome, None, memory_controller=memory)
            wall = time.time() - t0

            # completion-token accounting from stored full completions
            completion_tokens = 0
            adapter_mismatch = 0
            n_done = 0
            with open(pred_path, encoding="utf-8") as f:
                for line in f:
                    rec = json.loads(line)
                    n_done += 1
                    if rec["output"]:
                        completion_tokens += len(backend._tokenizer(
                            rec["output"])["input_ids"])
                    if abs(rec["adapter_score"] - rec["correct"]) > 1e-9:
                        adapter_mismatch += 1

            cell.update({
                "n_items": n_done,
                "capability": metrics["capability"],
                "prompt_tokens_total": metrics.get("prompt_tokens_total"),
                "completion_tokens_total": completion_tokens,
                "latency_sec": metrics.get("latency_sec"),
                "wall_time_sec": wall,
                "adapter_scoring_mismatches": adapter_mismatch,
                "cached": wall < 1.0,
            })
            gpu_seconds += wall
            print("CELL_DONE %s cap=%.4f n=%d wall=%.1fs"
                  % (name, metrics["capability"], n_done, wall))
        except Exception:
            cell["error_count"] += 1
            cell["errors"].append(traceback.format_exc())
            manifest["cells"].append(cell)
            manifest["status"] = "INCOMPLETE"
            manifest["aggregate_gpu_seconds"] = gpu_seconds
            flush()
            print("CELL_FAIL %s — STOP (no partial averages)" % name)
            sys.exit(2)

        manifest["cells"].append(cell)
        manifest["aggregate_gpu_seconds"] = gpu_seconds
        flush()

        if gpu_seconds / 60.0 > args.gpu_budget_min:
            manifest["status"] = "INCOMPLETE_BUDGET"
            flush()
            print("BUDGET_STOP at %.1f min" % (gpu_seconds / 60.0))
            sys.exit(3)

    manifest["status"] = "COMPLETE"
    flush()
    print("F2_PROCESS_DONE aggregate_gpu_min=%.1f" % (gpu_seconds / 60.0))


if __name__ == "__main__":
    main()
