"""F2 Phase A: freeze the SVAMP confirmation lock BEFORE any model inference.

Writes v2_quality/fasttrack/confirmation_lock.json with:
- pinned HF revision + per-file sha256 (test.json used; train.json recorded
  but never used for evaluation);
- all 300 test IDs in their original fixed order + a sha256 over that list;
- adapter + scorer source hashes;
- provenance/contamination caveats.
"""

import hashlib
import json
import os
import sys

REPO = os.path.join(os.path.dirname(__file__), "..", "..")
DATA = os.path.join(REPO, "v2_quality", "fasttrack", "data")
OUT = os.path.join(REPO, "v2_quality", "fasttrack", "confirmation_lock.json")
REVISION = "5e0bf1e5e7c0e9c4bc39180d224f41f3f801b7ef"


def sha256_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    test_path = os.path.join(DATA, "svamp_test.json")
    rows = json.load(open(test_path, encoding="utf-8"))
    assert len(rows) == 300, "expected 300 SVAMP test rows"
    ids = [str(r["ID"]) for r in rows]  # original fixed order
    assert len(set(ids)) == 300, "duplicate test IDs"

    id_hash = hashlib.sha256("\n".join(ids).encode()).hexdigest()
    lock = {
        "dataset": "ChilleD/SVAMP",
        "hf_revision": REVISION,
        "license": "MIT (per dataset card; verify file notices before redistribution)",
        "files": {
            "test.json": sha256_file(test_path),
            "train.json": sha256_file(os.path.join(DATA, "svamp_train.json")),
        },
        "split_used": "test",
        "train_used": "NEVER (recorded for provenance only)",
        "n_items": 300,
        "test_ids_sha256": id_hash,
        "test_ids": ids,
        "locked_configs": ["REF", "B2", "B1"],
        "primary_contrast": "REF vs B2 (paired accuracy, tokens, CI + McNemar)",
        "secondary_contrast": "REF vs B1",
        "backbone": "Qwen/Qwen2.5-1.5B-Instruct",
        "model_revision": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
        "adapter_source_sha256": None,  # filled after adapter is written
        "scorer_source_sha256": None,
        "caveats": [
            "Public benchmark; pretraining contamination cannot be ruled out.",
            "Not a same-distribution GSM8K holdout; distribution shift caveat applies.",
            "Prompts use Body+Question only; Equation/Answer never enter prompts.",
        ],
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(lock, f, indent=2)
    print("lock written:", OUT, "items:", len(ids), "ids_sha:", id_hash[:16])


if __name__ == "__main__":
    main()
