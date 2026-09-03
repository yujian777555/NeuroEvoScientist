"""Hybrid Agent architecture for NeuroEvoScientist.

Assembles a candidate agent from an ArchitectureGenome:

- memory:      "mamba" -> MambaMemory, "attention" -> self-attention block
- reasoning:   "direct" -> single forward pass, "verify" -> extra verifier pass
- compression: "none" -> full weights, "lora" -> low-rank adapter placeholder

Phase-12 uses lightweight CPU-friendly stand-ins; the module boundaries are
the real deliverable so kernels (official Mamba, LoRA adapters) can be
dropped in later without touching the evolution loop.
"""

import torch.nn as nn

from .mamba_memory import MambaMemory


class AttentionMemory(nn.Module):
    """Attention-based memory substrate (CPU placeholder)."""

    def __init__(self, hidden_size=1024, num_heads=8):
        super().__init__()
        self.attention = nn.MultiheadAttention(hidden_size, num_heads)

    def forward(self, hidden_states):
        # hidden_states: (batch, seq, hidden) -> attention expects (seq, batch, hidden)
        x = hidden_states.transpose(0, 1)
        out, _ = self.attention(x, x, x)
        return out.transpose(0, 1)


class DirectReasoning(nn.Module):
    """Single-pass reasoning head."""

    def __init__(self, hidden_size=1024):
        super().__init__()
        self.head = nn.Linear(hidden_size, hidden_size)

    def forward(self, hidden_states):
        return self.head(hidden_states)


class VerifyReasoning(nn.Module):
    """Reasoning with an extra self-verification pass."""

    def __init__(self, hidden_size=1024):
        super().__init__()
        self.head = nn.Linear(hidden_size, hidden_size)
        self.verifier = nn.Linear(hidden_size, hidden_size)

    def forward(self, hidden_states):
        draft = self.head(hidden_states)
        checked = self.verifier(draft)
        return 0.5 * (draft + checked)


class LoRAAdapter(nn.Module):
    """Low-rank compression placeholder wrapping a base module."""

    def __init__(self, base, hidden_size=1024, rank=8):
        super().__init__()
        self.base = base
        self.lora_a = nn.Linear(hidden_size, rank, bias=False)
        self.lora_b = nn.Linear(rank, hidden_size, bias=False)

    def forward(self, hidden_states):
        return self.base(hidden_states) + self.lora_b(self.lora_a(hidden_states))


class HybridAgent(nn.Module):
    def __init__(self, genome):
        super().__init__()
        self.genome = genome
        hidden = genome.hidden_size

        if genome.memory == "mamba":
            memory = MambaMemory(
                hidden_size=hidden,
                state_size=genome.state_size,
            )
        elif genome.memory == "attention":
            memory = AttentionMemory(hidden_size=hidden)
        else:
            raise ValueError("unknown memory substrate: %s" % genome.memory)

        if genome.reasoning == "direct":
            reasoning = DirectReasoning(hidden_size=hidden)
        elif genome.reasoning == "verify":
            reasoning = VerifyReasoning(hidden_size=hidden)
        else:
            raise ValueError("unknown reasoning module: %s" % genome.reasoning)

        if genome.compression == "lora":
            memory = LoRAAdapter(memory, hidden_size=hidden)
        elif genome.compression != "none":
            raise ValueError("unknown compression strategy: %s" % genome.compression)

        self.memory = memory
        self.reasoning = reasoning

    def forward(self, x):
        return self.reasoning(self.memory(x))

    def num_parameters(self):
        return sum(p.numel() for p in self.parameters())
