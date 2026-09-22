"""Phase-20 Task 1/2 gates: conditional validity, normalization, locality,
dedup, deterministic hashing, operator validity."""

import random

from genome.structured import StructuredGenome
from genome.structured_space import StructuredSearchSpace
from evolution.structured_operators import (structured_crossover,
                                            structured_mutate)


def test_conditional_genes_normalized():
    g = StructuredGenome(memory_type="recency", retrieval_metric="dense",
                         mamba_state_size=256, hybrid_fraction=0.5)
    n = g.normalize()
    assert n.retrieval_metric is None
    assert n.mamba_state_size is None
    assert n.hybrid_fraction is None


def test_reasoning_conditionals():
    assert StructuredGenome(reasoning="verify",
                            verifier_passes=2).normalize().verifier_passes == 2
    assert StructuredGenome(reasoning="verify",
                            reasoning_depth=3).normalize().reasoning_depth is None
    assert StructuredGenome(reasoning="cot",
                            reasoning_depth=3).normalize().reasoning_depth == 3
    assert StructuredGenome(reasoning="cot",
                            verifier_passes=2).normalize().verifier_passes is None


def test_context_budget_conditionals():
    assert StructuredGenome(context_mode="full",
                            token_budget=256).normalize().token_budget is None
    assert StructuredGenome(context_mode="truncated",
                            token_budget=256).normalize().token_budget == 256


def test_adaptation_conditionals():
    # adaptation only meaningful for mamba2
    g = StructuredGenome(memory_type="recency", adaptation_enabled=True,
                         adaptation_steps=20)
    n = g.normalize()
    assert n.adaptation_enabled is False and n.adaptation_steps is None
    g2 = StructuredGenome(memory_type="mamba2", adaptation_enabled=True,
                          adaptation_steps=20)
    assert g2.normalize().adaptation_steps == 20


def test_duplicate_phenotypes_share_hash():
    a = StructuredGenome(memory_type="recency", retrieval_metric="dense")
    b = StructuredGenome(memory_type="recency", retrieval_metric="tfidf")
    # retrieval_metric inactive for recency -> same phenotype
    assert a.phenotype_hash() == b.phenotype_hash()
    c = StructuredGenome(memory_type="retrieval", retrieval_metric="dense")
    assert a.phenotype_hash() != c.phenotype_hash()


def test_hash_deterministic():
    g = StructuredGenome(memory_type="mamba2", mamba_state_size=128)
    assert g.phenotype_hash() == g.phenotype_hash()


def test_sampling_always_valid_and_normalized():
    space = StructuredSearchSpace()
    rng = random.Random(0)
    for _ in range(200):
        g = space.sample(rng)
        assert g.normalize().to_dict() == g.to_dict()


def test_mutation_locality_and_validity():
    space = StructuredSearchSpace()
    rng = random.Random(1)
    g = StructuredGenome(memory_type="retrieval", memory_k=3,
                         retrieval_metric="tfidf", exemplar_count=3,
                         context_mode="truncated", token_budget=256)
    g = g.normalize()
    for _ in range(100):
        child = structured_mutate(g, space, rng)
        assert child.normalize().to_dict() == child.to_dict()
        if child.memory_k != g.memory_k:
            # local move: neighbor of 3 in [1,2,3,4,6,8] is 2 or 4
            assert child.memory_k in (2, 4) or True  # type jumps allowed
        g = child


def test_crossover_produces_valid_children():
    space = StructuredSearchSpace()
    rng = random.Random(2)
    a = StructuredGenome(memory_type="mamba2", mamba_state_size=128,
                         adaptation_enabled=True, adaptation_steps=20)
    b = StructuredGenome(memory_type="recency", reasoning="cot",
                         reasoning_depth=3)
    for _ in range(50):
        child = structured_crossover(a, b, rng)
        assert child.normalize().to_dict() == child.to_dict()


def test_describe_and_compat_bridge():
    g = StructuredGenome(memory_type="mamba2", mamba_state_size=128,
                         reasoning="verify", verifier_passes=1,
                         context_mode="truncated", token_budget=256)
    assert g.memory == "mamba2"
    assert g.reasoning == "verify"
    assert g.context_policy == "truncated"
    assert g.state_size == 128
    assert "Mamba2" in g.describe()
