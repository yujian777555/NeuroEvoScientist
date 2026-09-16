"""Verify the PubMedQA pipeline: loading, extraction, scoring, leakage."""

import os

import pytest

from genome.architecture import ArchitectureGenome
from evaluator.pubmedqa import (PubMedQAEvaluator, extract_pubmedqa_answer)

FIXTURE = os.path.join(os.path.dirname(__file__),
                       "fixtures", "pubmedqa_sample.jsonl")


def test_extract_answer():
    assert extract_pubmedqa_answer("reasoning... #### Yes") == "yes"
    assert extract_pubmedqa_answer("maybe. Actually no.") == "no"
    assert extract_pubmedqa_answer("no idea") == "no"  # 'no' in text
    assert extract_pubmedqa_answer("unclear") is None


def test_pipeline_with_scripted_backend():
    answers = iter(["#### yes", "#### yes", "#### maybe"])  # 2/3 correct
    ev = PubMedQAEvaluator(backend=lambda p, g: next(answers),
                           data_path=FIXTURE,
                           calibration_path=FIXTURE)
    metrics = ev.evaluate(ArchitectureGenome(memory="recency"), agent=None)
    assert metrics["capability"] == pytest.approx(2.0 / 3.0)
    # adaptability proxy = accuracy on 'maybe'-gold questions (1/1 here)
    assert metrics["adaptability"] == pytest.approx(1.0)


def test_no_backend_refuses():
    ev = PubMedQAEvaluator(backend=None, data_path=FIXTURE,
                           calibration_path=FIXTURE)
    with pytest.raises(RuntimeError, match="backend"):
        ev.evaluate(ArchitectureGenome(), agent=None)


def test_calibration_slice_disjoint_from_eval(tmp_path):
    """Calibration exemplars must not overlap evaluation items."""
    import json
    import shutil

    # fabricate a 6-sample dataset: eval limit 2, offset 500 clamps safely
    lines = [{"question": "q%d unique-marker-%d" % (i, i),
              "answer": "yes"} for i in range(6)]
    path = str(tmp_path / "pqal.jsonl")
    with open(path, "w") as f:
        for row in lines:
            f.write(json.dumps(row) + "\n")

    seen = []

    def backend(prompt, genome):
        seen.append(prompt)
        return "#### yes"

    ev = PubMedQAEvaluator(backend=backend, data_path=path, limit=2,
                           calibration_path=path)
    calib = ev.calibration_samples()
    eval_qs = {s["question"] for s in ev.load_samples()}
    calib_qs = {s["question"] for s in calib}
    assert eval_qs.isdisjoint(calib_qs)
