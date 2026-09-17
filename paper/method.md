# Method: Task-Conditioned Cognitive Architecture Co-Design（Phase-19 迁移版）

> 本文方法部分描述的实际机制以 Phase-17 修正实现为准
> （`src/genome/`、`src/evaluator/memory.py`、`src/evolution/`）。
> 历史上的 "ENSS / 神经基底进化" 措辞仅指下述机制，不含全主干 NAS。

## 1. Overview

We study whether an LLM agent's cognitive architecture can be automatically
co-designed per task, above a frozen backbone. The architecture is treated as
an evolutionary object:

```
Task
 |
 v
Architecture Genome  G = (M, R, C)
 |
 v
Evolution Controller (Pareto selection, mutation, crossover)
 |
 v
Agent Population
 |
 v
Multi-objective Evaluation (capability, cost)
 |
 v
Next Generation
```

## 2. Architecture Genome (corrected semantics)

Each candidate is a genome over three real, activated genes:

- **Memory M** — episodic memory over a leakage-free experience bank built
  from the benchmark's train/calibration split only:
  - `recency`: most recent k bank entries enter the prompt;
  - `retrieval`: TF-IDF similarity top-k selection;
  - `mamba2`: a real, trainable Mamba-2 substrate (Transformers
    `Mamba2Model`) integrates the bank as an ordered sequence and scores
    candidates against the resulting order-dependent memory state;
  - `hybrid`: retrieval top-(k-1) plus the most recent entry.
- **Reasoning R** — prompt-level strategy: `direct`, `cot`, `verify`,
  `planner` (distinct instruction templates).
- **Context policy C** — exemplar verbosity: `full` / `truncated` /
  `answer_only`, which changes real prompt-token cost.

Every gene changes real inference behavior; this is enforced by tests
(e.g., different memory genes provably produce different prompts).

## 3. Evolution Operators

- **Mutation**: replace one gene with another value in the configured space.
- **Crossover**: uniform gene-level recombination of two parents.
- **Selection**: NSGA-style non-dominated sorting with crowding-distance
  diversity over raw objectives (capability, efficiency, adaptability).
  Scalar fitness is used for logging only, never as the selection signal.
- **Weight inheritance (appendix mechanism)**: children sharing a parent's
  memory substrate inherit the parent's post-adaptation substrate weights;
  each candidate receives the same fixed adaptation budget
  (`configs/phase17_adaptation.yaml`) with the backbone frozen.

## 4. Multi-Objective Evaluation

Objectives (persisted raw per candidate, `history.jsonl` population records):

1. capability — task accuracy on the evaluation slice;
2. efficiency — parameter-footprint proxy blended with measured
   prompt-token cost;
3. adaptability — accuracy on a harder/shifted subset.

## 5. Candidate Adaptation

For genomes with a trainable substrate (`mamba2`), the substrate is adapted
on a fixed calibration split (48 train samples, 30 AdamW steps, fixed
learning rate and seed) before evaluation. The LLM backbone is never trained.

## 6. Relationship to Prior Paradigms

AlphaEvolve evolves programs; NAS optimizes static networks; agent-workflow
search optimizes cooperation topology. Here the search object is a single
agent's cognitive configuration (memory/reasoning/context) under multi-objective
capability–cost criteria.

## 7. Hypothesis (as tested)

Task-adaptive cognitive configurations provide better capability–cost
tradeoffs than manually designed fixed agent configurations. (Search-algorithm
superiority over random search is explicitly **not** hypothesized; see
`paper/experiments.md` and the claim audit.)
