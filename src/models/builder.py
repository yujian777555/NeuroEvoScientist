"""Agent model construction from architecture genomes (Phase-17).

In the corrected schema the neural module of a candidate is its trainable
memory substrate; reasoning/context_policy act at prompt level and
quantization at runtime level. ``build_agent`` returns a light wrapper
exposing the substrate for parameter accounting and inheritance.
"""

import torch.nn as nn

from .mamba_memory import MambaMemory


class SubstrateAgent(nn.Module):
    """A candidate's neural substrate (memory module) plus genome metadata."""

    def __init__(self, genome, dim=64):
        super().__init__()
        self.genome = genome
        if genome.memory == "mamba2":
            self.substrate = MambaMemory(
                hidden_size=dim, state_size=min(genome.state_size, 64))
        else:
            # non-trainable memory policies carry only a tiny probe so the
            # interface (and parameter accounting) stays uniform
            self.substrate = nn.Linear(dim, dim)

    def forward(self, x):
        if self.genome.memory == "mamba2":
            return self.substrate(x)
        return self.substrate(x)

    def num_parameters(self):
        return sum(p.numel() for p in self.parameters())

    def effective_parameters(self):
        """Quantization-adjusted parameter footprint for efficiency."""
        scale = {"fp16": 1.0, "int8": 0.25}.get(self.genome.quantization, 1.0)
        return self.num_parameters() * scale


def build_agent(genome):
    """Create an agent instance from an ArchitectureGenome."""
    return SubstrateAgent(genome)
