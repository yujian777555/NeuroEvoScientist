"""Structured genome for Phase-20 cognitive co-design.

Hierarchical genome with conditional sub-genes. Every active gene changes
real computation, prompt construction, memory behavior, or adaptation cost.
Inactive conditional genes are normalized to None so duplicate phenotypes
are never counted as distinct architectures.

Compat bridge: ``memory`` / ``reasoning`` / ``context_policy`` properties
map to the Phase-17 flat gene names so the evaluators keep working.
"""

import hashlib
import json
from dataclasses import dataclass, asdict
from typing import Dict, Optional


@dataclass
class StructuredGenome:
    # memory block
    memory_type: str = "recency"          # recency|retrieval|mamba2|hybrid
    memory_k: int = 3                     # 1,2,3,4,6,8 (max exemplars)
    retrieval_metric: Optional[str] = None   # tfidf|dense; retrieval/hybrid
    mamba_state_size: Optional[int] = None   # 32..256; mamba2 only
    hybrid_fraction: Optional[float] = None  # 0.25..0.75; hybrid only

    # reasoning block
    reasoning: str = "direct"             # direct|cot|verify|planner
    reasoning_depth: Optional[int] = None    # 1-4; cot/planner
    verifier_passes: Optional[int] = None    # 0-2; verify only

    # context block
    context_mode: str = "full"            # full|truncated|answer_only
    token_budget: Optional[int] = None    # 128..1024; truncated/answer_only
    exemplar_count: int = 3               # 0-8 (0 = memory disabled in effect)

    # adaptation block
    adaptation_enabled: bool = False
    adaptation_steps: Optional[int] = None   # 0,10,20,40; enabled only

    quantization: str = "fp16"            # fixed, not searched

    # ---- normalization ------------------------------------------------------

    def normalize(self) -> "StructuredGenome":
        """Return a canonical copy with inactive conditional genes removed."""
        g = StructuredGenome(**asdict(self))
        if g.memory_type not in ("retrieval", "hybrid"):
            g.retrieval_metric = None
        if g.memory_type != "mamba2":
            g.mamba_state_size = None
        if g.memory_type != "hybrid":
            g.hybrid_fraction = None
        if g.reasoning not in ("cot", "planner"):
            g.reasoning_depth = None
        if g.reasoning != "verify":
            g.verifier_passes = None
        if g.context_mode == "full":
            g.token_budget = None
        if not g.adaptation_enabled:
            g.adaptation_steps = None
        # adaptation only trains the mamba2 substrate; with no mamba2 the
        # adaptation genes have no effect and are normalized off
        if g.memory_type != "mamba2":
            g.adaptation_enabled = False
            g.adaptation_steps = None
        # exemplar_count=0 means no exemplars; memory sub-genes inert
        if g.exemplar_count == 0:
            g.retrieval_metric = None
            g.mamba_state_size = None
            g.hybrid_fraction = None
        return g

    def phenotype_hash(self) -> str:
        """Deterministic hash of the normalized phenotype."""
        g = self.normalize()
        payload = json.dumps(asdict(g), sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    # ---- compat bridge to the Phase-17 flat evaluator interface -------------

    @property
    def memory(self):
        return self.memory_type

    @property
    def context_policy(self):
        return self.context_mode

    @property
    def state_size(self):
        return self.mamba_state_size or 64

    def to_dict(self) -> Dict:
        return asdict(self.normalize())

    def describe(self) -> str:
        g = self.normalize()
        parts = [g.memory_type, g.reasoning, g.context_mode, "FP16"]
        return " + ".join(p.capitalize() for p in parts)

    def describe_full(self) -> str:
        g = self.normalize()
        d = g.to_dict()
        active = {k: v for k, v in d.items()
                  if v is not None and k != "quantization"}
        return " ".join("%s=%s" % (k, v) for k, v in sorted(active.items()))
