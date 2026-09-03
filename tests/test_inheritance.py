"""Verify weight inheritance between parent and child architectures."""

import torch

from genome.architecture import ArchitectureGenome
from models.builder import build_agent
from evolution.inheritance import inherit_state, build_child_with_inheritance


def _genome(memory="mamba", reasoning="direct", compression="none",
            hidden_size=32, state_size=8):
    return ArchitectureGenome(memory=memory, reasoning=reasoning,
                              compression=compression,
                              hidden_size=hidden_size, state_size=state_size)


def test_identical_architecture_inherits_everything():
    parent = _genome()
    child = _genome()
    parent_agent = build_agent(parent)
    child_agent = build_agent(child)

    inherited = inherit_state(parent, parent_agent.state_dict(), child,
                              child_state=child_agent.state_dict())
    assert set(inherited) == set(child_agent.state_dict())


def test_changed_memory_keeps_reasoning_weights():
    parent = _genome(memory="mamba")
    child = _genome(memory="attention")
    parent_agent = build_agent(parent)
    child_agent = build_agent(child)

    inherited = inherit_state(parent, parent_agent.state_dict(), child,
                              child_state=child_agent.state_dict())
    assert inherited, "reasoning weights should transfer"
    assert all(name.startswith("reasoning.") for name in inherited)
    assert not any(name.startswith("memory.") for name in inherited)


def test_inherited_weights_actually_load():
    parent = _genome(reasoning="verify")
    child = _genome(reasoning="verify")  # same arch -> full transfer
    parent_agent = build_agent(parent)

    child_agent, n = build_child_with_inheritance(
        parent, parent_agent.state_dict(), child, build_agent)
    assert n > 0

    x = torch.randn(2, 4, 32)
    with torch.no_grad():
        assert torch.allclose(parent_agent(x), child_agent(x))


def test_shape_mismatch_is_skipped():
    parent = _genome(hidden_size=32)
    child = _genome(hidden_size=64)
    parent_agent = build_agent(parent)
    child_agent = build_agent(child)

    inherited = inherit_state(parent, parent_agent.state_dict(), child,
                              child_state=child_agent.state_dict())
    assert inherited == {}
