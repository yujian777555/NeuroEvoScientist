"""Verify Phase-17 memory substrates: recall behavior, genome control, schema."""

import pytest

from genome.architecture import ArchitectureGenome
from evaluator.memory import (build_memory_controller, format_exemplar,
                              tfidf_scores)
from models.mamba_memory import mamba2_available

HISTORY = [
    ("How much is 2 + 2?", "2 + 2 = 4.\n#### 4"),
    ("A train travels 60 km in 1 hour. Speed?", "60 km/h.\n#### 60"),
    ("What is the capital of France?", "Paris.\n#### Paris"),
]


def _fill(memory):
    for q, a in HISTORY:
        memory.store(q, a)
    return memory


def test_recency_window():
    g = ArchitectureGenome(memory="recency")
    mem = _fill(build_memory_controller(g))
    out = mem.recall("anything", k=2)
    assert len(out) == 2
    assert out[-1]["question"] == HISTORY[-1][0]


def test_retrieval_similarity():
    g = ArchitectureGenome(memory="retrieval")
    mem = _fill(build_memory_controller(g))
    out = mem.recall("train speed km per hour", k=1)
    assert out[0]["question"] == HISTORY[1][0]


@pytest.mark.skipif(not mamba2_available(),
                    reason="transformers Mamba2 unavailable on this box")
def test_mamba2_recall_runs_and_returns_k():
    g = ArchitectureGenome(memory="mamba2", state_size=16)
    mem = _fill(build_memory_controller(g))
    out = mem.recall("2 + 2", k=2)
    assert len(out) == 2
    assert all("question" in h for h in out)


def test_hybrid_includes_latest():
    g = ArchitectureGenome(memory="hybrid")
    mem = _fill(build_memory_controller(g))
    out = mem.recall("train speed", k=3)
    assert out[-1]["question"] == HISTORY[-1][0]


def test_empty_bank_recall():
    g = ArchitectureGenome(memory="recency")
    assert build_memory_controller(g).recall("x") == []


def test_context_policy_controls_exemplar_budget():
    ex = {"question": "Q", "answer": "step one.\nstep two.\nstep three.\n#### 1"}
    full = format_exemplar(ex, "full")
    trunc = format_exemplar(ex, "truncated")
    ans = format_exemplar(ex, "answer_only")
    assert "step one" in full
    assert "step one" not in trunc and "step three" in trunc
    assert "#### 1" in ans and "step" not in ans


def test_tfidf_prefers_relevant():
    scores = tfidf_scores("apple fruit", ["apple pie fruit", "quantum physics"])
    assert scores[0] > scores[1]


def test_unknown_memory_raises():
    g = ArchitectureGenome(memory="nonexistent")
    with pytest.raises(ValueError):
        build_memory_controller(g)


def test_every_gene_value_maps_to_a_real_mechanism():
    """Phase-17 Task 1 gate: genome values map to mechanisms, not labels."""
    from genome.search_space import SearchSpace
    from evaluator.memory import MEMORY_CONTROLLERS
    from evaluator.gsm8k import PROMPT_TEMPLATES

    space = SearchSpace()
    for value in space.memory:
        assert value in MEMORY_CONTROLLERS  # real controller class
    for value in space.reasoning:
        assert value in PROMPT_TEMPLATES  # real prompt strategy
    ex = {"question": "Q", "answer": "a\nb\n#### 1"}
    for value in space.context_policy:
        assert format_exemplar(ex, value)  # real rendering policy
    for value in space.quantization:
        assert value in ("fp16", "int8")  # real runtime quantization only


def test_legacy_gene_names_are_gone():
    """lora/qlora must not appear as context policies; attention/mamba
    (legacy memory names) must not be in the Phase-17 space."""
    from genome.search_space import SearchSpace
    space = SearchSpace()
    assert "lora" not in space.context_policy
    assert "qlora" not in space.context_policy
    assert "int8" not in space.context_policy
    assert "attention" not in space.memory
    assert "mamba" not in space.memory  # real gene is mamba2
