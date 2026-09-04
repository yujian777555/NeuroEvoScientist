# Phase-14 Plan: Real Evolution Experiment on A800

## Goal

Upgrade ENSS from framework validation to paper-level experimental validation.

The main question:

Can Evolutionary Neural Substrate Search discover better adaptive agent architectures than manually designed agents and random search?

---

# Phase-14 Priorities

## Task 1: Real LLM Backend

Integrate a real foundation model backend.

Recommended first model:

- Qwen2.5-1.5B

Reason:

- low cost
- suitable for iterative evolution
- easy scaling to larger models later

Required:

```
Genome
 |
Agent Builder
 |
Qwen Backend
 |
Benchmark
 |
Fitness
```

---

# Task 2: A800 Experiment Setup

Initial configuration:

```
GPU:
1 x A800 80GB

Population:
32

Generation:
20
```

Do not start with maximum scale.

First verify reproducibility.

---

# Task 3: Baseline Matrix

Must compare:

## Fixed Architectures

1. Transformer Memory Agent
2. Mamba Memory Agent
3. Hybrid Memory Agent

## Search Methods

4. Random Search
5. Evolution without Pareto
6. ENSS

---

# Task 4: Benchmark

First benchmark:

GSM8K

Later:

- PubMedQA
- scientific reasoning benchmarks

---

# Task 5: Required Ablations

## Full ENSS

Compare against:

```
-w/o NSGA Pareto
-w/o Weight Inheritance
-w/o Mamba Memory
-w/o Evolution
```

---

# Expected Paper Figures

## Figure 1

Evolution curve:

Generation vs Capability/Efficiency

## Figure 2

Pareto front evolution

## Figure 3

Architecture distribution across generations

## Table 1

Main benchmark comparison

## Table 2

Ablation study

---

# Important Research Constraints

Do not modify ENSS into ordinary NAS.

Keep the contribution:

Evolution of Agent Cognitive Architecture.

The search target is:

Memory + Reasoning + Tool + Compression substrate.

---

# Success Criteria

Phase-14 is complete when:

1. Real LLM backend runs
2. GSM8K real evaluation works
3. ENSS completes multiple generations
4. Baselines are implemented
5. First paper-quality result table is generated

After completion update:

- status.json
- CHANGELOG.md
- experiment logs
