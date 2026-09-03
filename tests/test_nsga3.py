"""Verify NSGA-III-style selection: sorting, fronts, diversity, selection."""

from evolution.nsga3 import (Individual, NSGA3Selector, dominates,
                             fast_non_dominated_sort, assign_crowding_distance)


def _ind(objs):
    return Individual(genome=None, objectives=list(objs))


def test_dominance():
    assert dominates(_ind([0.5, 0.5]), _ind([0.4, 0.5]))
    assert not dominates(_ind([0.5, 0.4]), _ind([0.4, 0.5]))
    assert not dominates(_ind([0.5, 0.5]), _ind([0.5, 0.5]))


def test_non_dominated_sorting():
    pop = [
        _ind([0.9, 0.1]),  # front 0
        _ind([0.1, 0.9]),  # front 0
        _ind([0.5, 0.5]),  # front 0
        _ind([0.4, 0.4]),  # dominated by [0.5, 0.5] -> front 1
        _ind([0.3, 0.3]),  # dominated by [0.4, 0.4] -> front 2
    ]
    fronts = fast_non_dominated_sort(pop)
    assert len(fronts) == 3
    assert [len(f) for f in fronts] == [3, 1, 1]
    assert {p.rank for p in fronts[0]} == {0}
    assert fronts[1][0].objectives == [0.4, 0.4]


def test_crowding_prefers_boundaries():
    front = [_ind([0.0]), _ind([0.5]), _ind([1.0])]
    assign_crowding_distance(front)
    by_obj = {p.objectives[0]: p.crowding for p in front}
    assert by_obj[0.0] == float("inf")
    assert by_obj[1.0] == float("inf")
    assert by_obj[0.5] < float("inf")


def test_environmental_selection_is_multi_objective():
    # A scalar-fitness search would drop the efficient-but-weak individual;
    # Pareto selection must keep it (non-dominated on efficiency).
    pop = [
        _ind([0.9, 0.1]),   # high capability, low efficiency
        _ind([0.1, 0.9]),   # low capability, high efficiency
        _ind([0.8, 0.05]),  # dominated by first
    ]
    selector = NSGA3Selector(population_size=2)
    selected = selector.select(pop, n_select=2)
    selected_objs = sorted(tuple(p.objectives) for p in selected)
    assert (0.1, 0.9) in selected_objs
    assert (0.9, 0.1) in selected_objs
    assert (0.8, 0.05) not in selected_objs


def test_selection_fills_by_fronts_then_crowding():
    pop = [_ind([i / 10.0, 1.0 - i / 10.0]) for i in range(10)]
    selector = NSGA3Selector(population_size=4)
    selected = selector.select(pop, n_select=4)
    assert len(selected) == 4
    # boundary points always survive crowding truncation
    first_coords = sorted(round(p.objectives[0], 6) for p in selected)
    assert first_coords[0] == 0.0
    assert first_coords[-1] == 0.9
