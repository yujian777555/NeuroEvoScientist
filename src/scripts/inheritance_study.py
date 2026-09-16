"""Phase-18 Task 4: paired weight-inheritance study (adequately sized).

For each pair i:
- child genome: mamba2 memory + sampled reasoning/context_policy;
- INHERITED init: substrate weights copied from an adapted parent substrate;
- SCRATCH init: deterministic fresh init (seeded by genome hash);
- identical calibration data / optimizer / lr / adaptation steps / eval set.

Recorded per side: pre/post adaptation loss, pre/post capability,
wall-clock. Output: results/phase18_inheritance_pairs.csv
(+ raw JSON alongside), enabling paired statistics / bootstrap CIs.
"""

import argparse
import csv
import hashlib
import json
import os
import random
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import torch

from genome.architecture import ArchitectureGenome
from genome.search_space import SearchSpace
from models.builder import build_agent
from evaluator.gsm8k import GSM8KEvaluator
from evaluator.memory import build_memory_controller
from evolution.adaptation import AdaptationConfig, adapt_substrate
from evolution.controller import genome_signature, substrate_fingerprint


def _seeded_init(genome):
    torch.manual_seed(
        int(hashlib.sha256(genome_signature(genome).encode()).hexdigest(),
            16) % (2 ** 32))


def _evaluate_with_substrate(evaluator, genome, memory):
    substrate = getattr(memory, "substrate", None)
    fp = substrate_fingerprint(substrate) if substrate is not None else None
    agent = build_agent(genome)
    return evaluator.evaluate(genome, agent, memory_controller=memory,
                              substrate_fingerprint=fp)


def run_pair(evaluator, genome, parent_state, config, calib):
    """One matched pair: inherited vs scratch, identical budget."""
    row = {"genome": genome_signature(genome),
           "architecture": genome.describe()}

    for side, init_state in (("inherited", parent_state),
                             ("scratch", None)):
        memory = build_memory_controller(genome)
        _seeded_init(genome)
        if init_state is not None:
            memory.substrate.load_state_dict(
                {k: v.clone() for k, v in init_state.items()})
        memory.invalidate_state_cache()

        # pre-adaptation capability (unadapted substrate in place)
        pre_metrics = _evaluate_with_substrate(evaluator, genome, memory)

        record = adapt_substrate(memory, calib, config)

        # post-adaptation capability
        post_metrics = _evaluate_with_substrate(evaluator, genome, memory)

        row["%s_pre_loss" % side] = record["pre_loss"]
        row["%s_post_loss" % side] = record["post_loss"]
        row["%s_pre_capability" % side] = pre_metrics["capability"]
        row["%s_post_capability" % side] = post_metrics["capability"]
        row["%s_wall_clock" % side] = record["wall_time_sec"]
    return row


def main():
    parser = argparse.ArgumentParser(description="Phase-18 inheritance study")
    parser.add_argument("--pairs", type=int, default=20)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--device", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--data-path", type=str, default=None)
    parser.add_argument("--calibration-path", type=str, default=None)
    parser.add_argument("--out", type=str, default=os.path.join(
        "results", "phase18_inheritance_pairs.csv"))
    args = parser.parse_args()

    from evaluator.backends import QwenBackend, HFTransformersBackend
    if "qwen" in args.model.lower():
        backend = QwenBackend(args.model, device=args.device,
                              batch_size=args.batch_size)
    else:
        backend = HFTransformersBackend(args.model, device=args.device,
                                        batch_size=args.batch_size)
    evaluator = GSM8KEvaluator(
        backend=backend, limit=args.limit, data_path=args.data_path,
        cache_path=os.path.join("experiments",
                                "eval_cache_inheritance_study.json"),
        calibration_path=args.calibration_path)

    config = AdaptationConfig.from_yaml(os.path.join(
        os.path.dirname(__file__), "..", "..", "configs",
        "phase17_adaptation.yaml"))
    calib = evaluator.calibration_samples()

    # Build 4 adapted "parent" substrates (different seeds -> diverse donors)
    print("preparing adapted parent substrates...")
    parents = []
    holder = ArchitectureGenome(memory="mamba2")
    for pseed in range(4):
        torch.manual_seed(1000 + pseed)
        mem = build_memory_controller(holder)  # same dims as any child
        adapt_substrate(mem, calib, config)
        parents.append({k: v.clone()
                        for k, v in mem.substrate.state_dict().items()})

    space = SearchSpace()
    rng = random.Random(20260918)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    rows = []
    for i in range(args.pairs):
        genome = ArchitectureGenome(
            memory="mamba2",
            reasoning=rng.choice(space.reasoning),
            context_policy=rng.choice(space.context_policy),
        )
        parent_state = parents[i % len(parents)]
        row = run_pair(evaluator, genome, parent_state, config, calib)
        row["pair_id"] = i
        rows.append(row)
        print("pair %d/%d done: inh_cap=%.3f scr_cap=%.3f"
              % (i + 1, args.pairs, row["inherited_post_capability"],
                 row["scratch_post_capability"]))

    fieldnames = ["pair_id", "genome", "architecture"] + [
        "%s_%s" % (side, k)
        for side in ("inherited", "scratch")
        for k in ("pre_loss", "post_loss", "pre_capability",
                  "post_capability", "wall_clock")
    ]
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    with open(args.out.replace(".csv", ".json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    print("PAIRS_DONE ->", args.out)


if __name__ == "__main__":
    main()
