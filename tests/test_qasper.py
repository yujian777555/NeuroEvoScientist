"""QASPER evaluator tests (fixtures + scripted backend; no real scores)."""

import os

import pytest

from genome.architecture import ArchitectureGenome
from genome.structured import StructuredGenome
from evaluator.qasper import QasperEvaluator, qa_f1

FIXTURE = os.path.join(os.path.dirname(__file__),
                       "fixtures", "qasper_sample.jsonl")


def test_qa_f1():
    assert qa_f1("sparse attention windows", "sparse attention windows") == 1.0
    assert qa_f1("dense attention", "sparse attention windows") < 1.0
    assert qa_f1("", "something") == 0.0
    assert qa_f1("the cat sat", "the cat sat") == 1.0


def test_pipeline_with_scripted_backend():
    answers = iter(["#### sparse attention windows", "#### something wrong"])
    ev = QasperEvaluator(backend=lambda p, g: next(answers),
                         data_path=FIXTURE, calibration_path=FIXTURE,
                         start=0, limit=2)
    metrics = ev.evaluate(ArchitectureGenome(memory="recency"), agent=None)
    assert metrics["capability"] == pytest.approx(0.5)
    assert metrics["prompt_tokens_total"] > 0


def test_no_backend_refuses():
    ev = QasperEvaluator(backend=None, data_path=FIXTURE)
    with pytest.raises(RuntimeError, match="backend"):
        ev.evaluate(ArchitectureGenome(), agent=None)


def test_structured_genome_prompt_wiring():
    """Structured genes reach the actual QASPER prompt."""
    seen = []

    def backend(prompt, genome):
        seen.append(prompt)
        return "#### x"

    ev = QasperEvaluator(backend=backend, data_path=FIXTURE,
                         calibration_path=FIXTURE, start=0, limit=1)

    g_cot = StructuredGenome(reasoning="cot", reasoning_depth=4,
                             exemplar_count=0)
    ev.evaluate(g_cot, agent=None)
    assert "exactly 4 short steps" in seen[-1]

    g_direct = StructuredGenome(reasoning="direct", exemplar_count=0)
    ev.evaluate(g_direct, agent=None)
    assert "step by step" not in seen[-1]


def test_split_disjointness():
    """dev [0:50), holdout [50:150), calibration [150:) are disjoint."""
    ev_dev = QasperEvaluator(backend=lambda p, g: "", data_path=FIXTURE,
                             calibration_path=FIXTURE, start=0, limit=1)
    ev_hold = QasperEvaluator(backend=lambda p, g: "", data_path=FIXTURE,
                              calibration_path=FIXTURE, start=1, limit=1)
    dev_ids = {s["_id"] for s in ev_dev.load_samples()}
    hold_ids = {s["_id"] for s in ev_hold.load_samples()}
    assert dev_ids.isdisjoint(hold_ids)
    # fixture has only 2 items -> calibration (offset 150) is empty, safe
    assert ev_dev.calibration_samples() == []
