# EvoMamba-Agent

AlphaEvolve-inspired Evolutionary Neural Architecture Search for Lightweight Mamba-based LLM Agents.

## Research Goal

This project studies a self-evolving framework for discovering efficient large language model architectures.

Core technologies:

- Mamba / State Space Models (SSM)
- Evolutionary computation
- NSGA-II multi-objective optimization
- LLM-driven architecture proposal
- AI4Science autonomous agents

## Core Hypothesis

Future lightweight foundation models should not only be compressed manually. They should be automatically discovered by evolutionary AI researchers.

The proposed pipeline:

```
Research Agent
      |
      v
Architecture Genome Generator
      |
      v
Evolution Controller
      |
      v
Mamba / Attention / MoE Candidate Models
      |
      v
Multi-objective Evaluation
      |
      v
Pareto Optimal Lightweight LLM
```

## Expected Contributions

1. AlphaEvolve-inspired evolutionary neural architecture search for LLMs.
2. Hybrid Mamba-Attention architecture discovery.
3. Accuracy-memory-latency Pareto optimization.
4. Self-improving AI scientist agent for model engineering.

## Structure

```
docs/          Paper design and literature review
src/           Implementation
experiments/   Evaluation protocols
paper/         Manuscript materials
```
