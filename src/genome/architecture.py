"""
Architecture Genome for NeuroEvoScientist.

The genome encodes an agent cognitive substrate:
- memory module
- reasoning module
- tool module
- compression strategy
"""

from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class ArchitectureGenome:
    memory: str = "mamba"
    reasoning: str = "direct"
    tool_adapter: str = "basic"
    compression: str = "none"
    hidden_size: int = 1024
    state_size: int = 64

    def to_dict(self) -> Dict:
        return asdict(self)

    _DISPLAY_NAMES = {"mamba": "Mamba", "attention": "Attention",
                      "retrieval": "Retrieval", "hybrid": "Hybrid",
                      "direct": "Direct", "verify": "Verify",
                      "planner": "Planner", "cot": "CoT",
                      "none": "None", "lora": "LoRA", "qlora": "QLoRA",
                      "int8": "INT8"}

    def describe(self) -> str:
        """Human-readable architecture name, e.g. 'Mamba + Verify + LoRA'."""
        parts = [self.memory, self.reasoning, self.compression]
        return " + ".join(self._DISPLAY_NAMES.get(p, p) for p in parts)

    def mutate_target(self):
        return [
            "memory",
            "reasoning",
            "tool_adapter",
            "compression"
        ]
