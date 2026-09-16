"""
Crossover operators for Evolutionary Neural Substrate Search (ENSS).

Combines architecture genomes from two parent agents via uniform
gene-level crossover over the Phase-17 schema.
"""

import random
from copy import deepcopy


FIELDS = ["memory", "reasoning", "context_policy", "quantization"]


def crossover(parent_a, parent_b, rng=None):
    """Uniform crossover: each gene is taken from either parent."""
    rng = rng or random
    child = deepcopy(parent_a)
    for field in FIELDS:
        if rng.random() < 0.5:
            setattr(child, field, getattr(parent_b, field))
    return child


class GenomeCrossover:
    """Backwards-compatible class wrapper."""

    def crossover(self, parent_a, parent_b):
        return crossover(parent_a, parent_b)
