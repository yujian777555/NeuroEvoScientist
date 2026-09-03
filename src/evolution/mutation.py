"""
Mutation operators for Neural Substrate Evolution.
"""

import random
from copy import deepcopy


MEMORY = ["mamba", "attention", "retrieval", "hybrid"]
REASONING = ["attention", "moe", "tree_search", "verifier"]
COMPRESSION = ["none", "int8", "lora"]


def mutate(genome):
    child = deepcopy(genome)
    target = random.choice(genome.mutate_target())

    if target == "memory":
        child.memory = random.choice(MEMORY)
    elif target == "reasoning":
        child.reasoning = random.choice(REASONING)
    elif target == "compression":
        child.compression = random.choice(COMPRESSION)

    return child
