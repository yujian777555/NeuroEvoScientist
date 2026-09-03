"""
Multi-objective fitness for evolutionary agents.

Objectives:
- capability
- efficiency
- adaptability
"""


def calculate_fitness(result):
    capability = result.get("capability", 0)
    efficiency = result.get("efficiency", 0)
    adaptability = result.get("adaptability", 0)

    return (
        0.5 * capability
        + 0.3 * efficiency
        + 0.2 * adaptability
    )
