"""Phase-18: search-efficiency audit primitives (offline, CPU)."""

import pytest

from scripts.analyze_search_efficiency import (Oracle, enss_policy, gene_key,
                                               hypervolume_2d,
                                               random_policy)
from genome.architecture import ArchitectureGenome
from genome.search_space import SearchSpace


def test_hypervolume_2d_known_answer():
    # front: (1,0) (0.5,0.5) (0,1) with ref (0,0); (0.3,0.3) is dominated
    # descending x: (1,0): 1*(0-0)=0; (0.5,0.5): 0.5*(0.5-0)=0.25; (0,1): 0
    pts = [(1.0, 0.0), (0.5, 0.5), (0.0, 1.0), (0.3, 0.3)]
    assert hypervolume_2d(pts) == pytest.approx(0.25)


def test_hypervolume_empty_and_single():
    assert hypervolume_2d([]) == 0.0
    assert hypervolume_2d([(0.5, 0.5)]) == pytest.approx(0.25)


def _fake_table():
    space = SearchSpace()
    table = {}
    for i, combo in enumerate(space.enumerate_architectures()):
        table[gene_key(combo)] = (0.3 + (i % 7) * 0.05, 0.4 + (i % 5) * 0.05)
    return table


def test_oracle_online_constraint():
    """Policies may only ever look up budgeted points (KeyError guards any
    out-of-space access)."""
    table = _fake_table()
    oracle = Oracle(table)
    space = SearchSpace()
    evaluated, curve = random_policy(oracle, space, budget=12, seed=0)
    assert len(evaluated) == 12
    assert len(curve) == 12
    evaluated_e, _ = enss_policy(oracle, space, budget=12, seed=0)
    assert 0 < len(evaluated_e) <= 12


def test_enss_policy_deterministic_per_seed():
    table = _fake_table()
    oracle = Oracle(table)
    space = SearchSpace()
    a, _ = enss_policy(oracle, space, budget=16, seed=3)
    b, _ = enss_policy(oracle, space, budget=16, seed=3)
    assert a == b
