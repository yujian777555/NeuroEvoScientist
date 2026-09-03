"""
Mutation operators for Neural Substrate Evolution.

Phase-12: mutations stay inside the configured search space
(memory / reasoning / compression as defined in configs/search_space.yaml).
"""

import random
from copy import deepcopy


def mutate(genome, search_space, rng=None):
    """Return a mutated copy of ``genome`` within the search space."""
    rng = rng or random
    child = deepcopy(genome)
    target = rng.choice(["memory", "reasoning", "compression"])

    options = search_space.options_for(target)
    alternatives = [v for v in options if v != getattr(genome, target)]
    if alternatives:
        setattr(child, target, rng.choice(alternatives))

    return child
