"""Materialize the already-validated R1 lock into runner input artifacts.

This does not create or change a partition assignment. It reads the frozen
R1 lock, validates it, derives only the predeclared pilot subsets and BANK
exemplar list, and writes a separate provenance manifest.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from phase2 import duplicates, ids, preflight, runner  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--lock", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    repo, lock_path, out = os.path.abspath(args.repo), os.path.abspath(args.lock), os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    lock = __import__("json").load(open(lock_path, encoding="utf-8"))
    rows = preflight.load_gsm8k_jsonl(os.path.join(repo, "data", "gsm8k", "train.jsonl"))
    canonical = preflight.canonical_ids(rows)
    for row, nid in zip(rows, canonical):
        row["canonical_id"] = nid
    groups = lock["groups"]
    duplicates.validate_lock(lock, rows, groups, lock["source"]["sha256"])
    partitions = lock["partitions"]
    subsets = ids.assign_subsets(partitions)
    by_id = {r["canonical_id"]: r for r in rows}
    bank_ids = partitions["BANK"][:48]
    stage1_ids = subsets["FIT"] + subsets["TUNE"]
    leval_ids = subsets["LEVAL"]
    runner._write_jsonl([by_id[nid] for nid in bank_ids], os.path.join(out, "bank48.jsonl"))
    runner._write_jsonl([by_id[nid] for nid in stage1_ids], os.path.join(out, "stage1.jsonl"))
    runner._write_jsonl([by_id[nid] for nid in leval_ids], os.path.join(out, "leval.jsonl"))
    inputs = {
        "questions": {nid: by_id[nid]["question"] for nid in stage1_ids + leval_ids},
        "stage1_ids": stage1_ids,
        "fit_ids": subsets["FIT"],
        "tune_ids": subsets["TUNE"],
        "leval_ids": leval_ids,
        "bank_first48_ids": bank_ids,
    }
    preflight.write_json(inputs, os.path.join(out, "inputs.json"))
    manifest = {
        "status": "DERIVED_FROM_VALIDATED_R1_LOCK",
        "source_lock": os.path.relpath(lock_path, repo),
        "source_lock_sha256": runner._sha256_file(lock_path),
        "partition_assignment_changed": False,
        "counts": {name: len(partitions[name]) for name in ids.PARTITION_ORDER},
        "subset_counts": {name: len(subsets[name]) for name in subsets},
        "subset_hashes": {name: preflight.ordered_id_list_hash(subsets[name]) for name in subsets},
        "bank_first48_ids_sha256": preflight.bank_first48_id_hash(partitions["BANK"]),
        "artifact_hashes": {
            name: runner._sha256_file(os.path.join(out, name))
            for name in ("bank48.jsonl", "stage1.jsonl", "leval.jsonl", "inputs.json")
        },
        "math500_accessed": False,
        "gpu_inference_started_by_this_step": False,
    }
    preflight.write_json(manifest, os.path.join(out, "derived_manifest.json"))
    print("DERIVED_OK", manifest["subset_counts"], manifest["subset_hashes"])


if __name__ == "__main__":
    main()
