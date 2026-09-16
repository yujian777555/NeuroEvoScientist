"""
Mutation operators for Neural Substrate Evolution.

Mutations stay inside the configured search space (all genome fields from
ArchitectureGenome.mutate_target(), values from the SearchSpace config).
"""

import random
from copy import deepcopy


def mutate(genome, search_space, rng=None):
    """Return a mutated copy of ``genome`` within the search space."""
    rng = rng or random
    child = deepcopy(genome)
    target = rng.choice(genome.mutate_target())

    options = search_space.options_for(target)
    alternatives = [v for v in options if v != getattr(genome, target)]
    if alternatives:
        setattr(child, target, rng.choice(alternatives))

    return child
