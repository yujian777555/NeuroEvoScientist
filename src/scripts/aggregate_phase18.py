"""Phase-18 aggregation: dual-benchmark table, Pareto fronts, gene
distributions, paper tables/figures data.

Reads:
- experiments/<method>_<bench>_seed<N>/results.json + history.jsonl
- experiments/landscape_<bench>/landscape.jsonl

Writes (plan deliverables):
- results/phase18_dual_benchmark.csv
- results/phase18_pareto_fronts.json
- results/phase18_architecture_distribution.json
- paper/phase18_tables.md
- paper/phase18_figures_data.json
"""

import glob
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evolution.nsga3 import Individual, fast_non_dominated_sort

EXP = os.path.join(os.path.dirname(__file__), "..", "..", "experiments")
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "results")
PAPER = os.path.join(os.path.dirname(__file__), "..", "..", "paper")

METHODS = ["enss", "random", "fixed_recency", "fixed_retrieval",
           "fixed_mamba2", "fixed_hybrid", "no_memory"]
BENCHES = ["gsm8k", "pubmedqa"]
GENES = ["memory", "reasoning", "context_policy"]


def _valid_phase17(res):
    cfg = res.get("config", {})
    return cfg.get("schema") == "phase17" and cfg.get("limit") == 100


def mean_std(xs):
    if not xs:
        return None, None
    m = sum(xs) / len(xs)
    if len(xs) < 2:
        return m, 0.0
    return m, (sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5


def load_runs():
    runs = defaultdict(list)  # (method, bench) -> [result dicts]
    for res_path in glob.glob(os.path.join(EXP, "*_seed*", "results.json")):
        res = json.load(open(res_path))
        if not _valid_phase17(res):
            continue
        cfg = res["config"]
        runs[(cfg["method"], cfg["benchmark"])].append(res)
    return runs


def load_landscapes():
    landscapes = {}
    for bench in BENCHES:
        path = os.path.join(EXP, "landscape_%s" % bench, "landscape.jsonl")
        rows = [json.loads(l) for l in open(path)]
        landscapes[bench] = rows
    return landscapes


def main():
    runs = load_runs()
    landscapes = load_landscapes()
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PAPER, exist_ok=True)

    # --- dual benchmark CSV -------------------------------------------------
    csv_path = os.path.join(OUT, "phase18_dual_benchmark.csv")
    summary = {}
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("method,benchmark,seeds,fitness_mean,fitness_std,"
                "capability_mean,capability_std,efficiency_mean,"
                "best_architectures\n")
        for (method, bench), rs in sorted(runs.items()):
            fits = [r["best_fitness"] for r in rs]
            caps = [r["best_metrics"]["capability"] for r in rs]
            effs = [r["best_metrics"]["efficiency"] for r in rs]
            fm, fs = mean_std(fits)
            cm, cs = mean_std(caps)
            em, _ = mean_std(effs)
            archs = " | ".join(r["best_architecture"] for r in rs)
            f.write("%s,%s,%d,%.4f,%.4f,%.4f,%.4f,%.4f,\"%s\"\n"
                    % (method, bench, len(rs), fm, fs, cm, cs, em, archs))
            summary[(method, bench)] = {
                "n": len(rs), "fitness_mean": fm, "fitness_std": fs,
                "capability_mean": cm, "capability_std": cs,
                "efficiency_mean": em,
                "best_architectures": [r["best_architecture"] for r in rs],
            }

    # --- Pareto fronts from the landscape (Figure C) ------------------------
    pareto_fronts = {}
    gene_dist = {}
    for bench in BENCHES:
        rows = landscapes[bench]
        inds = [Individual(genome=None,
                           objectives=[r["capability"], r["efficiency"]],
                           payload=r) for r in rows]
        front = fast_non_dominated_sort(inds)[0]
        pareto_fronts[bench] = [
            {"architecture": i.payload["architecture"],
             "capability": i.payload["capability"],
             "efficiency": i.payload["efficiency"],
             "genome": i.payload["genome"]}
            for i in front
        ]
        # gene frequencies in the Pareto set (Figure A left)
        dist = {g: dict(Counter(i.payload["genome"][g] for i in front))
                for g in GENES}
        gene_dist[bench] = dist

    with open(os.path.join(OUT, "phase18_pareto_fronts.json"), "w") as f:
        json.dump(pareto_fronts, f, indent=2)

    # --- architecture distribution in evolved final populations (Figure A) --
    arch_dist = {}
    for (method, bench), rs in sorted(runs.items()):
        if method not in ("enss", "random"):
            continue
        counter = {g: Counter() for g in GENES}
        for r in rs:
            run = "%s_%s_seed%d" % (method, bench, r["config"]["seed"])
            hist = os.path.join(EXP, run, "history.jsonl")
            if not os.path.exists(hist):
                continue
            last = [json.loads(l) for l in open(hist)][-1]
            for ind in last.get("population", []):
                for g in GENES:
                    counter[g][ind["genome"][g]] += 1
        arch_dist["%s|%s" % (method, bench)] = {
            g: dict(counter[g]) for g in GENES}

    with open(os.path.join(OUT, "phase18_architecture_distribution.json"),
              "w") as f:
        json.dump({"pareto_set_gene_frequency": gene_dist,
                   "final_population_gene_frequency": arch_dist}, f, indent=2)

    # --- paper tables (markdown) ---------------------------------------------
    lines = ["# Phase-18 Paper Tables\n",
             "## Table A: Corrected-schema main results (mean±std, 3 seeds)\n"]
    for bench in BENCHES:
        lines.append("### %s\n" % bench.upper())
        lines.append("| Method | Fitness | Capability | Efficiency |")
        lines.append("|---|---|---|---|")
        for method in METHODS:
            s = summary.get((method, bench))
            if not s:
                continue
            lines.append("| %s | %.4f±%.4f | %.4f±%.4f | %.4f |" % (
                method, s["fitness_mean"], s["fitness_std"] or 0,
                s["capability_mean"], s["capability_std"] or 0,
                s["efficiency_mean"]))
        lines.append("")
    with open(os.path.join(PAPER, "phase18_tables.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(lines))

    # --- figures data ---------------------------------------------------------
    figures = {
        "figure_A_gene_distributions": {"pareto_set": gene_dist,
                                        "final_population": arch_dist},
        "figure_C_pareto_fronts": pareto_fronts,
    }
    with open(os.path.join(PAPER, "phase18_figures_data.json"), "w") as f:
        json.dump(figures, f, indent=2)

    print(open(csv_path).read())
    print("Pareto front sizes:", {b: len(p) for b, p in pareto_fronts.items()})


if __name__ == "__main__":
    main()
