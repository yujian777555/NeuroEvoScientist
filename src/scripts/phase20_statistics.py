"""Phase-20 statistics: paired bootstrap + McNemar on structured-genome
holdout predictions, keyed by (benchmark, model, architecture,
memory_enabled).

Key comparisons (per benchmark, per backbone):
- own-task representative vs each cross-task representative
- representative vs no_memory
- representative vs strongest fixed baseline
- 7B vs 1.5B for each representative (identical items)

Writes results/phase20_statistics.json plus cross-task/backbone CSVs.
"""

import csv
import json
import os
import random
from collections import defaultdict
from math import comb

_REPO = os.path.join(os.path.dirname(__file__), "..", "..")
PRED = os.path.join(_REPO, "results", "phase20_item_predictions.jsonl")
HOLDOUT = os.path.join(_REPO, "results", "phase20_holdout_results.csv")
OUT_STATS = os.path.join(_REPO, "results", "phase20_statistics.json")
OUT_CROSS = os.path.join(_REPO, "results", "phase20_task_transfer.csv")
OUT_BACKBONE = os.path.join(_REPO, "results", "phase20_backbone_transfer.csv")

BOOT_N = 10000
BOOT_SEED = 20260923


def load_predictions():
    """(bench, model, arch, mem_enabled) -> {item_index: score}"""
    table = defaultdict(dict)
    for line in open(PRED):
        r = json.loads(line)
        key = (r["benchmark"], r.get("model", ""), r["architecture"],
               bool(r.get("memory_enabled", True)))
        table[key][r["item_index"]] = r["correct"]
    return table


def paired_bootstrap(a, b, n=BOOT_N, seed=BOOT_SEED):
    rng = random.Random(seed)
    items = sorted(set(a) & set(b))
    if not items:
        return None
    diffs = [a[i] - b[i] for i in items]
    means = []
    for _ in range(n):
        sample = [diffs[rng.randrange(len(diffs))] for _ in diffs]
        means.append(sum(sample) / len(sample))
    means.sort()
    acc_a = sum(a[i] for i in items) / len(items)
    acc_b = sum(b[i] for i in items) / len(items)
    return {"n_items": len(items), "score_a": round(acc_a, 4),
            "score_b": round(acc_b, 4),
            "diff_pp": round(100 * (acc_a - acc_b), 2),
            "ci95_lo_pp": round(100 * means[int(0.025 * n)], 2),
            "ci95_hi_pp": round(100 * means[int(0.975 * n)], 2)}


def mcnemar(a, b):
    items = sorted(set(a) & set(b))
    aw = sum(1 for i in items if a[i] > b[i])
    bw = sum(1 for i in items if a[i] < b[i])
    n = aw + bw
    if n == 0:
        return {"discordant": 0, "a_wins": 0, "b_wins": 0, "p_exact": 1.0}
    k = min(aw, bw)
    p = 2 * sum(comb(n, i) for i in range(k + 1)) * (0.5 ** n)
    return {"discordant": n, "a_wins": aw, "b_wins": bw,
            "p_exact": round(min(1.0, p), 6)}


def _find(table, bench, model, arch, mem=True):
    return table.get((bench, model, arch, mem))


def main():
    table = load_predictions()
    results = {}

    reps = {"gsm8k": "Recency + Cot + Full + Fp16",
            "pubmedqa": "None + Direct + Full + Fp16",
            "qasper": "Retrieval + Direct + Truncated + Fp16"}

    for bench, rep in reps.items():
        others = [r for b2, r in reps.items() if b2 != bench]
        for model in ("Qwen2.5-1.5B-Instruct", "Qwen2.5-7B-Instruct"):
            for other in others:
                a = _find(table, bench, model, rep)
                b = _find(table, bench, model, other)
                if a and b:
                    results["%s|%s|own vs %s" % (bench, model.split("-")[1],
                                                 other)] = {
                        "bootstrap": paired_bootstrap(a, b),
                        "mcnemar": mcnemar(a, b),
                    }
            # rep vs no_memory (same arch as rep where possible)
            nm = table.get((bench, model, rep, False))
            a = _find(table, bench, model, rep)
            if a and nm:
                results["%s|%s|own vs no_memory" % (bench,
                        model.split("-")[1])] = {
                    "bootstrap": paired_bootstrap(a, nm),
                    "mcnemar": mcnemar(a, nm),
                }

    with open(OUT_STATS, "w") as f:
        json.dump(results, f, indent=2)

    rows = list(csv.DictReader(open(HOLDOUT)))
    with open(OUT_CROSS, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        benches = sorted({r["benchmark"] for r in rows})
        w.writerow(["config"] + benches)
        for cfg in sorted({r["config"] for r in rows}):
            row = [cfg]
            for bench in benches:
                hit = [r for r in rows if r["config"] == cfg
                       and r["benchmark"] == bench and "1.5B" in r["model"]]
                row.append(hit[0]["capability"] if hit else "")
            w.writerow(row)

    with open(OUT_BACKBONE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["config", "benchmark", "cap_1.5B", "cap_7B", "delta_pp"])
        for cfg in sorted({(r["config"], r["benchmark"]) for r in rows}):
            rs = [r for r in rows if (r["config"], r["benchmark"]) == cfg]
            a = [r for r in rs if "1.5B" in r["model"]]
            b = [r for r in rs if "7B" in r["model"]]
            if a and b:
                w.writerow([cfg[0], cfg[1], a[0]["capability"],
                            b[0]["capability"],
                            "%.2f" % (100 * (float(b[0]["capability"])
                                             - float(a[0]["capability"])))])

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
