"""Verify the Phase-17 search space: 48 architectures, legal sampling."""

import random

from genome.search_space import SearchSpace
from genome.architecture import ArchitectureGenome
from models.builder import build_agent
from models.mamba_memory import mamba2_available


def test_space_size():
    space = SearchSpace()
    combos = space.enumerate_architectures()
    # 4 memory x 4 reasoning x 3 context_policy x 1 quantization (fp16 only
    # until real int8 inference is enabled)
    assert len(combos) == 48
    assert len({tuple(sorted(c.items())) for c in combos}) == 48


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
        if combo["memory"] == "mamba2" and not mamba2_available():
            continue  # real substrate requires transformers>=4.44 (VM)
        genome = ArchitectureGenome(**combo)
        agent = build_agent(genome)
        assert agent.num_parameters() > 0
        assert 0 < agent.effective_parameters() <= agent.num_parameters()


def test_no_mamba2_ablation():
    space = SearchSpace(exclude={"memory": ["mamba2"]})
    assert "mamba2" not in space.memory
    assert len(space.enumerate_architectures()) == 36
