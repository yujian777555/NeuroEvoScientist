"""Phase-17 Task 2/3: real Mamba-2 substrate behavior + adaptation protocol.

Skipped on the CPU dev box (transformers 4.29 lacks Mamba2Model); these run
on the A800 VM (transformers 5.7) where the real substrate exists.
"""

import os

import pytest
import torch

from genome.architecture import ArchitectureGenome
from models.mamba_memory import MambaMemory, mamba2_available
from evaluator.memory import build_memory_controller, hashed_embedding
from evolution.adaptation import AdaptationConfig, adapt_substrate

pytestmark = pytest.mark.skipif(not mamba2_available(),
                                reason="requires transformers Mamba2 (VM)")

EPISODE = [
    ("Apples cost 2 dollars each.", "2 * 5 = 10.\n#### 10"),
    ("A train moves 60 km in one hour.", "60 km/h.\n#### 60"),
    ("Sara has 3 boxes with 4 pens.", "3 * 4 = 12.\n#### 12"),
    ("A book has 100 pages, 20 a day.", "100 / 20 = 5.\n#### 5"),
]


def _episode_embeddings(indices=None, dim=64):
    idx = indices if indices is not None else range(len(EPISODE))
    return torch.stack([
        hashed_embedding(EPISODE[i][0] + " " + EPISODE[i][1], dim)
        for i in idx
    ]).unsqueeze(0)


def test_real_mamba2_is_not_a_linear_placeholder():
    torch.manual_seed(0)
    m = MambaMemory(hidden_size=64, state_size=16)
    assert not isinstance(m.substrate, torch.nn.Linear)
    # SSM-specific parameters exist
    names = [n for n, _ in m.named_parameters()]
    assert any("A_log" in n or "dt_bias" in n for n in names)


def test_order_sensitivity():
    torch.manual_seed(0)
    m = MambaMemory(hidden_size=64, state_size=16)
    m.eval()
    normal = _episode_embeddings()
    permuted = _episode_embeddings(indices=[3, 1, 0, 2])
    with torch.no_grad():
        s1 = m.memory_state(normal)
        s2 = m.memory_state(permuted)
    assert not torch.allclose(s1, s2, atol=1e-5)


def test_state_sensitivity_new_experience():
    torch.manual_seed(0)
    g = ArchitectureGenome(memory="mamba2", state_size=16)
    mem = build_memory_controller(g)
    for q, a in EPISODE[:2]:
        mem.store(q, a)
    s_before = mem.memory_state()
    mem.store(*EPISODE[2])
    s_after = mem.memory_state()
    assert not torch.allclose(s_before, s_after, atol=1e-6)


def test_gradient_flows_through_substrate():
    m = MambaMemory(hidden_size=64, state_size=16)
    x = _episode_embeddings()
    loss = m.forward_sequence(x).pow(2).mean()
    loss.backward()
    grads = [p.grad for n, p in m.named_parameters()
             if "mixer" in n or "A_log" in n]
    assert grads and all(g is not None for g in grads)


def test_state_dict_has_real_parameters():
    m = MambaMemory(hidden_size=64, state_size=16)
    sd = m.state_dict()
    assert len(sd) > 10
    assert any("mixer" in k for k in sd)


def test_differs_from_legacy_linear_proxy():
    torch.manual_seed(0)
    real = MambaMemory(hidden_size=64, state_size=16)
    proxy = torch.nn.Linear(64, 64)
    x = _episode_embeddings()
    with torch.no_grad():
        out_real = real(x)
        out_proxy = proxy(x)
    assert not torch.allclose(out_real, out_proxy, atol=1e-4)


def _calib_samples(n=48):
    base = [{"question": q, "answer": a} for q, a in EPISODE]
    return [base[i % len(base)] for i in range(n)]


def test_adaptation_reduces_loss_fixed_budget():
    torch.manual_seed(0)
    g = ArchitectureGenome(memory="mamba2", state_size=16)
    mem = build_memory_controller(g)
    cfg = AdaptationConfig(calibration_samples=16, adaptation_steps=5,
                           sequence_window=4, seed=0)
    rec = adapt_substrate(mem, _calib_samples(16), cfg)
    assert rec["trainable"] is True
    assert rec["steps"] == 5
    assert rec["post_loss"] < rec["pre_loss"]
    assert rec["wall_time_sec"] >= 0
    assert rec["trainable_params"] > 0


def test_adaptation_deterministic_same_seed():
    records = []
    for _ in range(2):
        torch.manual_seed(123)
        g = ArchitectureGenome(memory="mamba2", state_size=16)
        mem = build_memory_controller(g)
        cfg = AdaptationConfig(calibration_samples=16, adaptation_steps=3,
                               sequence_window=4, seed=7)
        records.append(adapt_substrate(mem, _calib_samples(16), cfg))
    assert records[0]["post_loss"] == pytest.approx(records[1]["post_loss"])


def test_non_mamba_substrate_adaptation_is_noop():
    g = ArchitectureGenome(memory="recency")
    mem = build_memory_controller(g)
    cfg = AdaptationConfig(calibration_samples=8, adaptation_steps=3)
    rec = adapt_substrate(mem, _calib_samples(8), cfg)
    assert rec["trainable"] is False
    assert rec["steps"] == 0
