"""Verify the GSM8K pipeline: loading, prompting, extraction, scoring.

Uses a fixture file and a scripted backend — this validates the pipeline
mechanics, not model capability (no real scores are fabricated).
"""

import os

import pytest

from genome.architecture import ArchitectureGenome
from evaluator.gsm8k import (GSM8KEvaluator, extract_gsm8k_answer,
                             answers_match)

FIXTURE = os.path.join(os.path.dirname(__file__),
                       "fixtures", "gsm8k_sample.jsonl")


def test_extract_answer():
    assert extract_gsm8k_answer("some reasoning\n#### 42") == "42"
    assert extract_gsm8k_answer("the result is 1,000") == "1000"
    assert extract_gsm8k_answer("3.5 apples") == "3.5"
    assert extract_gsm8k_answer("no number here") is None


def test_answers_match():
    assert answers_match("7", "7.0")
    assert not answers_match("7", "8")
    assert not answers_match(None, "7")


def test_prompt_conditioned_on_genome():
    ev = GSM8KEvaluator(backend=lambda p, g: "", data_path=FIXTURE)
    sample = ev.load_samples()[0]
    cot = ev.build_prompt(sample, ArchitectureGenome(reasoning="cot"))
    direct = ev.build_prompt(sample, ArchitectureGenome(reasoning="direct"))
    assert "step by step" in cot
    assert "step by step" not in direct


def test_real_scoring_pipeline_with_scripted_backend():
    # Scripted backend: answers first two correctly, third wrong.
    answers = iter(["#### 7", "#### 10", "#### 99"])
    ev = GSM8KEvaluator(backend=lambda p, g: next(answers),
                        data_path=FIXTURE)
    metrics = ev.evaluate(ArchitectureGenome(), agent=None)
    assert metrics["capability"] == pytest.approx(2.0 / 3.0)
    assert 0.0 <= metrics["efficiency"] <= 1.0
    assert 0.0 <= metrics["adaptability"] <= 1.0


def test_no_backend_refuses_to_score():
    ev = GSM8KEvaluator(backend=None, data_path=FIXTURE)
    with pytest.raises(RuntimeError, match="backend"):
        ev.evaluate(ArchitectureGenome(), agent=None)
