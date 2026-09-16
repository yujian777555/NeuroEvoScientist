"""Backwards-compatible shim (Phase-17).

The old HybridAgent assembled placeholder modules for the legacy schema.
In the corrected schema the neural component is the memory substrate;
see models/builder.py: SubstrateAgent.
"""

from .builder import SubstrateAgent

# Legacy alias — new code should use SubstrateAgent directly.
HybridAgent = SubstrateAgent
