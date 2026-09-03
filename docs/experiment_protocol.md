# Experiment Protocol

## Baselines

- Transformer agents
- Mamba agents
- ReAct style agents
- Memory augmented agents

## Benchmarks

General reasoning:
- GSM8K
- MATH subset

Agent:
- AgentBench
- GAIA subset

Science:
- PubMedQA
- SciQ

## Ablation

1. Remove evolution
2. Remove Mamba memory
3. Remove task conditioning
4. Remove Pareto optimization

## Metrics

- accuracy
- task success rate
- latency
- GPU memory
- parameter count
