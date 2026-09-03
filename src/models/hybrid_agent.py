"""Hybrid Agent architecture for NeuroEvoScientist.

Assembles a candidate agent from an ArchitectureGenome:

- memory:      "mamba" | "attention" | "retrieval" | "hybrid"
- reasoning:   "direct" | "verify" | "planner" | "cot"
- compression: "none" | "lora" | "qlora" | "int8"

Phase-13 uses lightweight CPU-friendly stand-ins; the module boundaries are
the real deliverable so kernels (official Mamba, PEFT LoRA, dynamic int8
quantization) can be dropped in later without touching the evolution loop.
"""

import torch
import torch.nn as nn

from .mamba_memory import MambaMemory


# ---------------------------------------------------------------------------
# Memory substrates
# ---------------------------------------------------------------------------

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


class RetrievalMemory(nn.Module):
    """Retrieval-augmented memory placeholder (gated self-mixing)."""

    def __init__(self, hidden_size=1024):
        super().__init__()
        self.key = nn.Linear(hidden_size, hidden_size)
        self.value = nn.Linear(hidden_size, hidden_size)
        self.gate = nn.Linear(hidden_size, hidden_size)

    def forward(self, hidden_states):
        retrieved = torch.softmax(self.key(hidden_states), dim=1)
        retrieved = retrieved * self.value(hidden_states)
        gate = torch.sigmoid(self.gate(hidden_states))
        return gate * retrieved + (1 - gate) * hidden_states


class HybridMemory(nn.Module):
    """Hybrid substrate: Mamba state track + attention track."""

    def __init__(self, hidden_size=1024, state_size=64, num_heads=8):
        super().__init__()
        self.mamba_track = MambaMemory(hidden_size=hidden_size,
                                       state_size=state_size)
        self.attention_track = AttentionMemory(hidden_size=hidden_size,
                                               num_heads=num_heads)
        self.mix = nn.Linear(2 * hidden_size, hidden_size)

    def forward(self, hidden_states):
        m = self.mamba_track(hidden_states)
        a = self.attention_track(hidden_states)
        return self.mix(torch.cat([m, a], dim=-1))


# ---------------------------------------------------------------------------
# Reasoning modules
# ---------------------------------------------------------------------------

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


class PlannerReasoning(nn.Module):
    """Plan-then-solve reasoning."""

    def __init__(self, hidden_size=1024):
        super().__init__()
        self.planner = nn.Linear(hidden_size, hidden_size)
        self.solver = nn.Linear(hidden_size, hidden_size)

    def forward(self, hidden_states):
        plan = torch.tanh(self.planner(hidden_states))
        return self.solver(plan * hidden_states)


class CoTReasoning(nn.Module):
    """Chain-of-thought reasoning: iterated shallow steps."""

    def __init__(self, hidden_size=1024, steps=2):
        super().__init__()
        self.steps = steps
        self.step_fn = nn.Linear(hidden_size, hidden_size)

    def forward(self, hidden_states):
        x = hidden_states
        for _ in range(self.steps):
            x = x + torch.tanh(self.step_fn(x))
        return x


# ---------------------------------------------------------------------------
# Compression wrappers
# ---------------------------------------------------------------------------

# Footprint proxy relative to an uncompressed module (used by the
# efficiency metric until real quantization/PEFT is wired in).
COMPRESSION_FOOTPRINT = {"none": 1.0, "lora": 0.9, "qlora": 0.3, "int8": 0.25}


class LoRAAdapter(nn.Module):
    """Low-rank compression placeholder wrapping a base module."""

    def __init__(self, base, hidden_size=1024, rank=8):
        super().__init__()
        self.base = base
        self.lora_a = nn.Linear(hidden_size, rank, bias=False)
        self.lora_b = nn.Linear(rank, hidden_size, bias=False)

    def forward(self, hidden_states):
        return self.base(hidden_states) + self.lora_b(self.lora_a(hidden_states))


class Int8Wrapper(nn.Module):
    """INT8 quantization placeholder (pass-through + footprint marker)."""

    def __init__(self, base):
        super().__init__()
        self.base = base

    def forward(self, hidden_states):
        return self.base(hidden_states)


# ---------------------------------------------------------------------------
# Agent assembly
# ---------------------------------------------------------------------------

class HybridAgent(nn.Module):
    def __init__(self, genome):
        super().__init__()
        self.genome = genome
        hidden = genome.hidden_size

        if genome.memory == "mamba":
            memory = MambaMemory(hidden_size=hidden,
                                 state_size=genome.state_size)
        elif genome.memory == "attention":
            memory = AttentionMemory(hidden_size=hidden)
        elif genome.memory == "retrieval":
            memory = RetrievalMemory(hidden_size=hidden)
        elif genome.memory == "hybrid":
            memory = HybridMemory(hidden_size=hidden,
                                  state_size=genome.state_size)
        else:
            raise ValueError("unknown memory substrate: %s" % genome.memory)

        if genome.reasoning == "direct":
            reasoning = DirectReasoning(hidden_size=hidden)
        elif genome.reasoning == "verify":
            reasoning = VerifyReasoning(hidden_size=hidden)
        elif genome.reasoning == "planner":
            reasoning = PlannerReasoning(hidden_size=hidden)
        elif genome.reasoning == "cot":
            reasoning = CoTReasoning(hidden_size=hidden)
        else:
            raise ValueError("unknown reasoning module: %s" % genome.reasoning)

        if genome.compression == "lora":
            memory = LoRAAdapter(memory, hidden_size=hidden, rank=8)
        elif genome.compression == "qlora":
            memory = LoRAAdapter(memory, hidden_size=hidden, rank=4)
        elif genome.compression == "int8":
            memory = Int8Wrapper(memory)
        elif genome.compression != "none":
            raise ValueError("unknown compression strategy: %s" % genome.compression)

        self.memory = memory
        self.reasoning = reasoning

    def forward(self, x):
        return self.reasoning(self.memory(x))

    def num_parameters(self):
        return sum(p.numel() for p in self.parameters())

    def effective_parameters(self):
        """Compression-adjusted parameter footprint used by efficiency metric."""
        scale = COMPRESSION_FOOTPRINT.get(self.genome.compression, 1.0)
        return self.num_parameters() * scale
