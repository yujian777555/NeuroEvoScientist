"""Deterministic R1 duplicate-group and atomic-partition tests (no real data)."""

import json

import pytest

from phase2 import duplicates, ids, preflight


def _row(question, answer="#### 1"):
    return {"question": question, "answer": answer,
            "canonical_id": ids.fallback_id(question)}


JOSIE = _row("Josie received $50 as a gift. She plans to buy two cassette tapes that cost $9 each and a headphone set that costs $25. How much money will she have left?")
AMANDA = _row("Amanda received $50 as a gift. She plans to buy two cassette tapes that cost $9 each and a headphone set that costs $25. How much money will she have left?")


@pytest.fixture(scope="module")
def corpus():
    rows = [_row("Unique problem %d: %d apples in %d boxes" % (i, i % 7 + 1, i % 11 + 1))
            for i in range(7471)]
    rows.extend([JOSIE, AMANDA])
    return rows


@pytest.fixture(scope="module")
def groups(corpus):
    edges, _ = duplicates.near_duplicate_pairs([JOSIE, AMANDA])
    # All other rows are singleton groups; only the known pair is merged.
    edges = [dict(e, i=7471, j=7472) for e in edges]
    return duplicates.build_groups(corpus, edges)


@pytest.fixture(scope="module")
def partitioned(corpus, groups):
    return duplicates.partition_groups(corpus, groups)


@pytest.fixture(scope="module")
def lock(corpus, groups, partitioned):
    return duplicates.make_lock(corpus, groups, partitioned,
                                duplicates.detector_contract(),
                                {"sha256": "a" * 64}, {"gsm8k_test": []})


def test_jaccard_and_sequence_ratio_match_frozen_detector():
    edges, stats = duplicates.near_duplicate_pairs([JOSIE, AMANDA])
    assert len(edges) == 1
    assert edges[0]["jaccard"] == pytest.approx(0.9310344827586207)
    assert edges[0]["sequence_ratio"] == pytest.approx(0.9644012944983819)
    assert stats["total_pairs"] == 1


def test_josie_amanda_same_partition(corpus, partitioned):
    locations = {nid: name for name, members in partitioned["partitions"].items()
                 for nid in members}
    assert locations[JOSIE["canonical_id"]] == locations[AMANDA["canonical_id"]]


def test_repeated_partition_is_identical(corpus, groups, partitioned):
    again = duplicates.partition_groups(corpus, groups)
    assert again["partitions"] == partitioned["partitions"]
    assert again["group_assignment"] == partitioned["group_assignment"]


def test_all_samples_exactly_once_and_content_unchanged(corpus, partitioned):
    flat = [nid for members in partitioned["partitions"].values() for nid in members]
    assert len(flat) == len(set(flat)) == 7473
    assert set(flat) == {r["canonical_id"] for r in corpus}
    assert JOSIE["answer"] == AMANDA["answer"] == "#### 1"


def test_detector_uses_question_not_answer():
    a = _row("Two apples and three pears", answer="#### 99")
    b = _row("Two apples and three pears", answer="#### 12345")
    c = _row("A completely different question", answer="#### 99")
    edges, _ = duplicates.near_duplicate_pairs([a, b, c])
    assert len(edges) == 1
    assert edges[0]["id_a"] == a["canonical_id"]
    assert edges[0]["id_b"] == b["canonical_id"]


def test_bank_label_isolation(lock):
    assert lock["bank_label_isolation"]["prohibited_overlap"] == {"gsm8k_test": 0}
    assert lock["bank_label_isolation"]["bank_contains_fit_tune_leval_or_test_labels"] is False


def test_bank_label_overlap_is_rejected(corpus, groups, partitioned):
    bank_id = next(iter(partitioned["partitions"]["BANK"]))
    with pytest.raises(duplicates.LockValidationError):
        duplicates.bank_label_audit(partitioned["partitions"],
                                    {"gsm8k_test": [bank_id]})


def test_missing_detector_threshold_fails_closed(monkeypatch):
    monkeypatch.setattr(preflight, "NEAR_DUP_THRESHOLD", None)
    with pytest.raises(duplicates.DetectorContractError):
        duplicates.detector_contract()


def test_threshold_change_is_rejected():
    with pytest.raises(duplicates.DetectorContractError):
        duplicates.near_duplicate_pairs([JOSIE, AMANDA], threshold=0.8)


def test_chain_non_clique_group_is_hard_stop():
    rows = [_row("alpha beta gamma"), _row("alpha beta gamma delta"),
            _row("alpha beta gamma delta epsilon")]
    # Artificially retain only A-B and B-C, producing a non-clique chain.
    edges = [{"i": 0, "j": 1, "id_a": rows[0]["canonical_id"],
              "id_b": rows[1]["canonical_id"], "jaccard": 0.95,
              "sequence_ratio": 0.95},
             {"i": 1, "j": 2, "id_a": rows[1]["canonical_id"],
              "id_b": rows[2]["canonical_id"], "jaccard": 0.95,
              "sequence_ratio": 0.95}]
    groups = duplicates.build_groups(rows, edges)
    assert groups[0]["ambiguities"] == ["CHAIN_NON_CLIQUE"]
    with pytest.raises(duplicates.AmbiguousGroupError):
        duplicates.assert_unambiguous(groups)


def test_abnormally_large_group_cannot_meet_exact_counts(corpus, groups):
    # Largest target is BANK=2989. An indivisible 2990-member group must fail.
    member_ids = [g["member_ids"] for g in groups]
    flat = [nid for members in member_ids for nid in members]
    big = {"group_id": "dg:big", "member_ids": flat[:2990], "size": 2990,
           "internal_edge_count": 0, "min_internal_jaccard": None,
           "max_internal_jaccard": None, "is_clique": True,
           "missing_clique_edges": [], "ambiguities": []}
    singles = [g for g in groups if len(g["member_ids"]) > 1
               and g["member_ids"] not in (flat[:2990],)]
    # Rebuild singleton groups for the remainder without duplicating big members.
    bigset = set(big["member_ids"])
    remainder = [nid for nid in flat if nid not in bigset]
    singles = [{"group_id": "dg:" + nid, "member_ids": [nid], "size": 1,
                "internal_edge_count": 0, "min_internal_jaccard": None,
                "max_internal_jaccard": None, "is_clique": True,
                "missing_clique_edges": [], "ambiguities": []}
               for nid in remainder]
    with pytest.raises(duplicates.PartitionToleranceError):
        duplicates.partition_groups(corpus, [big] + singles)


def test_lock_and_partition_hash_validate(corpus, groups, lock):
    assert duplicates.validate_lock(lock, corpus, groups, "a" * 64)


def test_tampered_source_hash_is_rejected(corpus, groups, lock):
    bad = json.loads(json.dumps(lock))
    bad["source"]["sha256"] = "b" * 64
    with pytest.raises(duplicates.LockValidationError):
        duplicates.validate_lock(bad, corpus, groups, "a" * 64)


def test_tampered_partition_lock_is_rejected(corpus, groups, lock):
    bad = json.loads(json.dumps(lock))
    bad["partition_hashes"]["BANK"] = "0" * 64
    with pytest.raises(duplicates.LockValidationError):
        duplicates.validate_lock(bad, corpus, groups, "a" * 64)


def test_tampered_group_assignment_is_rejected(corpus, groups, lock):
    bad = json.loads(json.dumps(lock))
    first = next(iter(bad["group_assignment"]))
    bad["group_assignment"][first] = "TUNE" if bad["group_assignment"][first] != "TUNE" else "BANK"
    with pytest.raises(duplicates.LockValidationError):
        duplicates.validate_lock(bad, corpus, groups, "a" * 64)


def test_regression_artifact_uses_real_pytest_log(tmp_path):
    log = tmp_path / "pytest.log"
    log.write_text("warnings summary\n187 passed in 144.00s\n", encoding="utf-8")
    manifest = {"status": "ATOMIC_PARTITION_WRITTEN_PENDING_REGRESSION"}
    preflight.write_json(manifest, str(tmp_path / "preflight_manifest_r1.json"))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "r1_cli", "src/scripts/phase2_duplicate_r1.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.record_regression(".", str(tmp_path), str(log))
    assert result["status"] == "PASS"
    assert result["passed"] == 187 and result["failed"] == 0
    final = json.loads((tmp_path / "preflight_manifest_r1.json").read_text())
    assert final["status"] == "CPU_PREFLIGHT_PASS_PENDING_PLANNER_REVIEW"


def test_old_failure_evidence_is_not_modified(tmp_path):
    old = tmp_path / "phase2" / "pilot"
    old.mkdir(parents=True)
    manifest = old / "preflight_manifest.json"
    log = old / "preflight.log"
    manifest.write_text("{\"status\": \"NO-GO\"}\n", encoding="utf-8")
    log.write_text("original failure\n", encoding="utf-8")
    before = {p.name: p.read_bytes() for p in (manifest, log)}
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "r1_cli", "src/scripts/phase2_duplicate_r1.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    first = module._old_evidence(str(tmp_path))
    second = module._old_evidence(str(tmp_path))
    assert first == second
    assert {p.name: p.read_bytes() for p in (manifest, log)} == before
