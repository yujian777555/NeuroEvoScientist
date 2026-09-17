# Phase 20 — Structured Search-Space Expansion After Robustness Gate

## Status

**Conditional phase. Do not execute before Phase-19 finishes.**

Phase-18 established three important facts under the corrected schema:

1. task-dependent cognitive configurations are real and reproducible;
2. memory/context choices materially affect capability and inference cost;
3. ENSS is **not** currently more sample-efficient than equal-budget random search in the 48-point discrete space.

Therefore Phase-20 must not try to "tune ENSS until it beats random". Its purpose is to test whether evolutionary search becomes useful only when the architecture space has genuine structure, locality, conditional dependencies, and a size that random search cannot nearly exhaust.

Scientific correctness has priority over recovering C3.

---

## Entry Gate from Phase-19

Execute Phase-20 only if Phase-19 shows that the core task-conditioned architecture result survives at least one of the following robustness tests:

- held-out GSM8K / PubMedQA evaluation;
- cross-task architecture transfer showing a task-specific advantage;
- cross-backbone transfer from Qwen2.5-1.5B to a larger backbone.

If Phase-19 fails to reproduce task conditioning, **stop architecture-space expansion** and move directly to paper revision around the narrower supported findings.

---

# Goal

Replace the tiny 48-point categorical space with a structured, hierarchical cognitive co-design space where nearby genomes represent meaningfully related architectures and evolutionary operators can exploit locality.

The primary research question is:

> Does structured evolutionary search provide a useful capability–cost search advantage over equal-budget random search once the cognitive architecture space is large, conditional, and non-enumerable under the evaluation budget?

This is a fresh hypothesis test. Phase-18 C3 remains unsupported unless Phase-20 provides new evidence.

---

# Task 1 — Expand the Genome Semantically, Not Combinatorially

Keep the corrected Phase-17/18 semantics:

- `memory`
- `reasoning`
- `context_policy`
- `quantization` only when it maps to a real runtime mechanism

Add real, interpretable sub-genes.

Recommended genome:

```yaml
memory:
  type: [recency, retrieval, mamba2, hybrid]
  k: [1, 2, 3, 4, 6, 8]
  retrieval_metric: [tfidf, dense]        # active only for retrieval/hybrid
  state_size: [32, 64, 128, 256]         # active only for mamba2
  hybrid_retrieval_fraction: [0.25, 0.5, 0.75]

reasoning:
  strategy: [direct, cot, verify, planner]
  depth: [1, 2, 3, 4]
  verifier_passes: [0, 1, 2]              # active only for verify

context_policy:
  mode: [full, truncated, answer_only]
  token_budget: [128, 256, 512, 768, 1024]
  exemplar_count: [0, 1, 2, 3, 4, 6, 8]

adaptation:
  enabled: [false, true]
  steps: [0, 10, 20, 40]                 # conditional on enabled
```

Rules:

- every active gene must change real computation, prompt construction, memory behavior, or adaptation cost;
- inactive conditional genes must not create duplicate phenotypes;
- do not re-introduce LoRA/QLoRA names unless actual adapters are instantiated and trained;
- do not call a component Mamba unless the real Mamba2 path is used;
- preserve the frozen-backbone scope unless Phase-19 explicitly justifies otherwise.

### Deliverable

`configs/phase20_structured_search_space.yaml`

plus a canonical genome normalizer that removes inactive fields before hashing/evaluation.

---

# Task 2 — Design Structure-Aware Evolution Operators

The current operators treat architecture choices too independently.

Implement mutation/crossover that respects hierarchy and locality:

### Local mutation examples

- `memory.k: 3 -> 4`, not random jump `1 -> 8` by default;
- `token_budget: 256 -> 512` through neighboring values;
- `reasoning.depth: 2 -> 3`;
- changing `memory.type` activates/deactivates only valid dependent genes.

### Crossover rules

- crossover at semantic blocks (`memory`, `reasoning`, `context`), then reconcile dependent sub-genes;
- no invalid child genome may reach evaluation;
- identical normalized phenotypes must be deduplicated.

### Required tests

- conditional-gene validity;
- phenotype normalization;
- locality of mutation;
- no duplicate effective architectures from inactive fields;
- deterministic genome hashing.

---

# Task 3 — Progressive-Fidelity Evaluation

Do not evaluate every candidate on the full benchmark.

Use three fidelity levels:

```text
F0: cheap proxy subset
F1: medium held-out subset
F2: full validation / finalist evaluation
```

Suggested initial setup:

- F0: 32 items
- F1: 128 items
- F2: largest clean held-out set available under Phase-19 split rules

Promotion must depend on raw Pareto objectives, not scalar fitness alone.

Record for every candidate:

- normalized genome;
- fidelity level;
- capability;
- prompt/context tokens;
- latency;
- peak VRAM where available;
- trainable parameter count;
- adaptation steps/time;
- benchmark/backbone/split identifiers;
- seed;
- cache key/model revision.

---

# Task 4 — Search-Efficiency Experiment

Compare under exactly equal candidate-evaluation budgets.

Methods:

```text
Structured ENSS
Uniform Random Search
Optional Bayesian/SMBO baseline if implementation is mature and fair
```

Do not add weak baselines merely to inflate the table.

Budgets should cover a small fraction of the effective search space, e.g.:

```text
{32, 64, 128, 256}
```

Use at least 20 search seeds for offline/oracle landscape simulations when possible and at least 3 real GPU seeds for representative runs.

Report:

- hypervolume vs evaluations;
- best capability vs evaluations;
- regret to best-known Pareto set;
- probability of finding an epsilon-Pareto candidate;
- evaluations-to-threshold;
- wall-clock search cost;
- duplicate-evaluation rate.

### Decision rule

C3 may only be reopened if ENSS shows a consistent advantage across multiple budgets and at least two tasks/backbones.

If it again ties random search, permanently drop search-efficiency superiority from the paper and retain evolution only as the architecture-generation mechanism.

---

# Task 5 — Strengthen Task-Conditioned Evidence

The main paper contribution remains task-conditioned cognitive co-design.

Required comparisons:

1. architecture searched on Task A -> evaluated on Task A;
2. architecture searched on Task A -> evaluated on Task B;
3. architecture searched on Task B -> evaluated on Task B;
4. architecture searched on Task B -> evaluated on Task A.

Use paired evaluation on identical held-out items where possible.

Primary question:

> Is the architecture discovered for a task measurably better on that task than a configuration transferred from another task under comparable cost?

This is more important than recovering C3.

---

# Task 6 — Optional Third Task

Only add a third benchmark if Phase-19 confirms the two-task result and the implementation cost is modest.

Prefer a task with a genuinely different demand profile, such as:

- long-context evidence integration;
- scientific QA with retrieval;
- multi-step tool/reasoning workload.

The purpose is not benchmark count. The purpose is to test whether a third task produces a distinct architectural preference.

Do not add a third task that is merely another short-form QA benchmark with the same structure.

---

# Task 7 — Mechanistic Analysis

For selected Pareto architectures, explain *why* they differ.

Analyze:

- exemplar selections produced by each memory strategy;
- token-budget utilization;
- failure cases improved/degraded by memory;
- reasoning depth/verifier usage;
- architecture sensitivity to removing one gene;
- per-example capability gain versus added token/latency cost.

Produce case studies that connect genome choices to actual inference behavior.

This section is essential for turning the work from "search benchmark" into a scientific analysis of agent architecture design.

---

# Task 8 — Paper Positioning Lock

Unless stronger evidence emerges, the paper-facing positioning should remain:

> **Task-conditioned cognitive architecture co-design for LLM agents**

Allowed core claims:

- agent memory/reasoning/context configurations materially affect capability-cost tradeoffs;
- different tasks favor different cognitive configurations;
- automatic search can recover competitive task-specific configurations;
- memory removal degrades capability under controlled evaluation;
- real Mamba2 is included as a valid candidate but is not claimed to improve performance.

Not allowed without new evidence:

- ENSS is superior to random search;
- Mamba improves performance;
- full neural architecture self-evolution;
- LoRA/QLoRA compression claims from legacy phases;
- universal superiority over manually designed fixed agents.

---

# Required Deliverables

```text
configs/
  phase20_structured_search_space.yaml

results/
  phase20_search_efficiency.csv
  phase20_task_transfer.csv
  phase20_pareto.json
  phase20_mechanism_cases.json

paper/
  phase20_tables.md
  phase20_figures_data.json

docs/
  phase20_results.md
  phase20_claim_update.md
```

Update:

- `status.json`
- `CHANGELOG.md`
- `docs/claim_audit.md`

---

# Stop Conditions

Stop Phase-20 and move to manuscript finalization if any of the following occurs:

1. Phase-19 task-conditioning result does not hold on held-out data;
2. expanded-space ENSS again ties random search across fair budgets;
3. additional search-space complexity does not create meaningful capability/cost diversity;
4. the third task does not produce a distinct architectural preference;
5. new complexity makes claims less interpretable rather than more informative.

Do not continue burning GPU time to rescue a failed claim.

---

# Executor Instruction

Kimi is the executor. Do not redefine the research objective.

Execution order:

1. finish Phase-19 first;
2. report Phase-19 robustness results to Planner;
3. only after Planner confirms the gate, begin Phase-20;
4. implement the structured genome and tests before any large GPU search;
5. run small fidelity-validation experiments before full budgets;
6. preserve all negative results and update claim audit honestly.

Suggested commit message when this phase is eventually completed:

```text
[Phase-20] structured cognitive search-space expansion and efficiency audit
```
