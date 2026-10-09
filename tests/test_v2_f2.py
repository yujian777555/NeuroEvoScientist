"""F2 preflight tests: SVAMP adapter, scorer, lock integrity, overlap guard.

All synthetic or schema-level; no SVAMP gold answers used in tests.
"""

import json
import os
import sys

REPO = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(REPO))

from v2_quality import svamp_adapter as A  # noqa: E402


def test_adapter_prompt_uses_body_plus_question_only():
    row = {"ID": 1, "Body": "Dan has 5 apples.", "Question": "How many?",
           "Equation": "5.0", "Answer": "5.0", "Type": "x"}
    q = A.to_prompt_question(row)
    assert "Dan has 5 apples." in q and "How many?" in q
    assert "5.0" not in q.split("How many?")[0].replace("5 apples", "")
    assert "Equation" not in q and "Answer" not in q


def test_scorer_numeric_formats():
    assert A.score(A.extract_model_answer("so the answer is #### 42"), "42") == 1.0
    assert A.score(A.extract_model_answer("#### -3.5"), "-3.5") == 1.0
    assert A.score(A.extract_model_answer("#### 1,000"), "1000") == 1.0
    assert A.score(A.extract_model_answer("#### 42"), "43") == 0.0
    assert A.score(A.extract_model_answer("no number"), "5") == 0.0
    assert A.extract_model_answer("#### ") is None


def test_lock_integrity():
    lock = json.load(open(A.LOCK, encoding="utf-8"))
    assert lock["n_items"] == 300
    assert len(lock["test_ids"]) == 300
    assert len(set(lock["test_ids"])) == 300
    assert lock["split_used"] == "test"
    assert lock["locked_configs"] == ["REF", "B2", "B1"]
    rows = A.load_locked_test_rows()  # raises if diverged from lock
    assert len(rows) == 300


def test_lock_predates_inference():
    """The lock commit must exist before any F2 result file."""
    lock_mtime = os.path.getmtime(A.LOCK)
    res = os.path.join(REPO, "v2_quality", "fasttrack", "f2_results")
    if os.path.isdir(res):
        for f in os.listdir(res):
            assert lock_mtime <= os.path.getmtime(os.path.join(res, f))


def test_no_overlap_with_gsm8k_calibration_bank():
    """Exact normalized-question overlap between SVAMP test and the GSM8K
    calibration bank must be zero (near-dup caveat documented separately)."""
    import re as _re
    def norm(t):
        return " ".join(_re.findall(r"[a-z0-9]+", t.lower()))
    gsm8k = set()
    with open(os.path.join(REPO, "data", "gsm8k", "train.jsonl"),
              encoding="utf-8") as f:
        for line in f:
            gsm8k.add(norm(json.loads(line)["question"]))
    rows = A.load_locked_test_rows()
    for r in rows:
        assert norm(A.to_prompt_question(r)) not in gsm8k
