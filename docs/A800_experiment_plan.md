# A800 Experiment Plan

## Hardware

Target environment:

- 4 x NVIDIA A800 80GB
- Distributed PyTorch

## Phase 1: Search

Population:

256 candidates

Generation:

50-100 iterations

## Phase 2: Validation

Select Pareto optimal agents.

Evaluate on:

- GSM8K
- MATH
- AgentBench
- PubMedQA

## Optimization

Use:

- Weight inheritance
- Surrogate fitness prediction
- Parallel evaluation

## Expected Runtime

A complete search cycle should finish within several days depending on evaluation budget.
