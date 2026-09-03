"""Metrics for candidate agent evaluation.

Objectives (all in [0, 1], higher is better):
- capability:    mean task score
- efficiency:    parameter-count proxy (fewer effective params -> higher)
- adaptability:  mean score on distribution-shifted tasks
"""

# Parameter count at which efficiency saturates to ~0.5.
_EFFICIENCY_SCALE = 4.0e6


def compute_metrics(agent, task_scores, shifted_scores=None):
    capability = sum(task_scores) / max(1, len(task_scores))

    n_params = agent.num_parameters() if agent is not None else _EFFICIENCY_SCALE
    efficiency = 1.0 / (1.0 + n_params / _EFFICIENCY_SCALE)

    if shifted_scores:
        adaptability = sum(shifted_scores) / len(shifted_scores)
    else:
        adaptability = capability

    return {
        "capability": capability,
        "efficiency": efficiency,
        "adaptability": adaptability,
    }
