"""Phase-18 Task 3: ENSS vs Random search-efficiency audit on the
exhaustive 48-point landscape oracle.

Online protocol: a policy may only observe objectives of architectures it
has already "evaluated" (looked up in the landscape table built by
Task 2). No new GPU inference happens here; the audit measures pure
search-policy sample efficiency.

Metrics per (benchmark, method, budget, seed):
1. best capability vs evaluations curve;
2. Pareto hypervolume (capability, efficiency; ref 0,0) vs evaluations;
3. hypervolume regret vs the global landscape front;
4. epsilon-Pareto hit (capability within eps of the global best);
5. evaluations-to-threshold;
6. AUC of the best-so-far capability curve.

Reads:  experiments/landscape_<bench>/landscape.jsonl
Writes: results/phase18_search_efficiency.csv (+ .json curves)
"""

import json
import os
import random
import sys
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from genome.architecture import ArchitectureGenome
from genome.search_space import SearchSpace
from evolution.mutation import mutate
from evolution.crossover import crossover
from evolution.nsga3 import Individual, NSGA3Selector, fast_non_dominated_sort

try:
    import yaml
except ImportError:
    yaml = None

EXP = os.path.join(os.path.dirname(__file__), "..", "..", "experiments")
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "results")

BUDGETS = [12, 24, 36, 48]
SEARCH_SEEDS = 20
EPSILON = 0.02


def gene_key(g):
    """Canonical key over the 4 genome genes (dims are not searched)."""
    d = g.to_dict() if hasattr(g, "to_dict") else dict(g)
    return tuple((f, d[f]) for f in
                 ("memory", "reasoning", "context_policy", "quantization"))


def load_landscape(bench):
    path = os.path.join(EXP, "landscape_%s" % bench, "landscape.jsonl")
    table = {}
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            table[gene_key(r["genome"])] = (r["capability"], r["efficiency"])
    return table


def hypervolume_2d(points, ref=(0.0, 0.0)):
    """2D Pareto hypervolume for maximization (sorted sweep, x descending)."""
    if not points:
        return 0.0
    inds = [Individual(genome=None, objectives=list(p)) for p in points]
    front = fast_non_dominated_sort(inds)[0]
    pts = sorted((tuple(i.objectives) for i in front), key=lambda p: -p[0])
    hv = 0.0
    prev_y = ref[1]
    for x, y in pts:  # x descending, y non-decreasing
        hv += (x - ref[0]) * (y - prev_y)
        prev_y = y
    return hv


class Oracle:
    """Lookup-only evaluator over the landscape table."""

    def __init__(self, table):
        self.table = table

    def evaluate(self, genome):
        key = gene_key(genome)
        return self.table[key]  # KeyError = point not in space (bug guard)


class _DotDict(dict):
    __getattr__ = dict.get


def enss_policy(oracle, space, budget, seed):
    """ENSS search policy, one evaluation at a time, budget-limited."""
    rng = random.Random(seed)
    selector = NSGA3Selector(population_size=8)
    evaluated = {}  # key -> objectives

    pop = [ArchitectureGenome(**space.sample(rng)) for _ in range(4)]
    curve = []
    while len(evaluated) < budget:
        batch = []
        for g in pop:
            key = gene_key(g)
            if key not in evaluated:
                evaluated[key] = oracle.evaluate(g)
                batch.append((key, evaluated[key]))
                curve.append(dict(evaluated))
            if len(evaluated) >= budget:
                break
        if len(evaluated) >= budget:
            break

        inds = [Individual(genome=None, objectives=list(o))
                for o in evaluated.values()]
        fronts = fast_non_dominated_sort(inds)
        # parent pool = current Pareto front keys (fallback: all)
        front0 = fronts[0]
        front_objs = {tuple(i.objectives) for i in front0}
        pool_keys = [k for k, v in evaluated.items()
                     if tuple(v) in front_objs] or list(evaluated)

        pop = []
        while len(pop) < 4 and len(evaluated) + len(pop) < budget:
            a = ArchitectureGenome(**dict(rng.choice(pool_keys)))
            b = ArchitectureGenome(**dict(rng.choice(pool_keys)))
            child = crossover(a, b, rng)
            if rng.random() < 0.5:
                child = mutate(child, space, rng)
            pop.append(child)
        if not pop:
            break
    return evaluated, curve


def random_policy(oracle, space, budget, seed):
    rng = random.Random(seed)
    evaluated = {}
    curve = []
    while len(evaluated) < budget:
        g = ArchitectureGenome(**space.sample(rng))
        key = gene_key(g)
        if key in evaluated:
            continue
        evaluated[key] = oracle.evaluate(g)
        curve.append(dict(evaluated))
    return evaluated, curve


def audit_benchmark(bench):
    table = load_landscape(bench)
    space = SearchSpace()
    oracle = Oracle(table)

    global_front_pts = list(table.values())
    global_best_cap = max(p[0] for p in global_front_pts)
    global_hv = hypervolume_2d(global_front_pts)

    rows = []
    curves = defaultdict(list)
    for method, policy in (("enss", enss_policy), ("random", random_policy)):
        for budget in BUDGETS:
            for seed in range(SEARCH_SEEDS):
                evaluated, curve = policy(oracle, space, budget, seed)
                pts = list(evaluated.values())
                best_cap = max(p[0] for p in pts)
                hv = hypervolume_2d(pts)
                # epsilon-Pareto hit + evaluations-to-threshold
                ett = None
                for i, snap in enumerate(curve, 1):
                    if max(p[0] for p in snap.values()) \
                            >= global_best_cap - EPSILON:
                        ett = i
                        break
                auc = sum(max(p[0] for p in snap.values())
                          for snap in curve) / max(1, len(curve))
                rows.append({
                    "benchmark": bench, "method": method,
                    "budget": budget, "seed": seed,
                    "best_capability": best_cap,
                    "hypervolume": hv,
                    "hypervolume_regret": global_hv - hv,
                    "eps_pareto_hit": 1 if ett is not None else 0,
                    "evals_to_threshold": ett if ett is not None else "",
                    "auc_best_capability": auc,
                })
                curves[(bench, method, budget)].append(
                    [max(p[0] for p in snap.values()) for snap in curve])
    return rows, curves, {"global_hypervolume": global_hv,
                          "global_best_capability": global_best_cap}


def main():
    os.makedirs(OUT, exist_ok=True)
    all_rows, all_curves, meta = [], {}, {}
    for bench in ("gsm8k", "pubmedqa"):
        rows, curves, m = audit_benchmark(bench)
        all_rows.extend(rows)
        for k, v in curves.items():
            all_curves["%s|%s|%d" % k] = v
        meta[bench] = m

    csv_path = os.path.join(OUT, "phase18_search_efficiency.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("benchmark,method,budget,seed,best_capability,hypervolume,"
                "hypervolume_regret,eps_pareto_hit,evals_to_threshold,"
                "auc_best_capability\n")
        for r in all_rows:
            f.write(",".join(str(r[k]) for k in
                             ["benchmark", "method", "budget", "seed",
                              "best_capability", "hypervolume",
                              "hypervolume_regret", "eps_pareto_hit",
                              "evals_to_threshold",
                              "auc_best_capability"]) + "\n")

    with open(os.path.join(OUT, "phase18_search_efficiency_curves.json"),
              "w") as f:
        json.dump({"curves": all_curves, "meta": meta}, f)

    # console verdict
    agg = defaultdict(list)
    for r in all_rows:
        agg[(r["benchmark"], r["method"], r["budget"])].append(r)
    for (bench, method, budget), rs in sorted(agg.items()):
        if method != "enss":
            continue
        rs_r = agg.get((bench, "random", budget), [])
        if not rs_r:
            continue
        e_auc = sum(x["auc_best_capability"] for x in rs) / len(rs)
        r_auc = sum(x["auc_best_capability"] for x in rs_r) / len(rs_r)
        e_hv = sum(x["hypervolume"] for x in rs) / len(rs)
        r_hv = sum(x["hypervolume"] for x in rs_r) / len(rs_r)
        print("%s B=%-3d AUC enss %.4f vs rand %.4f | HV %.4f vs %.4f"
              % (bench, budget, e_auc, r_auc, e_hv, r_hv))
    print("wrote", csv_path)


if __name__ == "__main__":
    main()
