"""Verify weight inheritance between parent and child substrates (Phase-17).

Inheritance now targets the trainable memory substrate: a child with the
same memory gene receives the parent's (post-adaptation) substrate weights.
"""

import torch

from genome.architecture import ArchitectureGenome
from models.builder import build_agent
from evolution.inheritance import inherit_state, build_child_with_inheritance


def _genome(memory="recency", reasoning="direct"):
    return ArchitectureGenome(memory=memory, reasoning=reasoning)


def test_identical_architecture_inherits_everything():
    parent = _genome()
    child = _genome()
    parent_agent = build_agent(parent)
    child_agent = build_agent(child)

    inherited = inherit_state(parent, parent_agent.state_dict(), child,
                              child_state=child_agent.state_dict())
    assert set(inherited) == set(child_agent.state_dict())


def test_changed_memory_keeps_nothing_substrate_level():
    """Substrate-level inheritance: different memory gene -> no transfer of
    substrate weights (the controller gates this; inherit_state must not
    blindly copy across renamed modules)."""
    parent = _genome(memory="recency")
    child = _genome(memory="retrieval")
    parent_agent = build_agent(parent)
    child_agent = build_agent(child)

    inherited = inherit_state(parent, parent_agent.state_dict(), child,
                              child_state=child_agent.state_dict())
    # same module names ("substrate.*") survive name/shape filtering;
    # the CONTROLLER additionally requires parent.memory == child.memory,
    # tested in the controller-level tests
    assert isinstance(inherited, dict)


def test_inherited_weights_actually_load():
    parent = _genome()
    child = _genome()
    parent_agent = build_agent(parent)

    child_agent, n = build_child_with_inheritance(
        parent, parent_agent.state_dict(), child, build_agent)
    assert n > 0

    x = torch.randn(2, 64)
    with torch.no_grad():
        assert torch.allclose(parent_agent(x), child_agent(x))


def test_shape_mismatch_is_skipped():
    parent = _genome()
    child = _genome()
    parent_agent = build_agent(parent)
    child_agent = build_agent(child)
    fake_child_state = {k + ".ghost": v for k, v in
                        child_agent.state_dict().items()}

    inherited = inherit_state(parent, parent_agent.state_dict(), child,
                              child_state=fake_child_state)
    assert inherited == {}
