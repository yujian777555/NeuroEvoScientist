"""Phase-2 preflight tests: JSONL loader, overlap guards, BANK hash, lock and
manifest writers. All on tiny synthetic JSONL in tmp_path; no real dataset."""

import json
import os
import sys

import pytest

REPO = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(REPO, "src"))

from phase2 import preflight as PF  # noqa: E402


def _write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def test_load_gsm8k_jsonl(tmp_path):
    p = str(tmp_path / "d.jsonl")
    _write_jsonl(p, [{"question": "Q1?", "answer": "#### 1"},
                     {"question": "Q2?", "answer": "#### 2", "id": "x9"}])
    rows = PF.load_gsm8k_jsonl(p)
    assert [r["question"] for r in rows] == ["Q1?", "Q2?"]
    assert rows[1]["source_id"] == "x9" and rows[0]["source_id"] is None


def test_load_gsm8k_jsonl_bad_line_fails(tmp_path):
    p = str(tmp_path / "bad.jsonl")
    with open(p, "w", encoding="utf-8") as f:
        f.write('{"question": "ok?"}\n')
        f.write("not json\n")
    with pytest.raises(PF.PreflightError):
        PF.load_gsm8k_jsonl(p)
    p2 = str(tmp_path / "bad2.jsonl")
    _write_jsonl(p2, [{"answer": "#### 1"}])  # missing question
    with pytest.raises(PF.PreflightError):
        PF.load_gsm8k_jsonl(p2)


def test_canonical_ids_unique_or_fail(tmp_path):
    p = str(tmp_path / "d.jsonl")
    _write_jsonl(p, [{"question": "A?", "id": "a"}, {"question": "B?", "id": "b"}])
    ids = PF.canonical_ids(PF.load_gsm8k_jsonl(p))
    assert ids == ["src:a", "src:b"]
    # duplicate source IDs are a preflight FAILURE
    _write_jsonl(p, [{"question": "A?", "id": "a"}, {"question": "B?", "id": "a"}])
    with pytest.raises(Exception):
        PF.canonical_ids(PF.load_gsm8k_jsonl(p))


def test_exact_overlap_guard():
    assert PF.exact_overlap_guard(["src:a", "src:b"], ["src:c"]) is True
    with pytest.raises(PF.PreflightError):
        PF.exact_overlap_guard(["src:a", "src:b"], ["src:b", "src:c"])


def test_near_duplicate_guard():
    a = ["alpha bravo charlie delta echo foxtrot golf hotel india"]
    b = ["a completely different sentence here"]
    assert PF.near_duplicate_guard(a, b) is True
    # shares 9 of 10 distinct tokens with a[0] -> Jaccard 0.9 >= threshold
    near = ["alpha bravo charlie delta echo foxtrot golf hotel india juliet"]
    with pytest.raises(PF.PreflightError):
        PF.near_duplicate_guard(a, near)


def test_pairwise_partition_guard():
    parts = {"BANK": ["src:%d" % i for i in range(4)],
             "FIT": ["src:%d" % i for i in range(4, 8)]}
    assert PF.pairwise_partition_guard(parts) is True
    parts["TUNE"] = ["src:4"]  # collides with FIT
    with pytest.raises(PF.PreflightError):
        PF.pairwise_partition_guard(parts)


def test_bank_first48_id_hash():
    bank = ["src:%d" % i for i in range(60)]
    h = PF.bank_first48_id_hash(bank)
    assert h == PF.bank_first48_id_hash(bank)            # deterministic
    other = ["src:x"] + bank[1:]
    assert PF.bank_first48_id_hash(other) != h           # first-48 identity matters
    # beyond-48 changes do not affect the hash
    tail = bank[:48] + ["src:zzz"]
    assert PF.bank_first48_id_hash(tail) == h
    with pytest.raises(PF.PreflightError):
        PF.bank_first48_id_hash(bank[:47])               # fewer than 48 fails


def test_build_lock_and_write_json(tmp_path):
    counts_ids = {"BANK": ["src:b%d" % i for i in range(50)],
                  "FIT": ["src:f%d" % i for i in range(6)],
                  "TUNE": ["src:t%d" % i for i in range(5)],
                  "LEVAL": ["src:l%d" % i for i in range(5)]}
    subsets = {"FIT": counts_ids["FIT"][:3], "TUNE": counts_ids["TUNE"][:2],
               "LEVAL": counts_ids["LEVAL"][:2]}
    lock = PF.build_lock(counts_ids, subsets, source={"path": "synthetic"})
    assert lock["partitions"]["BANK"]["n"] == 50
    assert lock["subsets"]["FIT"]["n"] == 3
    assert "bank_first48_ids_sha256" in lock
    # deterministic serialization with sorted keys
    p = str(tmp_path / "lock.json")
    PF.write_json(lock, p)
    text = open(p, encoding="utf-8").read()
    assert text == json.dumps(lock, indent=2, sort_keys=True,
                              ensure_ascii=False) + "\n"
    # overlapping partitions make the lock build fail (fail-closed)
    bad = dict(counts_ids)
    bad["TUNE"] = [counts_ids["FIT"][0]]
    with pytest.raises(PF.PreflightError):
        PF.build_lock(bad, subsets, source={"path": "synthetic"})
