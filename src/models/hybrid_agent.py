"""Hybrid Agent architecture for EvoScientist-Mamba.

Combines memory substrate and reasoning modules according to genome.
"""

import torch.nn as nn
from .mamba_memory import MambaMemory


class HybridAgent(nn.Module):
    def __init__(self, genome):
        super().__init__()
        self.genome = genome

        if genome.memory == "mamba":
            self.memory = MambaMemory(
                hidden_size=genome.hidden_size,
                state_size=genome.state_size,
            )
        else:
            self.memory = nn.Identity()

    def forward(self, x):
        return self.memory(x)
