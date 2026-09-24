"""Real Mamba-2 memory substrate for NeuroEvoScientist (Phase-17, Task 2).

This replaces the Phase-12..16 placeholder (a plain ``nn.Linear`` that was
named Mamba). The substrate is a genuine Mamba-2 block from the maintained
Transformers implementation (``transformers.Mamba2Model``):

- consumes a SEQUENCE of experience embeddings (not a single vector);
- order-dependent recurrent state computation;
- trainable parameters with gradient flow;
- standard ``state_dict()`` for exact parent->child weight inheritance.

No silent fallback: if the Transformers Mamba-2 implementation is not
available, construction raises loudly instead of degrading to a proxy
under the Mamba name (Phase-17 plan, Task 2 rule).
"""

import torch
import torch.nn as nn

try:
    from transformers import Mamba2Config, Mamba2Model
    _HAS_MAMBA2 = True
except ImportError:  # transformers < 4.43 (e.g. the CPU dev box)
    _HAS_MAMBA2 = False


def _force_naive_mamba2_path():
    """Disable lazy hub-kernel loading for Mamba2 (use the naive fallback).

    The shared A800 conda env's kernels package intermittently fails
    ``lazy_load_kernel("causal-conv1d")`` with a hard ValueError (offline
    mode + missing kernel metadata), crashing Mamba2Model construction
    instead of falling back. All previous phases used the naive path, so
    forcing it keeps results consistent and environment-independent.
    """
    if not _HAS_MAMBA2:
        return
    try:
        from transformers.models.mamba2 import modeling_mamba2 as _m2
        _m2.lazy_load_kernel = lambda *args, **kwargs: None
    except Exception:
        pass


class MambaMemory(nn.Module):
    """Mamba-2 episodic memory substrate.

    Args:
        hidden_size: embedding dim of experience vectors (default 64,
            matching evaluator.memory.hashed_embedding).
        state_size: SSM state size.
        num_layers:  number of Mamba-2 layers.
    """

    def __init__(self, hidden_size=64, state_size=16, num_layers=2):
        super().__init__()
        if not _HAS_MAMBA2:
            raise RuntimeError(
                "Real Mamba-2 substrate requires transformers>=4.44 "
                "(Mamba2Model). Refusing to substitute a placeholder under "
                "the Mamba name (Phase-17 semantics rule)."
            )
        _force_naive_mamba2_path()
        # Mamba-2 config constraint: hidden*expand == num_heads*head_dim.
        expand = 2
        intermediate = hidden_size * expand
        head_dim = 16
        num_heads = max(1, intermediate // head_dim)
        config = Mamba2Config(
            hidden_size=hidden_size,
            state_size=state_size,
            num_heads=num_heads,
            head_dim=head_dim,
            intermediate_size=intermediate,
            num_hidden_layers=num_layers,
        )
        self.substrate = Mamba2Model(config)
        self.hidden_size = hidden_size
        self.state_size = state_size

    def forward_sequence(self, embeddings):
        """Run the experience sequence through Mamba-2.

        Args:
            embeddings: (batch, seq_len, hidden_size) experience embeddings.
        Returns:
            (batch, seq_len, hidden_size) contextualized states.
        """
        return self.substrate(inputs_embeds=embeddings).last_hidden_state

    def memory_state(self, embeddings):
        """Order-dependent memory state: last position of the sequence."""
        return self.forward_sequence(embeddings)[:, -1]

    def forward(self, hidden_states):
        """Backwards-compatible single/sequence entry point.

        Accepts (batch, seq, dim) or (batch, dim) input; returns the Mamba-2
        contextualized output (for (batch, dim) input, a length-1 sequence).
        """
        if hidden_states.dim() == 2:
            hidden_states = hidden_states.unsqueeze(1)
        return self.forward_sequence(hidden_states)


def mamba2_available():
    """True when the real Mamba-2 substrate can be constructed."""
    return _HAS_MAMBA2
