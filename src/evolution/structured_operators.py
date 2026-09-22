"""Phase-20 Task 2: structure-aware evolutionary operators.

- Local mutation: ordered sub-genes move to NEIGHBORING values by default
  (memory.k 3->4, token_budget 256->512); type genes re-activate dependent
  sub-genes consistently; every child is normalized before evaluation.
- Block crossover: swap semantic blocks (memory/reasoning/context/
  adaptation) then normalize; invalid children never reach evaluation.
- Phenotype dedup: identical normalized phenotypes are the same candidate.
"""

import random
from dataclasses import asdict

from genome.structured import StructuredGenome

# ordered sub-gene fields -> their ordered option lists (from the space)
_LOCAL_FIELDS = {
    "memory_k": "k",
    "mamba_state_size": "state_size",
    "reasoning_depth": "depth",
    "verifier_passes": "verifier_passes",
    "token_budget": "token_budget",
    "exemplar_count": "exemplar_count",
    "adaptation_steps": "steps",
    "memory_type": "type",
    "retrieval_metric": "retrieval_metric",
    "hybrid_fraction": "hybrid_retrieval_fraction",
    "reasoning": "strategy",
    "context_mode": "mode",
    "adaptation_enabled": "enabled",
}

# genes whose mutation is a categorical jump (type-level), rest are local
_TYPE_FIELDS = {"memory_type", "reasoning", "context_mode",
                "retrieval_metric", "hybrid_fraction", "adaptation_enabled"}

_BLOCKS = {
    "memory": ["memory_type", "memory_k", "retrieval_metric",
               "mamba_state_size", "hybrid_fraction"],
    "reasoning": ["reasoning", "reasoning_depth", "verifier_passes"],
    "context": ["context_mode", "token_budget", "exemplar_count"],
    "adaptation": ["adaptation_enabled", "adaptation_steps"],
}


def structured_mutate(genome: StructuredGenome, space, rng: random.Random,
                      local_prob=0.8) -> StructuredGenome:
    """Local-first mutation on the structured genome."""
    g = StructuredGenome(**asdict(genome))
    field = rng.choice(list(_LOCAL_FIELDS))
    options = _options_for(field, space)

    if field in _TYPE_FIELDS or rng.random() > local_prob:
        current = getattr(g, field)
        choices = [v for v in options if v != current]
        if choices:
            setattr(g, field, rng.choice(choices))
    else:
        current = getattr(g, field)
        if current is None:
            setattr(g, field, rng.choice(options))
        else:
            nb = space.neighbors(options, current)
            if nb:
                setattr(g, field, rng.choice(nb))
    return g.normalize()


def structured_crossover(parent_a: StructuredGenome, parent_b: StructuredGenome,
                         rng: random.Random) -> StructuredGenome:
    """Semantic block crossover + normalization."""
    child = StructuredGenome(**asdict(parent_a))
    for block in _BLOCKS:
        if rng.random() < 0.5:
            for field in _BLOCKS[block]:
                setattr(child, field, getattr(parent_b, field))
    return child.normalize()


def _options_for(field, space):
    key = _LOCAL_FIELDS[field]
    if key in space.memory:
        return space.memory[key]
    if key in space.reasoning:
        return space.reasoning[key]
    if key in space.context_policy:
        return space.context_policy[key]
    return space.adaptation[key]
