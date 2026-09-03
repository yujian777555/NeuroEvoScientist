"""
Multi-objective fitness for evolutionary agents.

Objectives:
- capability
- efficiency
- adaptability

Scalarized with configurable weights (defaults from configs/search_space.yaml).
"""

DEFAULT_WEIGHTS = {"capability": 0.5, "efficiency": 0.3, "adaptability": 0.2}


def calculate_fitness(result, weights=None):
    weights = weights or DEFAULT_WEIGHTS
    return (
        weights.get("capability", 0.5) * result.get("capability", 0)
        + weights.get("efficiency", 0.3) * result.get("efficiency", 0)
        + weights.get("adaptability", 0.2) * result.get("adaptability", 0)
    )
