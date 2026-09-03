# Experimental Protocol

## Goal

The experiments verify whether Evolutionary Neural Substrate Search (ENSS) can discover adaptive agent architectures that outperform manually designed and conventional search-based systems.

## Research Questions

RQ1: Can evolutionary search discover better agent cognitive architectures than fixed design?

RQ2: Does Pareto-based multi-objective evolution improve the capability-efficiency tradeoff?

RQ3: Does adaptive Mamba-based memory improve long-horizon scientific reasoning?

## Baselines

### Fixed Agent Baselines

- ReAct-style Agent
- Fixed Transformer Agent
- Fixed Mamba-memory Agent
- Retrieval-Augmented Agent

### Search Baselines

- Random Search
- Grid Search
- Traditional NAS-style search
- Evolution without Pareto optimization
- Evolution without weight inheritance

## Backbone Models

Small-scale validation:

- Qwen2.5-1.5B
- Mamba-based language models

Large-scale experiments:

- Qwen2.5-7B
- Llama-family models

## Benchmarks

### Reasoning

- GSM8K
- MATH subset

### Agent Evaluation

- AgentBench subset

### Scientific Discovery

- PubMedQA
- SciQ

## Metrics

### Capability

- Accuracy
- Task success rate

### Efficiency

- Inference latency
- GPU memory usage
- Computational cost

### Adaptability

Performance improvement after task distribution changes.

## Ablation Studies

### Remove Evolution

Compare ENSS against fixed architectures.

### Remove Mamba Memory

Replace adaptive state memory with standard attention memory.

### Remove Pareto Optimization

Optimize only task accuracy.

### Remove Weight Inheritance

Measure search efficiency and convergence degradation.

### Remove Crossover

Evaluate the contribution of architecture recombination.

## Hardware Plan

Target platform:

- 4+ NVIDIA A800 80GB GPUs

Distributed workers evaluate candidate architectures in parallel.

## Expected Result

ENSS should discover agent architectures with better Pareto tradeoffs among capability, efficiency, and adaptability compared with fixed and random search baselines.
