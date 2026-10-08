"""F0 integrity tests (no GPU): split isolation, config identity,
V1-frozen checks, run-matrix sanity."""

import csv
import hashlib
import os

REPO = os.path.join(os.path.dirname(__file__), "..")

V1_PDF_SHA256 = ("e42191b0502f4b1ca7f7ed2bdd6b8b735ab0755294e185d2cd83156d"
                 "22ae931d")


def _read(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as f:
        return f.read()


def test_v1_pdf_untouched():
    path = os.path.join(REPO, "paper/arr2026/main.pdf")
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    assert h == V1_PDF_SHA256


def test_f1_run_matrix_valid():
    rows = list(csv.DictReader(open(os.path.join(
        REPO, "v2_quality/fasttrack/run_matrix.csv"), encoding="utf-8")))
    assert len(rows) >= 10
    ids = [r["cell_id"] for r in rows]
    assert len(ids) == len(set(ids))
    for r in rows:
        assert float(r["est_min_per_run"]) > 0
        assert r["split"].startswith("dev")
        assert "holdout" not in r["split"]


def test_protocol_and_budget_exist_and_locked():
    for rel in ("v2_quality/fasttrack/protocol_f0.md",
                "v2_quality/fasttrack/compute_budget.md",
                "v2_quality/fasttrack/confirmation_dataset.md",
                "v2_quality/fasttrack/archival_discrepancies.md"):
        assert os.path.exists(os.path.join(REPO, rel)), rel
    budget = _read("v2_quality/fasttrack/compute_budget.md")
    assert "3.0 GPU-hours" in budget


def test_supplementary_has_no_legacy_tables():
    import zipfile
    z = zipfile.ZipFile(os.path.join(
        REPO, "paper/arr2026/anonymous_supplementary.zip"))
    assert not any("phase21_tables" in n for n in z.namelist())


def test_confirmation_independence_documented():
    conf = _read("v2_quality/fasttrack/confirmation_dataset.md")
    assert "SVAMP" in conf and "5e0bf1e5" in conf
    # the inspected V1 holdouts must be explicitly excluded from confirmation
    assert "exploratory" in conf.lower() or "never evaluated" in conf
