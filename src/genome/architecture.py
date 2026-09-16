"""
Architecture Genome for NeuroEvoScientist (Phase-17 corrected schema).

Every gene names the REAL mechanism it controls:

- memory:         episodic memory substrate (recency/retrieval/mamba2/hybrid)
- reasoning:      prompt-level reasoning strategy (direct/cot/verify/planner)
- context_policy: exemplar verbosity (full/truncated/answer_only)
- quantization:   runtime quantization of the backbone (fp16/int8)

Phase-14..16 used a legacy schema where "compression: lora/qlora/int8" was
overloaded as context compression; those results are tagged legacy-schema.
"""

from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class ArchitectureGenome:
    memory: str = "mamba2"
    reasoning: str = "direct"
    context_policy: str = "full"
    quantization: str = "fp16"
    hidden_size: int = 1024
    state_size: int = 64

    def to_dict(self) -> Dict:
        return asdict(self)

    _DISPLAY_NAMES = {"mamba2": "Mamba2", "recency": "Recency",
                      "retrieval": "Retrieval", "hybrid": "Hybrid",
                      "direct": "Direct", "cot": "CoT", "verify": "Verify",
                      "planner": "Planner", "full": "Full",
                      "truncated": "Truncated", "answer_only": "AnswerOnly",
                      "fp16": "FP16", "int8": "INT8"}

    def describe(self) -> str:
        """Human-readable architecture name, e.g. 'Mamba2 + CoT + Full + FP16'."""
        parts = [self.memory, self.reasoning, self.context_policy,
                 self.quantization]
        return " + ".join(self._DISPLAY_NAMES.get(p, p) for p in parts)

    def mutate_target(self):
        return ["memory", "reasoning", "context_policy", "quantization"]
