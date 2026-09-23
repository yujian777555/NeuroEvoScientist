"""Phase-20 statistics: paired bootstrap + McNemar on structured-genome
holdout predictions, keyed by (benchmark, model, config, memory_enabled).

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

REPS = {"gsm8k": "A_gsm", "pubmedqa": "A_pubmed", "qasper": "A_qasper"}
FIXED = ["fixed_recency", "fixed_retrieval", "fixed_mamba2", "fixed_hybrid"]


def load_predictions():
    table = defaultdict(dict)
    for line in open(PRED):
        r = json.loads(line)
        key = (r["benchmark"], r["model"], r["config"],
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


def main():
    table = load_predictions()
    results = {}
    models = ["Qwen2.5-1.5B-Instruct", "Qwen2.5-7B-Instruct"]

    def compare(name, bench, model, cfg_a, cfg_b, mem_b=True):
        a = table.get((bench, model, cfg_a, True))
        b = table.get((bench, model, cfg_b, mem_b))
        if not a or not b:
            results[name] = {"error": "missing pair"}
            return
        results[name] = {"bootstrap": paired_bootstrap(a, b),
                         "mcnemar": mcnemar(a, b)}

    for bench, rep in REPS.items():
        crosses = [r for b2, r in REPS.items() if b2 != bench]
        for model in models:
            tag = model.split("-")[1]
            for other in crosses:
                compare("%s|%s|%s vs %s" % (bench, tag, rep, other),
                        bench, model, rep, other)
            compare("%s|%s|%s vs no_memory" % (bench, tag, rep),
                    bench, model, rep, "no_memory", mem_b=False)
            # vs strongest fixed baseline on that bench/model
            best_fixed = None
            best_cap = -1
            for fx in FIXED:
                scores = table.get((bench, model, fx, True))
                if scores:
                    cap = sum(scores.values()) / len(scores)
                    if cap > best_cap:
                        best_cap, best_fixed = cap, fx
            if best_fixed:
                compare("%s|%s|%s vs %s(best-fixed)" % (bench, tag, rep,
                        best_fixed), bench, model, rep, best_fixed)

    # backbone transfer on identical items
    for bench, rep in REPS.items():
        a = table.get((bench, models[1], rep, True))
        b = table.get((bench, models[0], rep, True))
        if a and b:
            results["%s|%s|7B vs 1.5B" % (bench, rep)] = {
                "bootstrap": paired_bootstrap(a, b),
                "mcnemar": mcnemar(a, b),
            }

    with open(OUT_STATS, "w") as f:
        json.dump(results, f, indent=2)

    rows = list(csv.DictReader(open(HOLDOUT)))
    benches = sorted({r["benchmark"] for r in rows})
    with open(OUT_CROSS, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
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
        for key in sorted({(r["config"], r["benchmark"]) for r in rows}):
            rs = [r for r in rows if (r["config"], r["benchmark"]) == key]
            a = [r for r in rs if "1.5B" in r["model"]]
            b = [r for r in rs if "7B" in r["model"]]
            if a and b:
                w.writerow([key[0], key[1], a[0]["capability"],
                            b[0]["capability"],
                            "%.2f" % (100 * (float(b[0]["capability"])
                                             - float(a[0]["capability"])))])

    for name, r in sorted(results.items()):
        if "bootstrap" in r and r["bootstrap"]:
            bs, mc = r["bootstrap"], r["mcnemar"]
            print("%-46s %+6.2fpp CI[%+6.2f,%+6.2f] p=%.4f" % (
                name, bs["diff_pp"], bs["ci95_lo_pp"], bs["ci95_hi_pp"],
                mc["p_exact"]))
        else:
            print(name, r)
    print("wrote", OUT_STATS)


if __name__ == "__main__":
    main()
