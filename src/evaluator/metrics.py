"""Metrics for candidate agent evaluation.

Objectives (all in [0, 1], higher is better):
- capability:    mean task score
- efficiency:    blend of parameter-footprint proxy and, when measured,
                 real prompt-token cost (Phase-15: compression and memory
                 genes change the context budget, hence real inference cost)
- adaptability:  mean score on distribution-shifted tasks
"""

# Parameter count at which the param proxy saturates to ~0.5.
_EFFICIENCY_SCALE = 4.0e6

# Average prompt tokens per problem at which the token proxy is ~0.5.
_TOKEN_SCALE = 1024.0


def compute_metrics(agent, task_scores, shifted_scores=None,
                    prompt_tokens=None, n_prompts=None):
    capability = sum(task_scores) / max(1, len(task_scores))

    if agent is None:
        n_params = _EFFICIENCY_SCALE
    elif hasattr(agent, "effective_parameters"):
        n_params = agent.effective_parameters()
    else:
        n_params = agent.num_parameters()
    param_eff = 1.0 / (1.0 + n_params / _EFFICIENCY_SCALE)

    if prompt_tokens is not None and n_prompts:
        avg_tokens = prompt_tokens / n_prompts
        token_eff = 1.0 / (1.0 + avg_tokens / _TOKEN_SCALE)
        efficiency = 0.5 * param_eff + 0.5 * token_eff
    else:
        efficiency = param_eff

    if shifted_scores:
        adaptability = sum(shifted_scores) / len(shifted_scores)
    else:
        adaptability = capability

    return {
        "capability": capability,
        "efficiency": efficiency,
        "adaptability": adaptability,
    }
