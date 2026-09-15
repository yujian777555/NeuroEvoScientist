"""Search space definition for ENSS.

Loads ``configs/search_space.yaml`` and exposes the combinatorial space of
agent cognitive architectures (Phase-13: 4 x 4 x 4 = 64 architectures).
Supports ablation subsets via ``exclude`` (e.g. "w/o Mamba memory").
"""

import itertools
import os

try:
    import yaml
except ImportError:  # pragma: no cover - yaml is optional
    yaml = None


DEFAULT_CONFIG = os.path.join(
    os.path.dirname(__file__), "..", "..", "configs", "search_space.yaml"
)

# Fallback matching configs/search_space.yaml when PyYAML is unavailable.
_FALLBACK = {
    "memory": ["attention", "mamba", "retrieval", "hybrid"],
    "reasoning": ["direct", "verify", "planner", "cot"],
    "compression": ["none", "lora", "qlora", "int8"],
    "population": 16,
    "generations": 10,
    "objectives": {"capability": 0.5, "efficiency": 0.3, "adaptability": 0.2},
}

MODULE_FIELDS = ["memory", "reasoning", "compression"]


class SearchSpace:
    """Combinatorial architecture search space.

    Args:
        config_path: override path to a search-space YAML.
        exclude:     optional {field: [values]} ablation filter, e.g.
                     ``{"memory": ["mamba"]}`` for the w/o-Mamba ablation.
    """

    def __init__(self, config_path=None, exclude=None):
        config = self._load_config(config_path or DEFAULT_CONFIG)
        exclude = exclude or {}
        self.memory = self._filter(config["memory"], exclude, "memory")
        self.reasoning = self._filter(config["reasoning"], exclude, "reasoning")
        self.compression = self._filter(config["compression"], exclude,
                                        "compression")
        self.population = int(config.get("population", 16))
        self.generations = int(config.get("generations", 10))
        self.objective_weights = dict(
            config.get("objectives", _FALLBACK["objectives"])
        )

    @staticmethod
    def _filter(values, exclude, field):
        kept = [v for v in values if v not in exclude.get(field, [])]
        if not kept:
            raise ValueError("exclusion emptied search-space field: %s"
                             % field)
        return kept

    @staticmethod
    def _load_config(config_path):
        if yaml is not None and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return dict(_FALLBACK)

    def options_for(self, field):
        """Return the allowed values for a genome module field."""
        return list(getattr(self, field))

    def enumerate_architectures(self):
        """Return all valid module combinations (64 in Phase-13)."""
        combos = itertools.product(self.memory, self.reasoning, self.compression)
        return [
            dict(zip(MODULE_FIELDS, combo))
            for combo in combos
        ]

    def sample(self, rng):
        """Sample one random architecture genome dict."""
        return {
            field: rng.choice(self.options_for(field))
            for field in MODULE_FIELDS
        }
