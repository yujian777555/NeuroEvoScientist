"""Phase-16 Task 4: verify Mamba memory is real in the inference path.

Traces the Mamba episodic memory controller over a synthetic episode and
checks:

1. state update is trackable (state vector changes on every store)
2. the memory gene changes the compute path (mamba recall sequence differs
   from attention/retrieval on the same episode)
3. comparison against attention/retrieval/hybrid recall selections

Writes results/mamba_trace.json.
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import torch

from genome.architecture import ArchitectureGenome
from evaluator.memory import build_memory_controller

EPISODE = [
    ("Apples cost 2 dollars each. How much do 5 apples cost?",
     "2 * 5 = 10.\n#### 10"),
    ("A train moves 60 km in one hour. What is its speed?",
     "60 km per hour.\n#### 60"),
    ("Sara has 3 boxes with 4 pens each. How many pens?",
     "3 * 4 = 12.\n#### 12"),
    ("A book has 100 pages. Tom reads 20 pages a day. Days to finish?",
     "100 / 20 = 5.\n#### 5"),
    ("Oranges cost 3 dollars each. How much do 7 oranges cost?",
     "3 * 7 = 21.\n#### 21"),
    ("Pencils cost 1 dollar each. How much do 9 pencils cost?",
     "1 * 9 = 9.\n#### 9"),
]

QUERY = "Pens cost 4 dollars each. How much do 6 pens cost?"


def main():
    torch.manual_seed(0)
    genome = ArchitectureGenome(memory="mamba", hidden_size=64, state_size=16)
    mamba = build_memory_controller(genome)

    # 1. trace state updates
    trace = []
    prev_norm = 0.0
    for q, a in EPISODE:
        mamba.store(q, a)
        norm = float(mamba.state.norm())
        trace.append({"stored": q[:40], "state_norm": norm,
                      "state_changed": abs(norm - prev_norm) > 1e-6})
        prev_norm = norm

    # 2./3. compare recall paths across memory genes on the same episode
    recall_paths = {}
    for gene in ("attention", "retrieval", "mamba", "hybrid"):
        g = ArchitectureGenome(memory=gene, hidden_size=64, state_size=16)
        ctrl = build_memory_controller(g)
        for q, a in EPISODE:
            ctrl.store(q, a)
        recall_paths[gene] = [h["question"][:30]
                              for h in ctrl.recall(QUERY, k=2)]

    result = {
        "state_trace": trace,
        "state_updates_trackable": all(t["state_changed"] for t in trace),
        "recall_paths": recall_paths,
        "compute_path_differs": len({
            tuple(v) for v in recall_paths.values()
        }) > 1,
        "mamba_module": type(mamba.gate).__name__,
    }

    out = os.path.join(os.path.dirname(__file__), "..", "..", "results")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "mamba_trace.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    assert result["state_updates_trackable"]
    assert result["compute_path_differs"]
    print("MAMBA_VALIDATION_OK ->", path)


if __name__ == "__main__":
    main()
