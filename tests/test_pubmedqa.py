"""Verify the PubMedQA pipeline: loading, extraction, scoring, memory hooks."""

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
                           data_path=FIXTURE)
    metrics = ev.evaluate(ArchitectureGenome(), agent=None)
    assert metrics["capability"] == pytest.approx(2.0 / 3.0)
    # adaptability proxy = accuracy on 'maybe'-gold questions (1/1 here)
    assert metrics["adaptability"] == pytest.approx(1.0)


def test_no_backend_refuses():
    ev = PubMedQAEvaluator(backend=None, data_path=FIXTURE)
    with pytest.raises(RuntimeError, match="backend"):
        ev.evaluate(ArchitectureGenome(), agent=None)


GSM8K_DIVERGENT = os.path.join(os.path.dirname(__file__),
                               "fixtures", "gsm8k_divergent.jsonl")


def test_memory_gene_changes_prompt_content():
    """Two different memory genes must produce different prompt content —
    genome activation is real, not cosmetic. The last fixture question is
    lexically closest to the FIRST one, so recency (attention) and
    similarity (retrieval) recall diverge."""
    from evaluator.gsm8k import GSM8KEvaluator
    seen = {}

    def make_backend(tag):
        def backend(prompt, genome):
            seen.setdefault(tag, []).append(prompt)
            return "#### 0"
        return backend

    for mem_gene in ("attention", "retrieval"):
        ev = GSM8KEvaluator(backend=make_backend(mem_gene),
                            data_path=GSM8K_DIVERGENT, memory_k=2)
        ev.evaluate(ArchitectureGenome(memory=mem_gene), agent=None)

    assert seen["attention"][0] == seen["retrieval"][0]  # empty history
    last_a, last_r = seen["attention"][-1], seen["retrieval"][-1]
    assert last_a != last_r
    # retrieval recalls the similar first question; recency does not
    assert "Apples cost 2 dollars" in last_r
    assert "Apples cost 2 dollars" not in last_a
