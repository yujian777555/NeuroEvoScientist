"""Phase-16: w/o-memory ablation, latency/token logging, aggregation."""

import json
import os

import pytest

from genome.architecture import ArchitectureGenome
from evaluator.gsm8k import GSM8KEvaluator

FIXTURE = os.path.join(os.path.dirname(__file__),
                       "fixtures", "gsm8k_divergent.jsonl")


def test_disable_memory_ablation_no_exemplars():
    seen = []

    def backend(prompt, genome):
        seen.append(prompt)
        return "#### 0"

    ev = GSM8KEvaluator(backend=backend, data_path=FIXTURE,
                        disable_memory=True)
    metrics = ev.evaluate(ArchitectureGenome(memory="retrieval"), agent=None)
    assert metrics["memory_enabled"] is False
    # exemplar answers (from gold history) must NOT appear in later prompts
    assert all("#### 10" not in p for p in seen)


def test_memory_enabled_injects_exemplars():
    seen = []

    def backend(prompt, genome):
        seen.append(prompt)
        return "#### 0"

    ev = GSM8KEvaluator(backend=backend, data_path=FIXTURE, memory_k=1)
    metrics = ev.evaluate(ArchitectureGenome(memory="attention"), agent=None)
    assert metrics["memory_enabled"] is True
    # by the last sample, some gold exemplar answer leaked into the prompt
    assert any("#### 10" in p or "#### 60" in p for p in seen[1:])


def test_metrics_include_latency_and_tokens():
    ev = GSM8KEvaluator(backend=lambda p, g: "#### 0", data_path=FIXTURE)
    metrics = ev.evaluate(ArchitectureGenome(), agent=None)
    assert "latency_sec" in metrics
    assert metrics["prompt_tokens_total"] > 0


def test_cache_key_separates_memory_ablation(tmp_path):
    cache = str(tmp_path / "c.json")
    g = ArchitectureGenome()
    ev1 = GSM8KEvaluator(backend=lambda p, gg: "#### 0", data_path=FIXTURE,
                         cache_path=cache, disable_memory=False)
    ev2 = GSM8KEvaluator(backend=lambda p, gg: "#### 0", data_path=FIXTURE,
                         cache_path=cache, disable_memory=True)
    m1 = ev1.evaluate(g, agent=None)
    m2 = ev2.evaluate(g, agent=None)
    assert m1["memory_enabled"] != m2["memory_enabled"]
    stored = json.load(open(cache))
    assert len(stored) == 2
