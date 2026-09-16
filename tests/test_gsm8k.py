"""Verify the GSM8K pipeline: loading, prompting, extraction, scoring,
leakage discipline (Phase-17).

Uses fixture files and scripted backends — validates pipeline mechanics,
not model capability (no real scores are fabricated).
"""

import os

import pytest

from genome.architecture import ArchitectureGenome
from evaluator.gsm8k import (GSM8KEvaluator, extract_gsm8k_answer,
                             answers_match)

FIXTURE = os.path.join(os.path.dirname(__file__),
                       "fixtures", "gsm8k_sample.jsonl")
TRAIN_FIXTURE = os.path.join(os.path.dirname(__file__),
                             "fixtures", "gsm8k_train_fixture.jsonl")
DIVERGENT = os.path.join(os.path.dirname(__file__),
                         "fixtures", "gsm8k_divergent.jsonl")


def _ev(backend, data_path=FIXTURE, **kw):
    kw.setdefault("calibration_path", TRAIN_FIXTURE)
    return GSM8KEvaluator(backend=backend, data_path=data_path, **kw)


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
    ev = _ev(lambda p, g: "")
    sample = ev.load_samples()[0]
    cot = ev.build_prompt(sample, ArchitectureGenome(reasoning="cot"))
    direct = ev.build_prompt(sample, ArchitectureGenome(reasoning="direct"))
    assert "step by step" in cot
    assert "step by step" not in direct


def test_real_scoring_pipeline_with_scripted_backend():
    answers = iter(["#### 7", "#### 10", "#### 99"])  # 2/3 correct
    ev = _ev(lambda p, g: next(answers))
    metrics = ev.evaluate(ArchitectureGenome(memory="recency"), agent=None)
    assert metrics["capability"] == pytest.approx(2.0 / 3.0)
    assert 0.0 <= metrics["efficiency"] <= 1.0
    assert 0.0 <= metrics["adaptability"] <= 1.0


def test_no_backend_refuses_to_score():
    ev = _ev(None)
    with pytest.raises(RuntimeError, match="backend"):
        ev.evaluate(ArchitectureGenome(), agent=None)


def test_eval_cache_hit_skips_backend(tmp_path):
    cache = str(tmp_path / "eval_cache.json")
    calls = []

    def backend(prompt, genome):
        calls.append(prompt)
        return "#### 7"

    genome = ArchitectureGenome(memory="recency")
    ev = _ev(backend, cache_path=cache)
    first = ev.evaluate(genome, agent=None)
    assert calls, "first evaluation must call the backend"

    ev2 = _ev(backend, cache_path=cache)
    calls.clear()
    second = ev2.evaluate(genome, agent=None)
    assert calls == []
    assert second == first


def test_no_test_leakage_in_exemplars():
    """Phase-17 gate: exemplars come from the TRAIN bank only; gold answers
    of test items must never appear in any prompt."""
    seen = []

    def backend(prompt, genome):
        seen.append(prompt)
        return "#### 0"

    ev = _ev(backend)  # test fixture gold answers: #### 7/10/99
    ev.evaluate(ArchitectureGenome(memory="recency"), agent=None)
    assert all("#### 10" not in p for p in seen)   # test item 2 gold
    assert all("#### 99" not in p for p in seen)   # (never a gold answer)
    # but train-bank exemplars DO appear (memory active)
    assert any("#### 120" in p for p in seen[1:])


def test_memory_gene_changes_prompt_content():
    """Different memory genes must produce different prompt content.
    The first train-bank item is lexically closest to the LAST test item,
    so recency (bank tail) and retrieval (similarity) diverge."""
    seen = {}
    train = os.path.join(os.path.dirname(__file__),
                         "fixtures", "gsm8k_train_divergent.jsonl")

    def make_backend(tag):
        def backend(prompt, genome):
            seen.setdefault(tag, []).append(prompt)
            return "#### 0"
        return backend

    for mem_gene in ("recency", "retrieval"):
        ev = _ev(make_backend(mem_gene), data_path=DIVERGENT, memory_k=2,
                 calibration_path=train)
        ev.evaluate(ArchitectureGenome(memory=mem_gene), agent=None)

    last_recency, last_retrieval = seen["recency"][-1], seen["retrieval"][-1]
    assert last_recency != last_retrieval
    # retrieval recalls the similar first bank item; recency does not
    assert "Pencils cost 2 dollars" in last_retrieval
    assert "Pencils cost 2 dollars" not in last_recency
