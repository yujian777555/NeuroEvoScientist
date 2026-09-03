"""Build neural agents from architecture genomes."""

from .hybrid_agent import HybridAgent


def build_agent(genome):
    """Create an agent instance from an ArchitectureGenome."""
    return HybridAgent(genome)
