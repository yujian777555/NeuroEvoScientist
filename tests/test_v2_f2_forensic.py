"""F3 forensic gate: the read-only F2 integrity verifier must pass on any
normal checkout. A FAIL there (exit code 2) is a hard blocker for paper
claims, so CI must surface it."""

import os
import subprocess
import sys

REPO = os.path.join(os.path.dirname(__file__), "..")


def test_f2_integrity_verifier_passes():
    proc = subprocess.run(
        [sys.executable,
         os.path.join(REPO, "v2_quality", "fasttrack",
                      "verify_f2_integrity.py")],
        capture_output=True, text=True, cwd=REPO)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "VERDICT: PASS" in proc.stdout


def test_forensic_report_committed_and_consistent():
    path = os.path.join(REPO, "v2_quality", "fasttrack",
                        "f2_provenance_forensic.md")
    assert os.path.exists(path)
    text = open(path, encoding="utf-8").read()
    # hard checks must be PASS; the loader gap must be disclosed
    assert "| A.test.json | PASS |" in text
    assert "| B.ids | PASS |" in text
    assert "F.v1_pdf | PASS" in text
    assert "ordered-ID hash" in text or "ordered ID" in text.lower()
    assert "PARTIAL" in text  # honest annotations retained
