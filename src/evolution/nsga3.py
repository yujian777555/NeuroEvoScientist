"""
NSGA-III style multi-objective evolutionary selection.

This module implements the core optimization idea of EvoScientist-Mamba:
searching adaptive neural substrates under multiple objectives.

Objectives:
- capability
- efficiency
- memory cost
- adaptability
"""

from dataclasses import dataclass
from typing import List


@dataclass
class Individual:
    genome: object
    objectives: List[float]


class NSGA3Selector:
    def __init__(self, population_size: int):
        self.population_size = population_size

    def dominates(self, a: Individual, b: Individual):
        """Return whether a dominates b on all objectives."""
        better_or_equal = all(
            x >= y for x, y in zip(a.objectives, b.objectives)
        )
        strictly_better = any(
            x > y for x, y in zip(a.objectives, b.objectives)
        )
        return better_or_equal and strictly_better

    def select(self, population: List[Individual]):
        """Simple Pareto front selection.

        Can be extended with reference-point niching from full NSGA-III.
        """
        front = []
        for candidate in population:
            dominated = False
            for other in population:
                if self.dominates(other, candidate):
                    dominated = True
                    break
            if not dominated:
                front.append(candidate)

        return front[: self.population_size]
