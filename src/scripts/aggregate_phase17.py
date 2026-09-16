"""Phase-17 aggregation: focused matrix, inheritance curve, Pareto fronts.

Reads experiments/*_gsm8k_seed*/ (Phase-17 schema runs) and writes:
- results/phase17_focused_matrix.csv  method x seed rows
- results/phase17_inheritance_curve.json  per-candidate adaptation records,
  enss (inherited) vs no_inherit (scratch) comparison
- results/phase17_pareto.json  per-generation Pareto fronts on RAW
  objectives (capability, efficiency) — never the scalar aggregate
"""

import glob
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from evolution.nsga3 import Individual, fast_non_dominated_sort

EXP = os.path.join(os.path.dirname(__file__), "..", "..", "experiments")
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "results")


def _is_phase17(res):
    return (res["config"].get("schema") == "phase17"
            and res["config"].get("limit") == 100)


def main():
    rows = []
    inherit_records = defaultdict(list)  # method -> per-candidate records
    pareto = {}

    for res_path in sorted(glob.glob(os.path.join(EXP, "*_gsm8k_seed*",
                                                  "results.json"))):
        run = os.path.basename(os.path.dirname(res_path))
        res = json.load(open(res_path))
        if not _is_phase17(res):
            continue
        method = res["config"]["method"]
        seed = res["config"]["seed"]
        m = res["best_metrics"]
        rows.append({
            "method": method, "seed": seed,
            "best_architecture": res["best_architecture"],
            "fitness": res["best_fitness"],
            "capability": m["capability"], "efficiency": m["efficiency"],
            "adaptability": m["adaptability"],
            "prompt_tokens_total": m.get("prompt_tokens_total"),
            "latency_sec": m.get("latency_sec"),
        })

        hist_path = os.path.join(EXP, run, "history.jsonl")
        fronts = []
        if os.path.exists(hist_path):
            for line in open(hist_path):
                rec = json.loads(line)
                pop = rec.get("population", [])
                inds = [Individual(
                    genome=None,
                    objectives=[p["capability"], p["efficiency"]],
                ) for p in pop if p.get("capability") is not None]
                if inds:
                    front = fast_non_dominated_sort(inds)[0]
                    fronts.append({
                        "generation": rec["generation"],
                        "front": [[round(i.objectives[0], 4),
                                   round(i.objectives[1], 4)]
                                  for i in front],
                    })
                for p in pop:
                    a = p.get("adaptation") or {}
                    if a.get("trainable"):
                        inherit_records[method].append({
                            "generation": rec["generation"],
                            "memory": p["genome"]["memory"],
                            "inherited": a.get("inherited"),
                            "pre_loss": a.get("pre_loss"),
                            "post_loss": a.get("post_loss"),
                            "wall_time_sec": a.get("wall_time_sec"),
                            "capability": p.get("capability"),
                            "fitness": p.get("fitness"),
                        })
        pareto["%s_seed%d" % (method, seed)] = fronts

    os.makedirs(OUT, exist_ok=True)

    csv_path = os.path.join(OUT, "phase17_focused_matrix.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("method,seed,best_architecture,fitness,capability,"
                "efficiency,adaptability,prompt_tokens_total,latency_sec\n")
        for r in rows:
            f.write(",".join(str(r[k]) for k in
                             ["method", "seed", "best_architecture",
                              "fitness", "capability", "efficiency",
                              "adaptability", "prompt_tokens_total",
                              "latency_sec"]) + "\n")

    # inheritance comparison: mean capability of adapted mamba2 candidates
    # with inherited vs scratch init
    curve = {"per_method_records": {k: v for k, v in inherit_records.items()},
             "summary": {}}
    for method, recs in inherit_records.items():
        inh = [r for r in recs if r["inherited"]]
        scr = [r for r in recs if r["inherited"] is False]
        def _mean(xs, k):
            xs = [x[k] for x in xs if x.get(k) is not None]
            return sum(xs) / len(xs) if xs else None
        curve["summary"][method] = {
            "n_inherited": len(inh), "n_scratch": len(scr),
            "inherited_mean_capability": _mean(inh, "capability"),
            "scratch_mean_capability": _mean(scr, "capability"),
            "inherited_mean_post_loss": _mean(inh, "post_loss"),
            "scratch_mean_post_loss": _mean(scr, "post_loss"),
        }

    with open(os.path.join(OUT, "phase17_inheritance_curve.json"), "w") as f:
        json.dump(curve, f, indent=2)
    with open(os.path.join(OUT, "phase17_pareto.json"), "w") as f:
        json.dump(pareto, f, indent=2)

    # console summary
    by_method = defaultdict(list)
    for r in rows:
        by_method[r["method"]].append(r)
    for method, rs in sorted(by_method.items()):
        fits = [r["fitness"] for r in rs]
        caps = [r["capability"] for r in rs]
        print("%-16s n=%d fitness=%.4f cap=%.4f  %s" % (
            method, len(rs), sum(fits) / len(fits), sum(caps) / len(caps),
            " | ".join(sorted({r["best_architecture"] for r in rs}))))
    print("\nwrote phase17_focused_matrix.csv / phase17_inheritance_curve.json"
          " / phase17_pareto.json")


if __name__ == "__main__":
    main()
