# Experiment Design

## 1. Research Questions

RQ1: Can evolutionary search discover better agent architectures than manual design?

RQ2: Does adaptive memory architecture improve long-context scientific tasks?

RQ3: Can Pareto evolution achieve better capability-efficiency tradeoffs?

## 2. Baselines

### Agent Baselines

- ReAct-style agents
- Fixed memory agents
- Fixed Mamba agents
- Fixed Transformer agents

### Search Baselines

- Random search
- Grid search
- Traditional NAS
- Evolution without Pareto optimization

## 3. Backbone Models

Initial experiments:

- Qwen2.5-1.5B
- Mamba-based language models

Large scale experiments:

- Qwen2.5-7B
- Llama-family models

## 4. Benchmarks

Reasoning:

- GSM8K
- MATH subset

Agent:

- AgentBench

Scientific:

- PubMedQA
- SciQ

## 5. Ablation Studies

Remove each component:

1. Without evolution
2. Without Mamba memory
3. Without crossover
4. Without weight inheritance
5. Without multi-objective optimization

## 6. Hardware Plan

Target platform:

- 4+ NVIDIA A800 80GB GPUs

Distributed evaluation is used for large population evolution.

## 7. Expected Result

The evolved agents should achieve better Pareto tradeoffs between capability, memory consumption, and latency compared with fixed architectures.
