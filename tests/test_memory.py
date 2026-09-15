"""Verify Phase-15 real memory substrates: recall behavior, genome control."""

from genome.architecture import ArchitectureGenome
from evaluator.memory import (build_memory_controller, format_exemplar,
                              tfidf_scores)

HISTORY = [
    ("How much is 2 + 2?", "2 + 2 = 4.\n#### 4"),
    ("A train travels 60 km in 1 hour. Speed?", "60 km/h.\n#### 60"),
    ("What is the capital of France?", "Paris.\n#### Paris"),
]


def _fill(memory):
    for q, a in HISTORY:
        memory.store(q, a)
    return memory


def test_attention_recency_window():
    g = ArchitectureGenome(memory="attention")
    mem = _fill(build_memory_controller(g))
    out = mem.recall("anything", k=2)
    assert len(out) == 2
    assert out[-1]["question"] == HISTORY[-1][0]  # most recent last


def test_retrieval_similarity():
    g = ArchitectureGenome(memory="retrieval")
    mem = _fill(build_memory_controller(g))
    out = mem.recall("train speed km per hour", k=1)
    assert out[0]["question"] == HISTORY[1][0]


def test_mamba_recall_runs_and_returns_k():
    g = ArchitectureGenome(memory="mamba", hidden_size=32, state_size=8)
    mem = _fill(build_memory_controller(g))
    out = mem.recall("2 + 2", k=2)
    assert len(out) == 2
    assert all("question" in h for h in out)


def test_hybrid_includes_latest():
    g = ArchitectureGenome(memory="hybrid")
    mem = _fill(build_memory_controller(g))
    out = mem.recall("train speed", k=3)
    assert out[-1]["question"] == HISTORY[-1][0]


def test_empty_history_recall():
    g = ArchitectureGenome(memory="mamba", hidden_size=32, state_size=8)
    assert build_memory_controller(g).recall("x") == []


def test_compression_controls_exemplar_budget():
    ex = {"question": "Q", "answer": "step one.\nstep two.\nstep three.\n#### 1"}
    full = format_exemplar(ex, "none")
    lora = format_exemplar(ex, "lora")
    qlora = format_exemplar(ex, "qlora")
    assert "step one" in full
    assert "step one" not in lora and "step three" in lora
    assert "#### 1" in qlora and "step" not in qlora


def test_tfidf_prefers_relevant():
    scores = tfidf_scores("apple fruit", ["apple pie fruit", "quantum physics"])
    assert scores[0] > scores[1]


def test_unknown_memory_raises():
    import pytest
    g = ArchitectureGenome(memory="nonexistent")
    with pytest.raises(ValueError):
        build_memory_controller(g)
