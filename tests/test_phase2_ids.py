"""Phase-2 canonical ID / partition tests (tiny synthetic data only, no dataset)."""

import os
import sys

import pytest

REPO = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(REPO, "src"))

from phase2 import ids  # noqa: E402


# --- canonical ID contract ---------------------------------------------------

def test_normalize_text_nfc_trim_collapse():
    # decomposed e + combining acute must equal composed e-acute after NFC
    composed = "café"
    decomposed = "café"
    assert ids.normalize_text(composed) == ids.normalize_text(decomposed)
    assert ids.normalize_text("  a   b \n\t c  ") == "a b c"


def test_source_id_scalar_forms():
    assert ids.canonical_id("abc", "q?") == "src:abc"
    assert ids.canonical_id(12, "q?") == "src:12"          # int -> JSON scalar
    assert ids.canonical_id(3.5, "q?") == "src:3.5"        # float -> JSON scalar
    # source normalization applies (trim/collapse) before prefixing
    assert ids.canonical_id("  a   b ", "q?") == "src:a b"


def test_source_id_unusable_falls_back():
    for bad in (None, True, False, [1], {"a": 1}):
        out = ids.canonical_id(bad, "hello world")
        assert out.startswith("q:"), (bad, out)
    # empty-after-normalization source also falls back
    assert ids.canonical_id("   ", "hello world").startswith("q:")


def test_fallback_id_applies_q_exactly_once():
    out = ids.fallback_id("What is 2+2?")
    assert out.startswith("q:")
    assert out.count("q:") == 1
    body = out[2:]
    assert len(body) == 64 and all(c in "0123456789abcdef" for c in body)
    # deterministic
    assert ids.fallback_id("What is 2+2?") == out


def test_fallback_id_empty_question_raises():
    with pytest.raises(ids.IDError):
        ids.fallback_id("   \n  ")


def test_duplicate_canonical_ids_fail():
    with pytest.raises(ids.IDError):
        ids.validate_unique(["src:a", "src:b", "src:a"])
    with pytest.raises(ids.IDError):
        ids.validate_unique(["src:a", ""])


# --- locked counts ------------------------------------------------------------

def test_locked_partition_and_subset_counts():
    assert ids.PARTITION_COUNTS == {"BANK": 2989, "FIT": 1868,
                                    "TUNE": 1121, "LEVAL": 1495}
    assert sum(ids.PARTITION_COUNTS.values()) == 7473 == ids.TOTAL_ITEMS
    assert ids.SUBSET_SIZES == {"FIT": 500, "TUNE": 200, "LEVAL": 300}
    assert ids.N_FOLDS == 5


# --- partition / subset / fold assignment on tiny synthetic IDs ----------------

def _fake_ids(n):
    return ["q:%064x" % i for i in range(n)]


def test_assign_partitions_slicing_and_disjoint():
    counts = {"BANK": 4, "FIT": 3, "TUNE": 2, "LEVAL": 1}
    part = ids.assign_partitions(_fake_ids(10), counts=counts)
    assert [len(part[k]) for k in ("BANK", "FIT", "TUNE", "LEVAL")] == [4, 3, 2, 1]
    # fixed slice order BANK,FIT,TUNE,LEVAL over the deterministic global sort
    ordered = ids.ordered_ids(_fake_ids(10), ids.PARTITION_TAG)
    assert part["BANK"] == ordered[:4]
    assert part["FIT"] == ordered[4:7]
    assert part["TUNE"] == ordered[7:9]
    assert part["LEVAL"] == ordered[9:]
    # pairwise disjoint
    seen = set()
    for k in part:
        assert not (seen & set(part[k]))
        seen |= set(part[k])
    # deterministic
    assert ids.assign_partitions(_fake_ids(10), counts=counts) == part


def test_assign_partitions_total_mismatch_raises():
    with pytest.raises(ids.IDError):
        ids.assign_partitions(_fake_ids(5),
                              counts={"BANK": 4, "FIT": 3, "TUNE": 2, "LEVAL": 1})


def test_assign_subsets_independent_order():
    counts = {"BANK": 4, "FIT": 6, "TUNE": 5, "LEVAL": 5}
    part = ids.assign_partitions(_fake_ids(20), counts=counts)
    subs = ids.assign_subsets(part, sizes={"FIT": 3, "TUNE": 2, "LEVAL": 4})
    assert [len(subs[k]) for k in ("FIT", "TUNE", "LEVAL")] == [3, 2, 4]
    for k in subs:
        assert set(subs[k]) <= set(part[k])
    # subset uses its own namespace tag -> independent ordering from partition
    assert subs["FIT"] == ids.ordered_ids(part["FIT"], ids.SUBSET_TAG)[:3]
    assert ids.assign_subsets(part, sizes={"FIT": 3, "TUNE": 2, "LEVAL": 4}) == subs


def test_assign_fold_deterministic_and_in_range():
    folds = [ids.assign_fold(x) for x in _fake_ids(50)]
    assert all(0 <= f < 5 for f in folds)
    assert ids.assign_fold(_fake_ids(50)[7]) == folds[7]
    # fold tag differs from partition tag -> fold sequence is independent
    assert ids.assign_fold("q:abc") == ids.assign_fold("q:abc")
