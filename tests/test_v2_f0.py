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


def test_planner_f1_baselines_distinct_on_each_task():
    """Normalized genomes must not waste F1 GPU budget on duplicate phenotypes."""
    import sys
    import json
    sys.path.insert(0, os.path.join(REPO, "src"))
    from genome.structured import StructuredGenome, task_phenotype_hash
    conf = json.loads(_read("v2_quality/fasttrack/baselines_f1.json"))
    b = conf["baselines"]
    assert set(b) == {"B0", "B1", "B2", "B3", "B4", "B5", "REF"}
    genomes = {k: StructuredGenome(**{**conf["common"], **v}) for k,v in b.items()}
    for task in ("gsm8k", "qasper"):
        keys = [task_phenotype_hash(g, task) for g in genomes.values()]
        assert len(set(keys)) == len(keys), (task, dict(zip(genomes, keys)))
    assert b["B4"]["exemplar_count"] > 0
    assert b["B4"]["context_mode"] != b["B1"]["context_mode"]
    assert b["B5"]["reasoning"] != b["B0"]["reasoning"] or b["B5"]["exemplar_count"] != b["B0"]["exemplar_count"]


def test_planner_f1_matrix_exact_15_cells_and_budget():
    import json
    rows = list(csv.DictReader(open(os.path.join(REPO,
        "v2_quality/fasttrack/run_matrix.csv"), encoding="utf-8")))
    b = json.loads(_read("v2_quality/fasttrack/baselines_f1.json"))["baselines"]
    assert len(rows) == 15
    assert all(r["baseline"] in b for r in rows)
    proto = _read("v2_quality/fasttrack/protocol_f0.md")
    budget = _read("v2_quality/fasttrack/compute_budget.md")
    assert "F1 <= 1.5" in proto.replace("≤", "<=")
    assert "1.5" in budget and "12 GPU-hours" in budget
    assert all(r["split"].startswith("dev") for r in rows)


def test_legacy_tables_are_flagged_as_inconsistent():
    doc = _read("paper/phase21_tables.md")
    assert "NUMERICALLY UNRELIABLE" in doc
    csv_path = os.path.join(REPO,"results/phase20_holdout_results.csv")
    rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    hit = next(r for r in rows if r["benchmark"] == "gsm8k"
               and r["config"] == "A_qasper"
               and "7B" in r["model"])
    assert abs(float(hit["capability"]) - 0.693) > 0.1
    erratum = _read("v2_quality/fasttrack/archival_discrepancies.md")
    assert "MATERIAL NUMERIC ERRORS" in erratum
