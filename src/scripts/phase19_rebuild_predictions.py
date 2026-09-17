"""Rebuild Phase-19 per-item predictions from eval caches (with model +
memory fields), replacing the ambiguous first-pass predictions file.

Cache entries (written during holdout runs) carry item_scores; item indices
are deterministic from (benchmark, start, limit).
"""

import glob
import json
import os
import re

CACHE_DIR = "/tmp/p19_cache"  # will be overridden by argv
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "results",
                   "phase19_item_predictions.jsonl")

HOLDOUT = {"gsm8k": (100, 1219), "pubmedqa": (100, 400)}


def main(cache_dir):
    rows = []
    for path in sorted(glob.glob(os.path.join(cache_dir, "*.json"))):
        base = os.path.basename(path)
        m = re.match(r"eval_cache_phase19_(\w+?)_((?:Qwen2\.5-[\d.]+B-Instruct))_(.+)\.json",
                     base)
        if not m:
            continue
        bench, model, config = m.groups()
        start, n = HOLDOUT[bench]
        cache = json.load(open(path))
        for entry in cache.values():
            scores = entry.get("item_scores")
            if not scores:
                continue
            arch = None  # genome not stored in entry; use config name
            for i, c in enumerate(scores[:n]):
                rows.append({
                    "benchmark": bench,
                    "model": model,
                    "config": config,
                    "memory_enabled": entry.get("memory_enabled", True),
                    "item_index": start + i,
                    "correct": c,
                })

    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print("rows:", len(rows), "->", OUT)


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else CACHE_DIR)
