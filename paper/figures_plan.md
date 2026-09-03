# Paper Figures Plan

## Figure 1: Overall Framework

Title:

Evolutionary Neural Substrate Search for Adaptive Scientific Agents

Content:

```
Task
 |
Architecture Genome
 |
Evolution Controller
 |
Agent Population
 |
Evaluation
 |
Pareto Selection
 |
New Generation Agent
```

Purpose:

Show the complete ENSS pipeline.

---

## Figure 2: Architecture Genome

Show how an agent is represented:

```
Genome
 |
 +-- Memory
 |     +-- Mamba
 |     +-- Attention
 |
 +-- Reasoning
 |     +-- Verifier
 |     +-- MoE
 |
 +-- Tool
 |
 +-- Compression
```

Purpose:

Explain the search space.

---

## Figure 3: Evolution Process

Show:

Generation 0 -> Generation N

including:

- mutation
- crossover
- weight inheritance
- Pareto selection

Purpose:

Demonstrate self-improvement.

---

## Figure 4: Pareto Frontier

X axis:

Memory/Latency

Y axis:

Capability

Compare:

- fixed agents
- random search
- ENSS

Purpose:

Show capability-efficiency advantage.

---

## Figure 5: Ablation Analysis

Compare:

- Full ENSS
- without evolution
- without Mamba
- without crossover
- without inheritance

Purpose:

Validate each component.
