"""
Crossover operators for Evolutionary Neural Substrate Search (ENSS).

Combines architecture genomes from multiple parent agents to create
new candidate neural substrates.
"""

from copy import deepcopy


class GenomeCrossover:
    def crossover(self, parent_a, parent_b):
        child = deepcopy(parent_a)

        # exchange cognitive modules
        if parent_b.memory != parent_a.memory:
            child.memory = parent_b.memory

        if parent_b.reasoning != parent_a.reasoning:
            child.reasoning = parent_b.reasoning

        if parent_b.tool_adapter != parent_a.tool_adapter:
            child.tool_adapter = parent_b.tool_adapter

        if parent_b.compression != parent_a.compression:
            child.compression = parent_b.compression

        return child
