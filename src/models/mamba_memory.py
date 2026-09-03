"""Mamba memory substrate placeholder for EvoScientist-Mamba.

This module defines the interface used by the evolutionary genome builder.
The implementation can later wrap official Mamba-2 kernels.
"""

import torch
import torch.nn as nn


class MambaMemory(nn.Module):
    def __init__(self, hidden_size=1024, state_size=64):
        super().__init__()
        self.hidden_size = hidden_size
        self.state_size = state_size
        self.projection = nn.Linear(hidden_size, hidden_size)

    def forward(self, hidden_states):
        return self.projection(hidden_states)
