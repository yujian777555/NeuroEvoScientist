"""Verify the Phase-13 search space: 64 architectures, legal sampling."""

import random

from genome.search_space import SearchSpace
from genome.architecture import ArchitectureGenome
from models.builder import build_agent


def test_space_has_64_architectures():
    space = SearchSpace()
    combos = space.enumerate_architectures()
    assert len(combos) == 64
    assert len({tuple(sorted(c.items())) for c in combos}) == 64


def test_sampling_stays_in_space():
    space = SearchSpace()
    rng = random.Random(0)
    valid = {tuple(sorted(c.items())) for c in space.enumerate_architectures()}
    for _ in range(50):
        sample = space.sample(rng)
        assert tuple(sorted(sample.items())) in valid


def test_every_architecture_builds():
    space = SearchSpace()
    for combo in space.enumerate_architectures():
        genome = ArchitectureGenome(hidden_size=32, state_size=8, **combo)
        agent = build_agent(genome)
        assert agent.num_parameters() > 0
        assert 0 < agent.effective_parameters() <= agent.num_parameters()
