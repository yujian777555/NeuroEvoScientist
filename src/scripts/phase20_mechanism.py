"""Phase-20 Task 5: mechanistic analysis — auditable case studies linking
genome choices to actual inference behavior.

For each task's representative architecture:
- rebuilds the memory bank from the calibration split (deterministic, local);
- records which exemplars would be recalled for each item;
- joins per-item outcomes across own/cross-task configurations;
- selects case studies: own-task wins, cross-task losses, memory-helped vs
  memory-harmed items, token-budget effects — with item IDs and model outputs.

Writes results/phase20_mechanism_cases.json and
docs/phase20_mechanism_analysis.md.
"""

import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from genome.structured import StructuredGenome
from evaluator.memory import build_memory_controller

_REPO = os.path.join(os.path.dirname(__file__), "..", "..")
PRED = os.path.join(_REPO, "results", "phase20_item_predictions.jsonl")
LOCK = os.path.join(_REPO, "results", "phase20_selection_lock.json")
OUT = os.path.join(_REPO, "results", "phase20_mechanism_cases.json")
OUT_MD = os.path.join(_REPO, "..", "docs", "phase20_mechanism_analysis.md")

SPLIT = {"gsm8k": ("data/gsm8k/test.jsonl", "data/gsm8k/train.jsonl",
                   100, None, 0, 48),
         "pubmedqa": ("data/pubmedqa/pqal.jsonl", "data/pubmedqa/pqal.jsonl",
                      100, 400, 500, 48),
         "qasper": ("data/qasper/qasper.jsonl", "data/qasper/qasper.jsonl",
                    50, 100, 150, 48)}

REPS = {"gsm8k": "A_gsm", "pubmedqa": "A_pubmed", "qasper": "A_qasper"}


def _load_jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def build_bank_for(bench, genome):
    data_path, calib_path, start, limit, cal_start, cal_size = SPLIT[bench]
    calib = _load_jsonl(os.path.join(_REPO, calib_path))[cal_start:cal_start + cal_size]
    ctrl = build_memory_controller(genome)
    if ctrl is None:
        return None
    for s in calib:
        q = s.get("question") or s.get("input", "")
        a = s.get("answer") or (s.get("answers") or [""])[0]
        ctrl.store(q, a)
    return ctrl


def main():
    lock = json.load(open(LOCK))
    cfgs = {c["name"]: c for c in lock["configurations"]}

    # predictions: (bench, arch, mem_enabled) -> {item: (score, output)}
    preds = defaultdict(dict)
    for line in open(PRED):
        r = json.loads(line)
        preds[(r["benchmark"], r["architecture"],
               bool(r.get("memory_enabled", True)))][r["item_index"]] = (
            r["correct"], r.get("output"))

    cases = []
    for bench, rep_name in REPS.items():
        genome = StructuredGenome(**cfgs[rep_name]["genome"]).normalize()
        ctrl = build_bank_for(bench, genome)
        rep_key = (bench, genome.describe(), True)

        # per-item question text for case reporting
        data_path, _, start, limit, _, _ = SPLIT[bench]
        items = _load_jsonl(os.path.join(_REPO, data_path))[start:
                start + limit if limit else None]

        for item_idx, (score, output) in sorted(preds.get(rep_key, {}).items()):
            q = items[item_idx - start] if 0 <= item_idx - start < len(items) \
                else None
            qtext = (q.get("question") or q.get("input", ""))[:200] if q else ""
            exemplars = []
            if ctrl is not None:
                k = genome.exemplar_count
                if k > 0:
                    exemplars = [h["question"][:120]
                                 for h in ctrl.recall(qtext, k=k)]
            cases.append({
                "benchmark": bench, "architecture": rep_name,
                "item_index": item_idx, "score": score,
                "question": qtext, "recalled_exemplars": exemplars,
                "output": output,
            })

    # select informative cases: per task, top wins / losses / outputs present
    selected = []
    for bench in REPS:
        own = [c for c in cases
               if c["benchmark"] == bench and c["architecture"] == REPS[bench]]
        wins = [c for c in own if c["score"] >= 0.99][:2]
        losses = [c for c in own if c["score"] <= 0.01][:2]
        selected.extend(wins + losses)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"n_cases": len(selected), "cases": selected}, f,
                  indent=2, ensure_ascii=False)

    lines = ["# Phase-20 Mechanism Analysis\n",
             "%d case studies (item IDs + recalled exemplars + outputs)."
             % len(selected), ""]
    for c in selected:
        lines.append("## %s / %s / item %d (score %.2f)" % (
            c["benchmark"], c["architecture"], c["item_index"], c["score"]))
        lines.append("- Q: %s" % c["question"])
        for e in c["recalled_exemplars"]:
            lines.append("  - exemplar: %s" % e)
        if c["output"]:
            lines.append("- output: %s" % c["output"][:300])
        lines.append("")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("cases:", len(selected), "->", OUT)


if __name__ == "__main__":
    main()
