"""SVAMP confirmation adapter (versioned, under v2_quality/; no V1 changes).

Input mapping: prompt question = Body + Question (NEVER Equation/Answer).
Scoring: numeric gold from Answer; model answer from the last '####'
marker (or last number), tolerating negatives, decimals, and commas.

Synthetic-fixture tested; no SVAMP gold used in tests.
"""

import hashlib
import json
import os
import re

REPO = os.path.join(os.path.dirname(__file__), "..")  # v2_quality/ is one level deep
LOCK = os.path.join(REPO, "v2_quality", "fasttrack", "confirmation_lock.json")
DATA = os.path.join(REPO, "v2_quality", "fasttrack", "data")

ADAPTER_VERSION = "svamp-adapter-v1"

_NUM_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def to_prompt_question(row):
    """Body + Question only."""
    return str(row["Body"]).strip() + "\n" + str(row["Question"]).strip()


def extract_model_answer(text):
    """Last number after the final '####' marker; else last number in text."""
    if "####" in text:
        text = text.split("####")[-1]
    nums = _NUM_RE.findall(text)
    if not nums:
        return None
    return nums[-1].replace(",", "").rstrip(".")


def score(pred, gold):
    if pred is None:
        return 0.0
    try:
        return 1.0 if abs(float(pred) - float(gold)) < 1e-6 else 0.0
    except (ValueError, TypeError):
        return 0.0


def load_locked_test_rows():
    """Load SVAMP test rows and verify them against the committed lock."""
    lock = json.load(open(LOCK, encoding="utf-8"))
    rows = json.load(open(os.path.join(DATA, "svamp_test.json"),
                          encoding="utf-8"))
    ids = [str(r["ID"]) for r in rows]
    assert hashlib.sha256("\n".join(ids).encode()).hexdigest() \
        == lock["test_ids_sha256"], "test IDs diverge from committed lock"
    assert len(rows) == lock["n_items"] == 300
    return rows


def source_sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()
