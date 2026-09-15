"""Phase-16 aggregation: build paper artifacts from experiments/ logs.

Outputs (into results/):
- phase16_matrix.csv      method x benchmark, mean +/- std across seeds
- evolution_history.json  per method/benchmark/seed fitness curves
- best_architectures.json per method/benchmark/seed best genome + metrics

Also prints the ENSS-vs-Random verdict (success criterion 1).
"""

import glob
import json
import os
import sys
from collections import defaultdict

EXP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "experiments")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "results")

METHODS = ["fixed_attention", "fixed_mamba", "fixed_hybrid",
           "random", "no_pareto", "enss", "no_memory", "no_inherit"]
BENCHES = ["gsm8k", "pubmedqa"]
SEEDS = [0, 1, 2]


def mean_std(values):
    if not values:
        return None, None
    m = sum(values) / len(values)
    if len(values) < 2:
        return m, 0.0
    var = sum((v - m) ** 2 for v in values) / (len(values) - 1)
    return m, var ** 0.5


def main():
    matrix = {}       # (method, bench) -> list of per-seed best fitness
    caps = {}
    archs = defaultdict(list)
    history = defaultdict(dict)
    best_arch = defaultdict(dict)

    for method in METHODS:
        for bench in BENCHES:
            for seed in SEEDS:
                run = os.path.join(EXP_DIR, "%s_%s_seed%d"
                                   % (method, bench, seed))
                res = os.path.join(run, "results.json")
                if not os.path.exists(res):
                    continue
                r = json.load(open(res))
                matrix.setdefault((method, bench), []).append(
                    r["best_fitness"])
                caps.setdefault((method, bench), []).append(
                    r["best_metrics"]["capability"])
                archs[(method, bench)].append(r["best_architecture"])
                best_arch["%s|%s" % (method, bench)]["seed%d" % seed] = {
                    "architecture": r["best_architecture"],
                    "genome": r["best_genome"],
                    "fitness": r["best_fitness"],
                    "metrics": r["best_metrics"],
                }
                hist_path = os.path.join(run, "history.jsonl")
                if os.path.exists(hist_path):
                    with open(hist_path) as f:
                        history["%s|%s" % (method, bench)]["seed%d" % seed] = [
                            {"generation": rec["generation"],
                             "best_fitness": rec["best_fitness"],
                             "mean_fitness": rec["mean_fitness"],
                             "best_architecture": rec["best_architecture"]}
                            for rec in map(json.loads, f)
                        ]

    os.makedirs(OUT_DIR, exist_ok=True)

    csv_path = os.path.join(OUT_DIR, "phase16_matrix.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("method,benchmark,seeds,fitness_mean,fitness_std,"
                "capability_mean,capability_std,architectures\n")
        for method in METHODS:
            for bench in BENCHES:
                fits = matrix.get((method, bench), [])
                if not fits:
                    continue
                fm, fs = mean_std(fits)
                cm, cs = mean_std(caps[(method, bench)])
                f.write("%s,%s,%d,%.4f,%.4f,%.4f,%.4f,\"%s\"\n" % (
                    method, bench, len(fits), fm, fs, cm, cs,
                    " | ".join(archs[(method, bench)])))

    with open(os.path.join(OUT_DIR, "evolution_history.json"), "w") as f:
        json.dump(history, f, indent=2)
    with open(os.path.join(OUT_DIR, "best_architectures.json"), "w") as f:
        json.dump(best_arch, f, indent=2)

    # Verdict: ENSS vs Random (per-benchmark, mean best fitness over seeds)
    print(open(csv_path).read())
    for bench in BENCHES:
        e = matrix.get(("enss", bench), [])
        r = matrix.get(("random", bench), [])
        if e and r:
            em, es = mean_std(e)
            rm, rs = mean_std(r)
            verdict = "ENSS>Random" if em > rm else (
                "ENSS==Random" if abs(em - rm) < 1e-9 else "ENSS<Random")
            print("%s: ENSS %.4f±%.4f vs Random %.4f±%.4f -> %s"
                  % (bench, em, es, rm, rs, verdict))
    print("artifacts in", OUT_DIR)


if __name__ == "__main__":
    main()
