"""Phase-16/17: w/o-memory ablation, latency/token logging, cache isolation."""

import json
import os

import pytest

from genome.architecture import ArchitectureGenome
from evaluator.gsm8k import GSM8KEvaluator

FIXTURE = os.path.join(os.path.dirname(__file__),
                       "fixtures", "gsm8k_divergent.jsonl")
TRAIN_FIXTURE = os.path.join(os.path.dirname(__file__),
                             "fixtures", "gsm8k_train_fixture.jsonl")


def _ev(backend, **kw):
    kw.setdefault("calibration_path", TRAIN_FIXTURE)
    return GSM8KEvaluator(backend=backend, data_path=FIXTURE, **kw)


def test_disable_memory_ablation_no_exemplars():
    seen = []

    def backend(prompt, genome):
        seen.append(prompt)
        return "#### 0"

    ev = _ev(backend, disable_memory=True)
    metrics = ev.evaluate(ArchitectureGenome(memory="retrieval"), agent=None)
    assert metrics["memory_enabled"] is False
    # no exemplar block: train-bank answers must NOT appear in any prompt
    assert all("#### 120" not in p for p in seen)


def test_memory_enabled_injects_train_exemplars():
    seen = []

    def backend(prompt, genome):
        seen.append(prompt)
        return "#### 0"

    ev = _ev(backend, memory_k=1)
    metrics = ev.evaluate(ArchitectureGenome(memory="recency"), agent=None)
    assert metrics["memory_enabled"] is True
    # train-bank exemplars appear from the FIRST sample (bank is pre-filled)
    assert any("#### 120" in p for p in seen)


def test_metrics_include_latency_and_tokens():
    ev = _ev(lambda p, g: "#### 0")
    metrics = ev.evaluate(ArchitectureGenome(memory="recency"), agent=None)
    assert "latency_sec" in metrics
    assert metrics["prompt_tokens_total"] > 0


def test_cache_key_separates_memory_ablation(tmp_path):
    cache = str(tmp_path / "c.json")
    g = ArchitectureGenome(memory="recency")
    ev1 = _ev(lambda p, gg: "#### 0", cache_path=cache, disable_memory=False)
    ev2 = _ev(lambda p, gg: "#### 0", cache_path=cache, disable_memory=True)
    m1 = ev1.evaluate(g, agent=None)
    m2 = ev2.evaluate(g, agent=None)
    assert m1["memory_enabled"] != m2["memory_enabled"]
    stored = json.load(open(cache))
    assert len(stored) == 2


def test_cache_key_separates_substrate_fingerprint(tmp_path):
    cache = str(tmp_path / "c.json")
    g = ArchitectureGenome(memory="recency")
    ev1 = _ev(lambda p, gg: "#### 0", cache_path=cache)
    ev1.evaluate(g, agent=None)
    ev2 = _ev(lambda p, gg: "#### 0", cache_path=cache)
    ev2.evaluate(g, agent=None, substrate_fingerprint="adapted-abc123")
    stored = json.load(open(cache))
    assert len(stored) == 2
