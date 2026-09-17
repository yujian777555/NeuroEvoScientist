"""Phase-19 Task 5: item-level paired statistics.

Reads results/phase19_item_predictions.jsonl (rebuilt from eval caches with
model/config/memory fields) and computes for key paired comparisons:

- capability difference in percentage points
- paired bootstrap 95% CI (10,000 resamples, fixed seed)
- McNemar exact test (discordant pairs)

Writes results/phase19_statistics.json plus cross-task matrix and backbone
transfer CSVs (from phase19_holdout_results.csv).
"""

import csv
import json
import os
import random
from collections import defaultdict
from math import comb

_REPO = os.path.join(os.path.dirname(__file__), "..", "..")
PRED = os.path.join(_REPO, "results", "phase19_item_predictions.jsonl")
HOLDOUT = os.path.join(_REPO, "results", "phase19_holdout_results.csv")
OUT_STATS = os.path.join(_REPO, "results", "phase19_statistics.json")
OUT_CROSS = os.path.join(_REPO, "results", "phase19_cross_task_matrix.csv")
OUT_BACKBONE = os.path.join(_REPO, "results", "phase19_backbone_transfer.csv")

BOOT_N = 10000
BOOT_SEED = 20260917


def load_predictions():
    """(benchmark, model, config) -> {item_index: correct}"""
    table = defaultdict(dict)
    for line in open(PRED):
        r = json.loads(line)
        table[(r["benchmark"], r["model"], r["config"])][
            r["item_index"]] = r["correct"]
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
    return {
        "n_items": len(items),
        "acc_a": round(acc_a, 4), "acc_b": round(acc_b, 4),
        "diff_pp": round(100 * (acc_a - acc_b), 2),
        "ci95_lo_pp": round(100 * means[int(0.025 * n)], 2),
        "ci95_hi_pp": round(100 * means[int(0.975 * n)], 2),
    }


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


def main():
    table = load_predictions()
    results = {}

    def compare(name, bench, model, cfg_a, cfg_b):
        a = table.get((bench, model, cfg_a))
        b = table.get((bench, model, cfg_b))
        if not a or not b:
            results[name] = {"error": "missing pair"}
            return
        results[name] = {"bootstrap": paired_bootstrap(a, b),
                         "mcnemar": mcnemar(a, b)}

    M15 = "Qwen2.5-1.5B-Instruct"
    M7 = "Qwen2.5-7B-Instruct"

    # Task-conditioned transfer (key C2 evidence)
    compare("gsm8k_1.5B: A_gsm vs A_pubmed", "gsm8k", M15, "A_gsm", "A_pubmed")
    compare("gsm8k_7B: A_gsm vs A_pubmed", "gsm8k", M7, "A_gsm", "A_pubmed")
    compare("pubmedqa_1.5B: A_pubmed vs A_gsm", "pubmedqa", M15,
            "A_pubmed", "A_gsm")
    compare("pubmedqa_7B: A_pubmed vs A_gsm", "pubmedqa", M7,
            "A_pubmed", "A_gsm")

    # memory contribution (C4)
    compare("gsm8k_1.5B: A_gsm vs no_memory", "gsm8k", M15,
            "A_gsm", "no_memory")
    compare("gsm8k_7B: A_gsm vs no_memory", "gsm8k", M7, "A_gsm", "no_memory")
    compare("pubmedqa_1.5B: A_pubmed vs no_memory", "pubmedqa", M15,
            "A_pubmed", "no_memory")
    compare("pubmedqa_7B: A_pubmed vs no_memory", "pubmedqa", M7,
            "A_pubmed", "no_memory")

    # vs strongest fixed baseline (C1)
    compare("gsm8k_1.5B: A_gsm vs fixed_mamba2", "gsm8k", M15,
            "A_gsm", "fixed_mamba2")
    compare("gsm8k_7B: A_gsm vs fixed_mamba2", "gsm8k", M7,
            "A_gsm", "fixed_mamba2")
    compare("pubmedqa_1.5B: A_pubmed vs fixed_retrieval", "pubmedqa", M15,
            "A_pubmed", "fixed_retrieval")
    compare("pubmedqa_7B: A_pubmed vs fixed_recency", "pubmedqa", M7,
            "A_pubmed", "fixed_recency")

    # backbone transfer on identical items (Task 4 evidence)
    for cfg, bench in (("A_gsm", "gsm8k"), ("A_pubmed", "pubmedqa")):
        a = table.get((bench, M7, cfg))
        b = table.get((bench, M15, cfg))
        if a and b:
            results["%s_%s: 7B vs 1.5B" % (bench, cfg)] = {
                "bootstrap": paired_bootstrap(a, b),
                "mcnemar": mcnemar(a, b),
            }

    with open(OUT_STATS, "w") as f:
        json.dump(results, f, indent=2)

    # --- cross-task + backbone matrices --------------------------------------
    rows = list(csv.DictReader(open(HOLDOUT)))
    with open(OUT_CROSS, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["config", "gsm8k_capability", "pubmedqa_capability"])
        for cfg in sorted({r["config"] for r in rows}):
            g = [r for r in rows if r["config"] == cfg
                 and r["benchmark"] == "gsm8k" and "1.5B" in r["model"]]
            p = [r for r in rows if r["config"] == cfg
                 and r["benchmark"] == "pubmedqa" and "1.5B" in r["model"]]
            w.writerow([cfg, g[0]["capability"] if g else "",
                        p[0]["capability"] if p else ""])

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
