"""Verify experiment infrastructure: baselines, ablations, logging."""

import json
import os

import pytest

from genome.search_space import SearchSpace
from evaluator.benchmark import get_evaluator
from evaluator.experiment_logger import ExperimentLogger
from evolution.controller import EvolutionController
from evolution.random_search import RandomSearchController
from models.mamba_memory import mamba2_available

# The CPU dev box cannot construct the real Mamba2 substrate (needs
# transformers>=4.44); exclude it locally, the VM runs the full space.
_EXCLUDE = None if mamba2_available() else {"memory": ["mamba2"]}


def _space():
    return SearchSpace(exclude=_EXCLUDE)


def test_random_search_runs_and_stays_in_space():
    space = _space()
    evaluator = get_evaluator("mock")
    rs = RandomSearchController(space, evaluator, population_size=4,
                                generations=3, seed=0)
    rs.run()
    assert len(rs.history) == 3
    for gen in rs.history:
        for e in gen:
            assert e.genome.memory in space.memory
            assert e.genome.reasoning in space.reasoning
            assert e.genome.context_policy in space.context_policy
            assert e.genome.quantization in space.quantization


def test_no_pareto_ablation_runs():
    space = _space()
    evaluator = get_evaluator("mock")
    controller = EvolutionController(space, evaluator, population_size=6,
                                     generations=3, seed=0, use_pareto=False)
    best = controller.run()
    assert best.fitness > 0
    assert len(controller.history) == 3


def test_no_mamba2_ablation_excludes_mamba2():
    space = SearchSpace(exclude={"memory": ["mamba2"]})
    assert "mamba2" not in space.memory
    assert len(space.enumerate_architectures()) == 36


def test_experiment_logger_writes_history_and_results(tmp_path):
    space = _space()
    evaluator = get_evaluator("mock")
    logger = ExperimentLogger("pytest_run", base_dir=str(tmp_path),
                              config={"method": "enss"})
    controller = EvolutionController(space, evaluator, population_size=4,
                                     generations=2, seed=0)
    best = controller.run(
        on_generation=lambda g, e: logger.log_generation(g, e))
    summary = logger.finalize(best)

    with open(os.path.join(logger.run_dir, "history.jsonl")) as f:
        records = [json.loads(line) for line in f]
    assert len(records) == 2
    rec = records[0]
    for key in ("generation", "best_fitness", "mean_fitness",
                "best_architecture", "pareto_front",
                "architecture_distribution", "population"):
        assert key in rec
    # Phase-17: raw per-individual objectives persisted
    ind = rec["population"][0]
    for key in ("genome", "capability", "efficiency", "adaptability",
                "fitness"):
        assert key in ind
    assert summary["best_architecture"] == best.genome.describe()
    assert os.path.exists(os.path.join(logger.run_dir, "results.json"))
