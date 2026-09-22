"""Phase-20 structured search space (hierarchical, conditional genes).

Loads configs/phase20_structured_search_space.yaml. Sampling produces
normalized StructuredGenome phenotypes; conditional genes are active only
where semantically valid.
"""

import os
import random

from .structured import StructuredGenome

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

DEFAULT_CONFIG = os.path.join(
    os.path.dirname(__file__), "..", "..", "configs",
    "phase20_structured_search_space.yaml"
)

_FALLBACK = {
    "memory": {"type": ["recency", "retrieval", "mamba2", "hybrid"],
               "k": [1, 2, 3, 4, 6, 8],
               "retrieval_metric": ["tfidf", "dense"],
               "state_size": [32, 64, 128, 256],
               "hybrid_retrieval_fraction": [0.25, 0.5, 0.75]},
    "reasoning": {"strategy": ["direct", "cot", "verify", "planner"],
                  "depth": [1, 2, 3, 4],
                  "verifier_passes": [0, 1, 2]},
    "context_policy": {"mode": ["full", "truncated", "answer_only"],
                       "token_budget": [128, 256, 512, 768, 1024],
                       "exemplar_count": [0, 1, 2, 3, 4, 6, 8]},
    "adaptation": {"enabled": [False, True], "steps": [0, 10, 20, 40]},
    "population": 16,
    "generations": 10,
    "objectives": {"capability": 0.5, "efficiency": 0.3, "adaptability": 0.2},
}


class StructuredSearchSpace:
    def __init__(self, config_path=None):
        path = config_path or DEFAULT_CONFIG
        if yaml is not None and os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
        else:
            cfg = _FALLBACK
        self.memory = cfg["memory"]
        self.reasoning = cfg["reasoning"]
        self.context_policy = cfg["context_policy"]
        self.adaptation = cfg["adaptation"]
        self.population = int(cfg.get("population", 16))
        self.generations = int(cfg.get("generations", 10))
        self.objective_weights = dict(cfg.get("objectives",
                                              _FALLBACK["objectives"]))

    def sample(self, rng: random.Random) -> StructuredGenome:
        """Sample a random genome, then normalize (conditional validity)."""
        g = StructuredGenome(
            memory_type=rng.choice(self.memory["type"]),
            memory_k=rng.choice(self.memory["k"]),
            retrieval_metric=rng.choice(self.memory["retrieval_metric"]),
            mamba_state_size=rng.choice(self.memory["state_size"]),
            hybrid_fraction=rng.choice(
                self.memory["hybrid_retrieval_fraction"]),
            reasoning=rng.choice(self.reasoning["strategy"]),
            reasoning_depth=rng.choice(self.reasoning["depth"]),
            verifier_passes=rng.choice(self.reasoning["verifier_passes"]),
            context_mode=rng.choice(self.context_policy["mode"]),
            token_budget=rng.choice(self.context_policy["token_budget"]),
            exemplar_count=rng.choice(
                self.context_policy["exemplar_count"]),
            adaptation_enabled=rng.choice(self.adaptation["enabled"]),
            adaptation_steps=rng.choice(self.adaptation["steps"]),
        )
        return g.normalize()

    def neighbors(self, values, current):
        """Ordered-neighbor helper for local mutation."""
        if current not in values:
            return values
        i = values.index(current)
        out = []
        if i > 0:
            out.append(values[i - 1])
        if i < len(values) - 1:
            out.append(values[i + 1])
        return out
