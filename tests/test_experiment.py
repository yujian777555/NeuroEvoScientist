"""Verify Phase-14 experiment infrastructure: baselines, ablations, logging."""

import json
import os

from genome.search_space import SearchSpace
from evaluator.benchmark import get_evaluator
from evaluator.experiment_logger import ExperimentLogger
from evolution.controller import EvolutionController
from evolution.random_search import RandomSearchController


def _setup(**kwargs):
    space = SearchSpace()
    evaluator = get_evaluator("mock")
    return space, evaluator, kwargs


def test_random_search_runs_and_stays_in_space():
    space, evaluator, kw = _setup()
    rs = RandomSearchController(space, evaluator, population_size=4,
                                generations=3, seed=0)
    rs.run()
    for g in range(len(rs.history)):
        for e in rs.history[g]:
            assert e.genome.memory in space.memory
            assert e.genome.reasoning in space.reasoning
            assert e.genome.compression in space.compression
    assert len(rs.history) == 3


def test_no_pareto_ablation_runs():
    space, evaluator, kw = _setup()
    controller = EvolutionController(space, evaluator, population_size=6,
                                     generations=3, seed=0, use_pareto=False)
    best = controller.run()
    assert best.fitness > 0
    assert len(controller.history) == 3


def test_no_mamba_ablation_excludes_mamba():
    space = SearchSpace(exclude={"memory": ["mamba"]})
    assert "mamba" not in space.memory
    assert len(space.enumerate_architectures()) == 48


def test_experiment_logger_writes_history_and_results(tmp_path):
    space, evaluator, kw = _setup()
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
                "architecture_distribution"):
        assert key in rec
    assert summary["best_architecture"] == best.genome.describe()
    assert os.path.exists(os.path.join(logger.run_dir, "results.json"))
