# Phase 20 — Structured Cognitive Co-Design After Phase-19 Holdout

## Status

**GO, with mandatory hotfix gate. Phase-19 robustness passed under the narrower-paper route, but commit `c772108` exposed several semantic/reproducibility issues that must be fixed before any Phase-20 matrix result becomes paper evidence.**

The authoritative execution order is now:

1. finish the Phase-20 semantic hotfix gate;
2. bump cache/schema version and invalidate affected pre-hotfix results;
3. rerun only results affected by changed semantics;
4. freeze selected per-task architectures;
5. perform held-out transfer, backbone transfer, and mechanism analysis;
6. update the claim audit and manuscript.

See also `plans/phase20_hotfix_plan.md`.

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
  retrieval_metric: [tfidf, hashed_bow]  # retrieval/hybrid only; do not call hash-BOW "dense retrieval"
  state_size: [32, 64, 128, 256]         # mamba2 only
  hybrid_retrieval_fraction: [0.25, 0.5, 0.75]

reasoning:
  strategy: [direct, cot, verify, planner]
  depth: [1, 2, 3, 4]
  verifier_passes: [1, 2, 3]              # verify only; zero-pass removed to avoid ambiguous semantics

context_policy:
  mode: [full, truncated, answer_only]
  exemplar_token_budget: [128, 256, 512, 768, 1024]
  exemplar_count: [0, 1, 2, 3, 4, 6, 8]

input_context:
  budget: [512, 1024, 2048, 4096]       # active on long-context tasks such as QASPER

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


## Task 1.5 — Mandatory Semantic / Reproducibility Hotfix Gate

This gate supersedes any pre-hotfix Phase-20 matrix result affected by the following semantics.

### Stable embeddings
- replace Python built-in `hash()` with a process-stable digest mapping (SHA-256/BLAKE2 or equivalent);
- add a subprocess regression test proving identical embeddings across independent Python processes.

### Canonical no-memory phenotype
- when `exemplar_count=0`, memory selection is behaviorally inactive;
- normalize equivalent no-memory genomes to one effective phenotype/hash;
- disable memory adaptation when no memory is actually injected.

### Verifier semantics
- every `verifier_passes` value must map exactly to its stated number of verification passes;
- zero-pass is removed from the Phase-20 search space unless implemented as a genuinely distinct explicit path.

### Honest retrieval naming
- current hashed bag-of-words cosine retrieval must be named `hashed_bow` (or similarly precise);
- the term `dense retrieval` is reserved for a real embedding-based dense retriever.

### Token semantics
- fields named `*_token_budget` must be enforced using the actual model tokenizer, not whitespace word counts;
- if a word budget is used, name it `*_word_budget` explicitly.

### QASPER long-context path
- QASPER must expose a real genome-controlled **input/document context budget**, separate from exemplar verbosity;
- the document/evidence budget must change how much paper context reaches the model;
- pre-hotfix QASPER runs that used a fixed 2500-word paper truncation are invalid for the long-context-budget claim.

### QASPER metric
- implement LongBench-compatible answer normalization before QA F1 (lowercase, punctuation removal, article removal, whitespace normalization);
- clearly state whether scoring uses the whole continuation or the extracted final answer.

### Cache isolation
- bump the Phase-20 pipeline/cache schema version after these fixes;
- never aggregate pre-hotfix and post-hotfix caches/results.

### Gate
Paper-facing Phase-20 experiments resume only after all corresponding regression tests pass.


---

# Task 2 — Structure-Aware Operators

Evolution remains an architecture-generation mechanism, not a claimed superior optimizer.

Implement local, semantically valid mutations:

- `memory.k: 3 -> 4` rather than arbitrary jumps by default;
- `exemplar_token_budget: 256 -> 512` via neighbors;
- `input_context.budget: 1024 -> 2048` via neighbors on long-context tasks;
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
4. for QASPER, ensure the genome-controlled input-context budget is active in the actual document path;
5. use LongBench-compatible normalized QA F1;
6. freeze the evaluation protocol before seeing holdout results.

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
2. complete the mandatory semantic/reproducibility hotfix gate from the review of `c772108`;
3. bump cache/schema and invalidate affected pre-hotfix results;
4. implement/verify the corrected structured genome + normalization/tests;
5. amend/freeze the third-task preregistration before corrected QASPER paper-facing runs;
6. run small validation first;
7. perform task-transfer + mechanistic analysis;
8. evaluate frozen representatives on 7B;
9. update claim audit without reopening C3/C5;
10. stop if the evidence does not strengthen the narrower paper story.

Suggested commit message:

```text
[Phase-20] structured task-conditioned cognitive co-design validation
```
