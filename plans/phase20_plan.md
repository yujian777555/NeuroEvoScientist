# Phase 20 — Structured Cognitive Co-Design After Phase-19 Holdout

## Status

**GO. Phase-19 robustness gate passed, but only under the narrower-paper route.**

Phase-19 established the final evidence boundary:

- GSM8K: automatically selected configuration strongly beats simple fixed baselines on untouched holdout data;
- PubMedQA: no universal capability superiority; the result is a capability–cost tradeoff;
- task-specific preferences are directionally consistent across both Qwen2.5-1.5B and 7B, but own-task capability gains are small and not individually significant;
- episodic memory contribution survives holdout and strengthens on the larger backbone;
- C3 (ENSS search-efficiency superiority over random search) is permanently closed by the Phase-18 oracle audit;
- Mamba-performance superiority is permanently closed.

Therefore Phase-20 must **not** attempt to rescue C3 or Mamba. Its purpose is to strengthen the main supported scientific story:

> Different tasks induce different capability–cost optima over agent memory, reasoning, and context configuration; structured automatic co-design can expose and analyze these task-specific cognitive architectures above a frozen LLM backbone.

---

# Goal

Build a larger but interpretable structured cognitive-design space, then test whether task identity produces stronger and mechanistically explainable architecture differences on clean held-out data.

Primary research questions:

1. Do task-specific architecture preferences become clearer in a richer, genuinely structured space?
2. Which genome dimensions explain those differences?
3. Are the preferences stable across backbones and held-out data?
4. Can an automatically discovered configuration occupy a better capability–cost Pareto position than generic fixed designs, without claiming the search optimizer itself is superior to random search?

C3 is not reopened in this phase.

---

# Task 1 — Structured Genome Expansion

Keep the corrected Phase-17/19 semantics and frozen-backbone scope.

Recommended genome:

```yaml
memory:
  type: [recency, retrieval, mamba2, hybrid]
  k: [1, 2, 3, 4, 6, 8]
  retrieval_metric: [tfidf, dense]        # retrieval/hybrid only
  state_size: [32, 64, 128, 256]         # mamba2 only
  hybrid_retrieval_fraction: [0.25, 0.5, 0.75]

reasoning:
  strategy: [direct, cot, verify, planner]
  depth: [1, 2, 3, 4]
  verifier_passes: [0, 1, 2]              # verify only

context_policy:
  mode: [full, truncated, answer_only]
  token_budget: [128, 256, 512, 768, 1024]
  exemplar_count: [0, 1, 2, 3, 4, 6, 8]

adaptation:
  enabled: [false, true]
  steps: [0, 10, 20, 40]                 # enabled only
```

Rules:

- every active gene must change real computation, prompt construction, memory behavior, or adaptation cost;
- inactive genes must be normalized away so duplicate phenotypes are not counted as distinct architectures;
- no legacy `compression=lora/qlora/int8` naming;
- `mamba2` must always map to the real trainable Mamba-2 path;
- quantization is excluded unless a real runtime path is implemented and validated.

Deliverables:

- `configs/phase20_structured_search_space.yaml`
- canonical genome normalizer + deterministic phenotype hash
- tests for conditional-gene validity, normalization, and duplicate removal

---

# Task 2 — Structure-Aware Operators

Evolution remains an architecture-generation mechanism, not a claimed superior optimizer.

Implement local, semantically valid mutations:

- `memory.k: 3 -> 4` rather than arbitrary jumps by default;
- `token_budget: 256 -> 512` via neighbors;
- `reasoning.depth: 2 -> 3`;
- dependent genes activated/deactivated consistently when memory/reasoning type changes.

Crossover should occur at semantic blocks (`memory`, `reasoning`, `context`, `adaptation`) followed by normalization.

Required tests:

- no invalid children;
- no inactive-field duplicates;
- mutation locality;
- deterministic normalization/hash.

---

# Task 3 — Task-Specific Evidence Is the Primary Experiment

The key experiment is not ENSS vs Random.

For each task, freeze a selected architecture before final held-out evaluation and compare:

```text
A_taskA -> Task A
A_taskA -> Task B
A_taskB -> Task B
A_taskB -> Task A
```

Use paired item-level statistics on identical held-out items where possible.

Primary outcomes:

- capability difference;
- prompt-token difference;
- latency difference;
- Pareto dominance / hypervolume contribution;
- per-example wins/losses.

Interpretation rule:

- if own-task capability is not significantly higher but uses materially fewer tokens/latency at equal capability, report a capability–cost specialization, not a capability superiority claim.

---

# Task 4 — Add One Genuinely Different Third Task

Phase-19 shows GSM8K and PubMedQA preferences are directionally different but capability separation is small. Add **one** third task only if it creates a distinct demand profile.

Preferred task properties:

- long-context evidence integration, or
- multi-hop retrieval/reasoning, or
- scientific evidence synthesis.

Do not add another short-form QA task that is structurally similar to PubMedQA/GSM8K.

Before any GPU run:

1. document why the task probes a different cognitive demand;
2. pre-register the clean split and calibration protocol;
3. pre-register the expected architecture dimensions to analyze;
4. freeze the evaluation protocol before seeing results.

The goal is to test whether a third task produces a distinct architecture preference, not to cherry-pick a favorable benchmark.

---

# Task 5 — Mechanistic Analysis

This is mandatory and more important than another optimizer comparison.

For representative Pareto architectures, record and analyze:

- which exemplars each memory policy retrieves;
- overlap/divergence of retrieved exemplars across tasks;
- token-budget utilization;
- reasoning depth / verifier usage;
- examples helped or harmed by memory;
- examples where own-task architecture wins over cross-task transfer;
- examples where the cheaper architecture matches the more expensive one.

Produce 8–12 auditable case studies with exact item IDs and model outputs.

Required artifact:

- `results/phase20_mechanism_cases.json`
- `docs/phase20_mechanism_analysis.md`

---

# Task 6 — Cross-Backbone Validation

Do not re-search every architecture on every backbone.

Search/select on Qwen2.5-1.5B, then freeze representative configurations and evaluate them on Qwen2.5-7B.

Report:

- ranking consistency;
- direction of task specialization;
- capability changes;
- cost changes;
- any ranking reversals.

A ranking reversal is a scientific result, not a failure.

---

# Task 7 — Search-Space Characterization

Because C3 is permanently closed, Phase-20 must not use random search as a target to beat.

Random sampling may still be used as a **diagnostic reference** to characterize:

- phenotype diversity;
- duplicate rate;
- objective distribution;
- coverage of the structured space.

Do not write or optimize toward:

> ENSS is more sample-efficient than Random Search.

That claim is closed unless a future, separately pre-registered paper explicitly reopens it.

---

# Task 8 — Paper Claim Lock v2

Allowed paper-facing core claims after Phase-19:

1. agent memory/reasoning/context choices materially affect capability–cost tradeoffs;
2. automatic co-design can discover strong task-specific configurations;
3. GSM8K shows a large held-out advantage over simple fixed baselines;
4. PubMedQA shows competitive capability–cost tradeoffs rather than universal capability superiority;
5. episodic memory removal degrades held-out capability, especially on the larger backbone;
6. task-specific architecture preferences are directionally stable across 1.5B and 7B backbones;
7. negative findings on random-search superiority and Mamba performance are explicitly retained.

Not allowed:

- universal automatic-search superiority;
- ENSS > Random Search;
- Mamba improves performance;
- full neural architecture self-evolution;
- task-specific capability superiority when Phase-19 only shows non-significant differences.

Preferred positioning remains:

> **Task-conditioned cognitive architecture co-design for LLM agents**

---

# Required Deliverables

```text
configs/
  phase20_structured_search_space.yaml
  phase20_protocol.yaml

results/
  phase20_task_transfer.csv
  phase20_pareto.json
  phase20_architecture_distribution.json
  phase20_mechanism_cases.json
  phase20_backbone_transfer.csv

paper/
  phase20_tables.md
  phase20_figures_data.json

docs/
  phase20_results.md
  phase20_mechanism_analysis.md
  phase20_claim_update.md
```

Update:

- `status.json`
- `CHANGELOG.md`
- `docs/claim_audit.md`
- `paper/manuscript_v1.md`

---

# Stop Conditions

Stop Phase-20 and move directly to manuscript finalization if any of the following occurs:

1. richer structured genes do not create meaningful objective diversity;
2. third-task preference is not distinct after the pre-registered test;
3. task-specific configurations show no capability–cost specialization on held-out data;
4. added complexity reduces interpretability without producing stronger scientific evidence;
5. the experiment starts drifting toward post-hoc tuning to rescue a failed claim.

Do not spend GPU time trying to rescue C3 or Mamba.

---

# Executor Instruction

Kimi is the executor. Do not redefine the research objective.

Execution order:

1. treat Phase-19 claims and negative findings as locked;
2. implement structured genome + normalization/tests;
3. pre-register the third-task protocol before running it;
4. run small validation first;
5. perform task-transfer + mechanistic analysis;
6. evaluate frozen representatives on 7B;
7. update claim audit without reopening C3/C5;
8. stop if the evidence does not strengthen the narrower paper story.

Suggested commit message:

```text
[Phase-20] structured task-conditioned cognitive co-design validation
```
