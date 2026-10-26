"""Run the R1 duplicate-group audit and atomic CPU-only partition preflight.

Usage:
  PYTHONPATH=src python src/scripts/phase2_duplicate_r1.py audit --repo . --out phase2/pilot_r1
  PYTHONPATH=src python src/scripts/phase2_duplicate_r1.py record-regression --repo . --out phase2/pilot_r1 --log phase2/pilot_r1/pytest.log

The audit command reads source data and produces real audit/lock artifacts;
it never calls a model, uses a GPU, or accesses MATH-500. The regression
command converts an actual pytest log into a regression artifact and then
writes the final manifest from the real lock and test evidence.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from phase2 import duplicates, ids, preflight, runner  # noqa: E402


def _sha256(path):
    return runner._sha256_file(path)


def _source(repo):
    train = os.path.join(repo, "data", "gsm8k", "train.jsonl")
    test = os.path.join(repo, "data", "gsm8k", "test.jsonl")
    return {
        "dataset": "openai/gsm8k",
        "split": "train",
        "path": "data/gsm8k/train.jsonl",
        "sha256": _sha256(train),
        "test_path": "data/gsm8k/test.jsonl",
        "test_sha256": _sha256(test),
        "upstream_commit": "not present in existing metadata; immutable file content hash is authoritative",
    }


def _historical(repo):
    test = preflight.load_gsm8k_jsonl(
        os.path.join(repo, "data", "gsm8k", "test.jsonl"))
    test_ids = preflight.canonical_ids(test)
    with open(os.path.join(repo, "v2_quality", "fasttrack", "data",
                           "svamp_test.json"), encoding="utf-8") as f:
        raw = json.load(f)
    svamp = [{"question": str(r["Body"]).strip() + "\n"
              + str(r["Question"]).strip(), "answer": str(r["Answer"]),
              "source_id": r["ID"]} for r in raw]
    svamp_ids = preflight.canonical_ids(svamp)
    return {"gsm8k_test": test_ids, "svamp_f2_locked": svamp_ids}, test, svamp


def _old_evidence(repo):
    result = {}
    for name in ("preflight_manifest.json", "preflight.log"):
        path = os.path.join(repo, "phase2", "pilot", name)
        result[name] = {"path": "phase2/pilot/" + name,
                        "sha256": _sha256(path)}
    return result


def run_audit(repo, out):
    os.makedirs(out, exist_ok=True)
    train_path = os.path.join(repo, "data", "gsm8k", "train.jsonl")
    rows = preflight.load_gsm8k_jsonl(train_path)
    if len(rows) != ids.TOTAL_ITEMS:
        raise duplicates.LockValidationError("source count != 7473")
    canonical = preflight.canonical_ids(rows)
    old_partitions = ids.assign_partitions(canonical)
    old_part_by_id = {nid: name for name, members in old_partitions.items()
                      for nid in members}
    for row, nid in zip(rows, canonical):
        row["canonical_id"] = nid
        row["original_partition"] = old_part_by_id[nid]

    print("R1 source rows", len(rows), flush=True)
    print("R1 detector", duplicates.detector_contract(), flush=True)
    edges, pair_stats = duplicates.near_duplicate_pairs(rows)
    print("R1 pair stats", pair_stats, flush=True)
    groups = duplicates.build_groups(rows, edges)
    print("R1 groups", len(groups), "sizes", duplicates.group_size_distribution(groups),
          flush=True)
    historical_ids, test_rows, svamp_rows = _historical(repo)
    # Re-run the frozen cross-partition/history guards on the new grouping:
    all_text = [r["question"] for r in rows]
    for name, hist_rows in (("gsm8k_test", test_rows),
                            ("svamp_f2_locked", svamp_rows)):
        preflight.near_duplicate_guard(all_text, [r["question"] for r in hist_rows],
                                       label_a="train", label_b=name)

    cross_partition_edges = sum(1 for e in edges
                                if e["partition_a"] != e["partition_b"])
    audit = {
        "status": "AUDIT_COMPLETE",
        "detector": duplicates.detector_contract(),
        "source": _source(repo),
        "pair_statistics": pair_stats,
        "candidate_edges": edges,
        "cross_partition_near_duplicate_edges": cross_partition_edges,
        "groups": groups,
        "group_count": len(groups),
        "group_size_distribution": duplicates.group_size_distribution(groups),
        "large_groups_for_review": [g for g in groups if g["size"] > 2],
        "ambiguity_policy": "Any non-clique component is CHAIN_NON_CLIQUE and hard-stops; no answer-based merging is used",
    }
    preflight.write_json(audit, os.path.join(out, "duplicate_audit_r1.json"))

    try:
        result = duplicates.partition_groups(rows, groups)
        new_part_by_id = {nid: name for name, members in result["partitions"].items()
                          for nid in members}
        after = sum(1 for e in edges
                    if new_part_by_id[e["id_a"]] != new_part_by_id[e["id_b"]])
        if after:
            raise duplicates.LockValidationError(
                "atomic split has %d cross-partition near-duplicate edges" % after)
        audit["cross_partition_near_duplicate_edges_after_atomic_split"] = after
        preflight.write_json(audit, os.path.join(out, "duplicate_audit_r1.json"))
        lock = duplicates.make_lock(rows, groups, result,
                                    duplicates.detector_contract(),
                                    _source(repo), historical_ids)
        lock["cross_partition_near_duplicate_edges_after_atomic_split"] = after
        duplicates.validate_lock(lock, rows, groups, _source(repo)["sha256"])
    except duplicates.DuplicateAuditError as exc:
        failure = {
            "status": "NO-GO",
            "reason": str(exc),
            "audit": "phase2/pilot_r1/duplicate_audit_r1.json",
            "locks_created": False,
            "gpu_inference_started": False,
            "old_evidence": _old_evidence(repo),
        }
        preflight.write_json(failure, os.path.join(out, "preflight_manifest_r1.json"))
        print("R1 NO-GO", exc, flush=True)
        return failure

    preflight.write_json(lock, os.path.join(out, "partition_lock_r1.json"))
    manifest = {
        "status": "ATOMIC_PARTITION_WRITTEN_PENDING_REGRESSION",
        "source": lock["source"],
        "counts": lock["counts"],
        "deviation": lock["deviation"],
        "partition_hashes": lock["partition_hashes"],
        "group_count": len(groups),
        "group_size_distribution": duplicates.group_size_distribution(groups),
        "cross_partition_near_duplicate_edges_before_atomic_split": cross_partition_edges,
        "cross_partition_near_duplicate_edges_after_atomic_split": after,
        "bank_label_isolation": lock["bank_label_isolation"],
        "old_evidence": _old_evidence(repo),
        "gpu_inference_started": False,
        "math500_accessed": False,
    }
    preflight.write_json(manifest, os.path.join(out, "preflight_manifest_r1.json"))
    scope = {
        "jaccard": "token-set Jaccard = |A intersection B| / |A union B|, lowercase [a-z0-9]+ token sets",
        "sequence_ratio": "difflib.SequenceMatcher on original question strings",
        "threshold_location": "src/phase2/preflight.py NEAR_DUP_THRESHOLD = 0.9; also present in old failed manifest",
        "all_pairs_or_candidates": "All pairs are considered; only pairs with an exact Jaccard upper bound below 0.9 are skipped as provably non-matches. No random sampling.",
        "normalization": "lowercase alphanumeric tokenization only; no special case/whitespace/punctuation/person-name normalization beyond that tokenizer",
        "old_algorithm": "Original code assigned partitions before checking leakage (yes). R1 instead identifies groups first and then assigns whole groups.",
        "manifest_bypass": "Not accepted: validate_lock recomputes groups/assignments and source/partition hashes; edited manifests or mismatched locks are rejected.",
        "tolerance": "No positive tolerance was found in protocol v6; exact frozen counts are required, otherwise NO-GO.",
        "old_evidence": _old_evidence(repo),
        "code_sha256": {
            "duplicates.py": _sha256(os.path.join(repo, "src", "phase2", "duplicates.py")),
            "preflight.py": _sha256(os.path.join(repo, "src", "phase2", "preflight.py")),
        },
    }
    preflight.write_json(scope, os.path.join(out, "phase2_preflight_r1_scope_audit.json"))
    print("R1 ATOMIC_PARTITION_WRITTEN", lock["counts"], flush=True)
    return manifest


def record_regression(repo, out, log_path):
    """Create regression evidence from the actual pytest log and final manifest."""
    with open(log_path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    passed = [int(x) for x in re.findall(r"(\d+) passed", text)]
    failed = [int(x) for x in re.findall(r"(\d+) failed", text)]
    result = {
        "command": "python -m pytest tests/ -q",
        "log_path": os.path.relpath(log_path, repo),
        "log_sha256": _sha256(log_path),
        "passed": passed[-1] if passed else 0,
        "failed": failed[-1] if failed else 0,
        "raw_tail": text.splitlines()[-5:],
    }
    result["status"] = "PASS" if result["passed"] > 0 and result["failed"] == 0 else "FAIL"
    preflight.write_json(result, os.path.join(out, "phase2_preflight_r1_regression.json"))
    with open(os.path.join(out, "preflight_manifest_r1.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    if manifest.get("status") == "NO-GO":
        manifest["regression"] = result
    else:
        manifest["regression"] = result
        manifest["status"] = "CPU_PREFLIGHT_PASS_PENDING_PLANNER_REVIEW" \
            if result["status"] == "PASS" else "NO-GO"
    manifest["stop"] = True
    preflight.write_json(manifest, os.path.join(out, "preflight_manifest_r1.json"))
    print("R1 regression", result["status"], result["passed"], "passed", result["failed"], "failed")
    return result


def verify_reproducible(repo, out):
    """Run the audit again in a separate directory and compare lock hashes."""
    first_path = os.path.join(out, "partition_lock_r1.json")
    first_hash = _sha256(first_path)
    second_dir = out + "_reprocheck"
    os.makedirs(second_dir, exist_ok=True)
    run_audit(repo, second_dir)
    second_hash = _sha256(os.path.join(second_dir, "partition_lock_r1.json"))
    report = {
        "first_lock_sha256": first_hash,
        "second_lock_sha256": second_hash,
        "identical": first_hash == second_hash,
        "second_directory": os.path.basename(second_dir),
    }
    if first_hash != second_hash:
        raise duplicates.LockValidationError("non-reproducible partition lock")
    with open(os.path.join(out, "preflight_manifest_r1.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    manifest["reproducibility"] = report
    preflight.write_json(manifest, os.path.join(out, "preflight_manifest_r1.json"))
    print("R1 reproducibility", report, flush=True)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["audit", "record-regression",
                                            "verify-reproducible"])
    parser.add_argument("--repo", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--log")
    args = parser.parse_args()
    if args.command == "audit":
        run_audit(os.path.abspath(args.repo), os.path.abspath(args.out))
    elif args.command == "verify-reproducible":
        verify_reproducible(os.path.abspath(args.repo), os.path.abspath(args.out))
    else:
        if not args.log:
            parser.error("--log is required for record-regression")
        record_regression(os.path.abspath(args.repo), os.path.abspath(args.out),
                          os.path.abspath(args.log))


if __name__ == "__main__":
    main()
