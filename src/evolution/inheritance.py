"""
Weight inheritance for ENSS (Phase-13).

Instead of rebuilding every evolved agent from scratch, child
architectures reuse compatible parameters from their parent:

    Parent Genome + Parent State  ->  Child Genome + Inherited State

Compatibility rule: a parameter tensor is inherited when the genome
module it belongs to (memory / reasoning / compression) is unchanged
between parent and child, the parameter name exists in the child, and
tensor shapes match. Everything else is freshly initialized.

This cuts evaluation cost for A800-scale experiments, where partially
trained parents pass their substrate weights to offspring.
"""

from typing import Dict, Optional

import torch


def _module_unchanged(parent_genome, child_genome, prefix: str) -> bool:
    """Whether the genome fields governing a module prefix are identical."""
    if prefix.startswith("memory"):
        fields = ["memory", "compression", "hidden_size", "state_size"]
    elif prefix.startswith("reasoning"):
        fields = ["reasoning", "hidden_size"]
    else:
        fields = ["hidden_size"]
    return all(
        getattr(parent_genome, f, None) == getattr(child_genome, f, None)
        for f in fields
    )


def inherit_state(parent_genome, parent_state: Dict[str, torch.Tensor],
                  child_genome,
                  child_state: Optional[Dict[str, torch.Tensor]] = None
                  ) -> Dict[str, torch.Tensor]:
    """Build an inherited state dict for a child architecture.

    Args:
        parent_genome: ArchitectureGenome of the parent.
        parent_state:  parent ``state_dict`` (tensors not modified).
        child_genome:  ArchitectureGenome of the child.
        child_state:   optional child ``state_dict`` used to filter by
                       name/shape (pass ``child_agent.state_dict()``).
                       When omitted, name/shape filtering is skipped.

    Returns:
        Dict of tensors to load into the child via
        ``child_agent.load_state_dict(inherited, strict=False)``.
    """
    inherited = {}
    for name, tensor in parent_state.items():
        prefix = name.split(".", 1)[0]
        if not _module_unchanged(parent_genome, child_genome, prefix):
            continue
        if child_state is not None:
            if name not in child_state:
                continue
            if child_state[name].shape != tensor.shape:
                continue
        inherited[name] = tensor.clone()
    return inherited


def build_child_with_inheritance(parent_genome, parent_state, child_genome,
                                 builder):
    """Build a child agent and load all compatible parent weights.

    Returns ``(child_agent, n_inherited)`` where ``n_inherited`` is the
    number of tensors transferred from the parent.
    """
    child_agent = builder(child_genome)
    inherited = inherit_state(
        parent_genome, parent_state, child_genome,
        child_state=child_agent.state_dict(),
    )
    if inherited:
        child_agent.load_state_dict(inherited, strict=False)
    return child_agent, len(inherited)


class WeightInheritance:
    """Backwards-compatible wrapper around the functional API."""

    def inherit(self, parent_model, child_architecture):
        return inherit_state(
            getattr(parent_model, "genome", None),
            parent_model.state_dict(),
            child_architecture,
        )

    def is_compatible(self, parameter_name, architecture):
        return True
