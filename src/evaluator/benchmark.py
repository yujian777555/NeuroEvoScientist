"""Benchmark evaluators for ENSS candidate agents.

Phase-12 ships a deterministic MockEvaluator so the evolution loop can be
validated end-to-end on CPU. The registry interface is the stable contract;
real benchmarks (GSM8K, AgentBench, PubMedQA) plug in later via
``register_benchmark`` without touching the evolution code.
"""

import hashlib
import json
import random

from .metrics import compute_metrics


def _stable_seed(genome, salt=""):
    """Deterministic seed from genome content (same genome -> same scores)."""
    payload = json.dumps(genome.to_dict(), sort_keys=True) + salt
    return int(hashlib.sha256(payload.encode("utf-8")).hexdigest(), 16) % (2 ** 32)


class MockEvaluator:
    """Deterministic pseudo-task evaluator.

    Scores are functions of the genome with per-module priors plus seeded
    noise, so evolution has a real (if synthetic) signal to optimize and
    results are reproducible.
    """

    # Capability priors over the Phase-13 64-architecture space.
    CAPABILITY_PRIOR = {
        "memory": {"mamba": 0.08, "attention": 0.05, "retrieval": 0.06,
                   "hybrid": 0.10},
        "reasoning": {"verify": 0.12, "direct": 0.0, "planner": 0.10,
                      "cot": 0.09},
    }
    # Adaptability prior: compression helps transfer under shift.
    ADAPTABILITY_PRIOR = {
        "compression": {"lora": 0.10, "none": 0.0, "qlora": 0.09,
                        "int8": 0.04},
    }

    def __init__(self, n_tasks=8):
        self.n_tasks = n_tasks

    def evaluate(self, genome, agent):
        """Return metrics dict {capability, efficiency, adaptability}."""
        rng = random.Random(_stable_seed(genome))

        capability = 0.45
        capability += self.CAPABILITY_PRIOR["memory"].get(genome.memory, 0.0)
        capability += self.CAPABILITY_PRIOR["reasoning"].get(genome.reasoning, 0.0)
        task_scores = [
            min(1.0, max(0.0, capability + rng.uniform(-0.08, 0.08)))
            for _ in range(self.n_tasks)
        ]

        adaptability = 0.40
        adaptability += self.ADAPTABILITY_PRIOR["compression"].get(
            genome.compression, 0.0
        )
        shifted_scores = [
            min(1.0, max(0.0, adaptability + rng.uniform(-0.08, 0.08)))
            for _ in range(self.n_tasks)
        ]

        return compute_metrics(agent, task_scores, shifted_scores)


def _not_implemented(name):
    class _Placeholder:
        def evaluate(self, genome, agent):
            raise NotImplementedError(
                "%s benchmark is not wired up yet (Phase-12 uses 'mock')" % name
            )
    _Placeholder.__name__ = name.title() + "Evaluator"
    return _Placeholder


def _gsm8k_factory():
    """Lazy import so the registry has no hard dependency on gsm8k module."""
    from .gsm8k import GSM8KEvaluator
    return GSM8KEvaluator


BENCHMARKS = {
    "mock": MockEvaluator,
    "gsm8k": _gsm8k_factory(),
    # Future real benchmarks — reserved names, same interface.
    "agentbench": _not_implemented("agentbench"),
    "pubmedqa": _not_implemented("pubmedqa"),
}


def register_benchmark(name, evaluator_cls):
    """Register an evaluator class under ``name``."""
    BENCHMARKS[name] = evaluator_cls


def get_evaluator(name="mock"):
    """Instantiate the evaluator registered under ``name``."""
    if name not in BENCHMARKS:
        raise KeyError("unknown benchmark: %s (have: %s)"
                       % (name, ", ".join(sorted(BENCHMARKS))))
    return BENCHMARKS[name]()
