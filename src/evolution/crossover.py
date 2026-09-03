"""
Crossover operators for Evolutionary Neural Substrate Search (ENSS).

Combines architecture genomes from two parent agents via uniform
module-level crossover.
"""

import random
from copy import deepcopy


FIELDS = ["memory", "reasoning", "tool_adapter", "compression"]


def crossover(parent_a, parent_b, rng=None):
    """Uniform crossover: each module is taken from either parent."""
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
