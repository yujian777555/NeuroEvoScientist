"""
NSGA-III style multi-objective selection for ENSS.

Implements the pieces Phase-13 requires to keep ENSS a genuine
multi-objective search rather than single-score genetic search:

- fast non-dominated sorting (Pareto fronts)
- crowding-distance diversity preservation within a front
- environmental selection across fronts
- binary tournament on (rank, crowding distance) for mating

All objectives are assumed to be maximized. Reference-point niching from
full NSGA-III can replace crowding distance when objective count grows.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Individual:
    genome: object
    objectives: List[float]
    rank: int = 0
    crowding: float = 0.0
    payload: object = None  # optional back-reference (e.g. EvaluatedAgent)


def dominates(a, b):
    """True if a Pareto-dominates b (all objectives maximized)."""
    better_or_equal = all(x >= y for x, y in zip(a.objectives, b.objectives))
    strictly_better = any(x > y for x, y in zip(a.objectives, b.objectives))
    return better_or_equal and strictly_better


def fast_non_dominated_sort(population: List[Individual]) -> List[List[Individual]]:
    """Sort population into Pareto fronts (front 0 = non-dominated)."""
    domination_counts = {id(p): 0 for p in population}
    dominated_sets = {id(p): [] for p in population}
    fronts = [[]]

    for p in population:
        for q in population:
            if p is q:
                continue
            if dominates(p, q):
                dominated_sets[id(p)].append(q)
            elif dominates(q, p):
                domination_counts[id(p)] += 1
        if domination_counts[id(p)] == 0:
            p.rank = 0
            fronts[0].append(p)

    i = 0
    while i < len(fronts) and fronts[i]:
        nxt = []
        for p in fronts[i]:
            for q in dominated_sets[id(p)]:
                domination_counts[id(q)] -= 1
                if domination_counts[id(q)] == 0:
                    q.rank = i + 1
                    nxt.append(q)
        if nxt:
            fronts.append(nxt)
        i += 1
    return fronts


def assign_crowding_distance(front: List[Individual]) -> None:
    """Crowding distance within one front (diversity preservation)."""
    n = len(front)
    if n == 0:
        return
    for p in front:
        p.crowding = 0.0
    n_obj = len(front[0].objectives)

    for m in range(n_obj):
        front.sort(key=lambda p: p.objectives[m])
        front[0].crowding = front[-1].crowding = float("inf")
        f_min = front[0].objectives[m]
        f_max = front[-1].objectives[m]
        span = f_max - f_min
        if span == 0:
            continue
        for i in range(1, n - 1):
            front[i].crowding += (
                front[i + 1].objectives[m] - front[i - 1].objectives[m]
            ) / span


class NSGA3Selector:
    def __init__(self, population_size: int):
        self.population_size = population_size

    def dominates(self, a: Individual, b: Individual):
        return dominates(a, b)

    def select(self, population: List[Individual],
               n_select: int = None) -> List[Individual]:
        """Environmental selection: fill by fronts, break ties by crowding."""
        n_select = n_select or self.population_size
        fronts = fast_non_dominated_sort(population)

        selected = []
        for front in fronts:
            if len(selected) + len(front) <= n_select:
                selected.extend(front)
            else:
                assign_crowding_distance(front)
                front.sort(key=lambda p: p.crowding, reverse=True)
                selected.extend(front[: n_select - len(selected)])
                break
        return selected

    def tournament(self, a: Individual, b: Individual) -> Individual:
        """Binary tournament on (rank, crowding distance)."""
        if a.rank != b.rank:
            return a if a.rank < b.rank else b
        if a.crowding != b.crowding:
            return a if a.crowding > b.crowding else b
        return a
