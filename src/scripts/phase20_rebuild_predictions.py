"""Rebuild Phase-20 per-item predictions from eval caches (model/config/
memory_enabled included), replacing the ambiguous first-pass file."""

import glob
import json
import os
import re

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "results",
                   "phase20_item_predictions.jsonl")

HOLDOUT_N = {"gsm8k": (100, 1219), "pubmedqa": (100, 400),
             "qasper": (50, 100)}


def main(cache_dir):
    rows = []
    for path in sorted(glob.glob(os.path.join(cache_dir, "*.json"))):
        base = os.path.basename(path)
        m = re.match(
            r"eval_cache_phase20_(\w+?)_(Qwen2\.5-[\d.]+B-Instruct)_(.+)\.json",
            base)
        if not m:
            continue
        bench, model, config = m.groups()
        start, n = HOLDOUT_N[bench]
        cache = json.load(open(path))
        for entry in cache.values():
            scores = entry.get("item_scores")
            if not scores:
                continue
            for i, c in enumerate(scores[:n]):
                rows.append({"benchmark": bench, "model": model,
                             "config": config,
                             "memory_enabled": entry.get("memory_enabled",
                                                         True),
                             "item_index": start + i, "correct": c})
    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print("rows:", len(rows), "->", OUT)


if __name__ == "__main__":
    import sys
    main(sys.argv[1])
