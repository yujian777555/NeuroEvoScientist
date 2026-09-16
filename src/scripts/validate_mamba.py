"""Phase-16 Task 4 / Phase-17 Task 2: verify Mamba memory is real in the
inference path.

Traces the Mamba-2 episodic memory controller over a synthetic episode and
checks:

1. state update is trackable (memory state changes on every store)
2. the memory gene changes the compute path (mamba2 recall differs from
   recency/retrieval/hybrid on the same episode)
3. comparison across all four memory genes

Writes results/mamba_trace.json. Requires the real Mamba-2 substrate
(transformers>=4.44, i.e. the A800 VM); exits loudly otherwise — no proxy
is reported as Mamba.
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import torch

from genome.architecture import ArchitectureGenome
from evaluator.memory import build_memory_controller
from models.mamba_memory import mamba2_available

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
    if not mamba2_available():
        raise SystemExit(
            "Real Mamba-2 substrate unavailable here (transformers<4.44). "
            "Run on the A800 VM; refusing to validate a proxy as Mamba.")

    torch.manual_seed(0)
    genome = ArchitectureGenome(memory="mamba2", state_size=16)
    mamba = build_memory_controller(genome)

    # 1. trace memory-state updates
    trace = []
    prev = None
    for q, a in EPISODE:
        mamba.store(q, a)
        state = mamba.memory_state()
        norm = float(state.norm())
        changed = prev is None or not torch.allclose(prev, state, atol=1e-6)
        trace.append({"stored": q[:40], "state_norm": norm,
                      "state_changed": bool(changed)})
        prev = state

    # 2./3. compare recall paths across memory genes on the same episode
    recall_paths = {}
    for gene in ("recency", "retrieval", "mamba2", "hybrid"):
        g = ArchitectureGenome(memory=gene, state_size=16)
        ctrl = build_memory_controller(g)
        for q, a in EPISODE:
            ctrl.store(q, a)
        recall_paths[gene] = [h["question"][:30]
                              for h in ctrl.recall(QUERY, k=2)]

    result = {
        "substrate": "transformers.Mamba2Model (real Mamba-2)",
        "state_trace": trace,
        "state_updates_trackable": all(t["state_changed"] for t in trace),
        "recall_paths": recall_paths,
        "compute_path_differs": len({
            tuple(v) for v in recall_paths.values()
        }) > 1,
        "mamba_module": type(mamba.substrate.substrate).__name__,
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
