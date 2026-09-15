"""Experiment logging for ENSS runs (Phase-14).

Each run writes to ``experiments/<run_name>/``:

- ``history.jsonl``  one record per generation: best/mean fitness, best
                     architecture + metrics, Pareto front objectives,
                     architecture distribution (Figure 1/2/3 data)
- ``results.json``   final summary: run config + best agent (Table 1/2 data)
"""

import json
import os
from collections import Counter

from evolution.nsga3 import fast_non_dominated_sort


class ExperimentLogger:
    def __init__(self, run_name, base_dir=None, config=None):
        base_dir = base_dir or os.path.join(
            os.path.dirname(__file__), "..", "..", "experiments")
        self.run_dir = os.path.join(base_dir, run_name)
        os.makedirs(self.run_dir, exist_ok=True)
        self.history_path = os.path.join(self.run_dir, "history.jsonl")
        self.config = config or {}
        # truncate any previous run with the same name
        open(self.history_path, "w").close()

    def log_generation(self, gen, evaluated):
        ranked = sorted(evaluated, key=lambda e: e.fitness, reverse=True)
        best = ranked[0]
        mean_fitness = sum(e.fitness for e in ranked) / len(ranked)

        fronts = fast_non_dominated_sort([e.as_individual() for e in ranked])
        pareto_front = [
            {"architecture": ind.genome.describe(),
             "objectives": ind.objectives}
            for ind in fronts[0]
        ]

        distribution = Counter(e.genome.describe() for e in evaluated)

        record = {
            "generation": gen,
            "best_fitness": best.fitness,
            "mean_fitness": mean_fitness,
            "best_architecture": best.genome.describe(),
            "best_metrics": best.metrics,
            "pareto_front": pareto_front,
            "architecture_distribution": dict(distribution),
        }
        with open(self.history_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def finalize(self, best):
        summary = {
            "config": self.config,
            "best_architecture": best.genome.describe(),
            "best_genome": best.genome.to_dict(),
            "best_fitness": best.fitness,
            "best_metrics": best.metrics,
        }
        path = os.path.join(self.run_dir, "results.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        return summary
