# Phase-19 — Paper Lock + Held-Out Robustness + Cross-Backbone Transfer

## Why this phase exists

Phase-18 is the point where the research claim must be frozen rather than expanded.

The corrected-schema audit established:

- C1: searched configurations can substantially outperform simple fixed baselines on GSM8K, but the PubMedQA picture is mixed if raw capability is isolated;
- C2: GSM8K and PubMedQA prefer different cognitive configurations under the corrected schema;
- C3: **ENSS does not outperform equal-budget random search in sample efficiency** on the fully audited 48-point landscape;
- C4: episodic-memory/context choices materially change capability and cost;
- C5: real Mamba-2 is a valid search-space component but **does not improve performance in the current protocol**;
- C6: inheritance improves post-adaptation loss in paired tests but does not improve capability, so it is an appendix mechanism rather than a headline contribution;
- C7: context policy creates a real capability/token-cost tradeoff;
- C8: the defensible scope is cognitive-architecture co-design above a frozen LLM backbone, not full neural-architecture self-evolution.

Phase-19 must therefore do two things before manuscript finalization:

1. test whether the main findings survive on **untouched held-out examples** and a second backbone;
2. migrate all paper-facing text from the old Phase-12–16 terminology to the corrected Phase-17/18 semantics.

This is a robustness and paper-lock phase, **not another algorithm-development phase**.

---

## Frozen paper positioning

Use this as the default paper-facing positioning unless the held-out experiment disproves it:

> **NeuroEvoScientist is an automated task-conditioned cognitive architecture co-design framework for LLM agents. It searches over episodic-memory strategy, reasoning strategy, and context policy under multiple capability/cost objectives.**

Recommended working title:

> **NeuroEvoScientist: Task-Conditioned Cognitive Architecture Co-Design for LLM Agents**

Do not use the phrases below as headline claims:

- "self-evolving neural architecture";
- "Mamba improves agent memory/performance";
- "ENSS is more sample-efficient than random search";
- "LoRA/QLoRA compression gene";
- "tool architecture evolution" unless a tool gene is actually varied in the reported experiment.

The historical identifier `enss` may remain in code for compatibility, but paper text must describe the actual mechanism precisely.

---

## Task 1 — Freeze the method and result-selection protocol

From the start of Phase-19:

- do not change evolutionary operators, objective definitions, genome semantics, prompt templates, memory algorithms, or context-policy behavior to improve results;
- correctness fixes are allowed only if documented before rerunning results;
- record the exact Phase-18 commit used to select architectures;
- choose all Phase-19 candidate configurations **before** evaluating held-out data.

Create:

```text
configs/phase19_protocol.yaml
results/phase19_selection_lock.json
```

`phase19_selection_lock.json` must include:

- source commit (`dd4bb7f...`);
- selected GSM8K architecture(s);
- selected PubMedQA architecture(s);
- fixed baselines;
- no-memory baseline;
- any Pareto representatives used;
- exact evaluation subsets;
- model generation settings.

No post-hoc replacement of architectures after hold-out results are observed.

---

## Task 2 — Use genuinely untouched held-out evaluation subsets

The Phase-18 search/evaluation used the first 100 examples. Phase-19 must not reuse those examples as the primary robustness test.

### GSM8K

Use:

```text
search/dev history: test[0:100]        # already used in Phase-18; do not report as holdout
held-out test:      test[100:1319]     # untouched by Phase-18 search
memory/adaptation:  train split only
```

Evaluate on all available held-out test items from index 100 onward.

### PubMedQA

Current evaluator reserves `samples[500:]` for calibration. Keep that separation.

Use:

```text
search/dev history: samples[0:100]     # already used in Phase-18
held-out test:      samples[100:500]   # untouched 400 examples
memory/adaptation:  samples[500:1000]  # calibration bank only
```

Do not evaluate on `samples[500:1000]` while they are used as memory/adaptation data.

Add explicit CLI/index-range support if necessary, but do not alter task semantics.

Add tests asserting that search/dev, holdout, and calibration indices are pairwise disjoint.

---

## Task 3 — Cross-task architecture-transfer matrix

This is the strongest direct test of the task-conditioned co-design claim.

Freeze at least one representative architecture selected for each task from Phase-18:

```text
A_gsm     = architecture selected from GSM8K
A_pubmed  = architecture selected from PubMedQA
```

Evaluate the 2×2 transfer matrix on held-out data:

| Frozen architecture | GSM8K holdout | PubMedQA holdout |
|---|---:|---:|
| A_gsm | capability/cost | capability/cost |
| A_pubmed | capability/cost | capability/cost |

Also include:

- Fixed Recency + Direct + Full;
- Fixed Retrieval + Direct + Full;
- Fixed Hybrid + Direct + Full;
- Fixed Mamba2 + Direct + Full;
- no-memory baseline;
- 2–3 Pareto representatives when necessary to avoid choosing one arbitrary scalarized point.

Primary evidence for task conditioning should be:

1. the task-selected configuration remains competitive on its own held-out task;
2. task-specific differences persist without re-searching on the holdout;
3. where possible, own-task selection improves the capability-cost tradeoff relative to the swapped task configuration.

Do not force a win if the cross-task matrix does not separate cleanly; report the result and downgrade C2 if necessary.

---

## Task 4 — Cross-backbone transfer

The current evidence is based on Qwen2.5-1.5B-Instruct. A paper-level robustness claim should not depend on a single 1.5B backbone.

Use two frozen backbones:

```text
Backbone A: Qwen2.5-1.5B-Instruct   # existing reference
Backbone B: Qwen2.5-7B-Instruct     # robustness/transfer backbone
```

Rules:

- do **not** rerun architecture search on the 7B model initially;
- transfer the already locked Phase-18/19 configurations to the 7B backbone;
- use the same prompt templates, memory bank, context policies, decoding settings, and held-out indices;
- preserve greedy/deterministic decoding unless there is a documented reason to change it;
- do not compare latency across backbones without clearly normalizing/reporting hardware and batch settings.

The question is:

> Do task-conditioned architecture preferences transfer to a larger frozen backbone, or are they specific to the 1.5B model?

If ranking reverses on 7B, report the result as backbone dependence rather than modifying the method.

---

## Task 5 — Statistical analysis on item-level outcomes

Phase-19 must save per-item predictions and correctness, not only aggregate accuracy.

Required artifacts:

```text
results/phase19_item_predictions.jsonl
results/phase19_statistics.json
```

For key paired comparisons, compute:

- accuracy / capability difference in percentage points;
- paired bootstrap 95% CI (10,000 resamples, fixed RNG seed);
- exact McNemar test where both systems are evaluated on exactly the same items;
- prompt-token difference and relative reduction;
- latency median + IQR from repeated uncached runs where feasible.

Key comparisons should include:

```text
A_gsm vs A_pubmed on GSM8K holdout
A_pubmed vs A_gsm on PubMedQA holdout
selected config vs no_memory
selected config vs strongest fixed baseline
1.5B vs 7B transfer behavior (reported separately, not pooled)
```

Do not use significance tests to rescue a tiny or directionally inconsistent effect. Report effect sizes and confidence intervals first.

---

## Task 6 — Re-audit C1, C2, C4, C7 under holdout data

Phase-18's claim audit is not automatically carried over. Re-evaluate the paper-facing claims using Phase-19 holdout results.

### C1 — automated configuration discovery vs fixed baselines

Use more precise wording than Phase-18.

Allowed only if supported:

> Automated co-design discovers configurations that substantially improve over simple fixed baselines on some tasks and produce competitive capability-cost tradeoffs on others.

Do **not** claim universal capability superiority. Phase-18 already showed PubMedQA Fixed Mamba2 capability (0.57) above the selected ENSS configuration (0.53).

### C2 — task-conditioned architecture preference

Promote to a main contribution only if the frozen cross-task configuration result survives held-out evaluation. If only the 100-example development slice separates, downgrade it to an exploratory observation.

### C4 — memory/context contribution

Require the no-memory degradation to persist on held-out items. Separate:

- extra exemplar information benefit;
- memory-selection mechanism benefit;
- token-cost increase.

Do not conflate "having demonstrations" with proof that a particular neural memory substrate is better.

### C7 — context-policy capability/cost tradeoff

Confirm with real token counts on held-out data. Report raw token counts and capability rather than only weighted fitness.

### Permanently closed claims

Unless new evidence arises from the pre-registered Phase-19 protocol (not method changes):

- C3 search-efficiency superiority remains **unsupported**;
- C5 Mamba performance benefit remains **unsupported**;
- C6 inheritance remains an appendix mechanism unless capability or concrete adaptation-cost benefit becomes materially stronger;
- no "full neural architecture self-evolution" wording.

---

## Task 7 — Paper schema migration

The current paper files still contain legacy claims and must be rewritten to match the corrected implementation.

Update at minimum:

```text
paper/contribution.md
paper/method.md
paper/experiments.md
paper/metrics.md
paper/related_work.md
paper/expected_results.md
paper/figures_plan.md
```

### Required method schema

Paper-facing genome should reflect the actual reported search space:

```text
G = (M, R, C)

M = episodic memory policy/substrate
R = reasoning strategy
C = context policy
```

If quantization is fixed to FP16 in the reported experiments, do not present quantization as a searched gene.

Do not present `tool_adapter=basic` as a searched tool gene.

### Required contribution structure

A defensible contribution set is:

1. **Task-conditioned cognitive architecture co-design:** a unified search space over episodic-memory policy, reasoning strategy, and context policy above a frozen LLM backbone.
2. **Multi-objective empirical characterization:** capability, token cost, latency and memory/context tradeoffs, including the complete small-space Pareto landscape.
3. **Task dependence and negative findings:** architectures preferred by math reasoning and biomedical QA differ; equal-budget evolutionary search does not beat random search in this compact space; real Mamba2 is not automatically beneficial.
4. **Reproducible audit protocol:** corrected semantics, leakage-safe calibration/evaluation, raw objectives, claim audit and held-out transfer evaluation.

Contribution 3 may sound unusual, but the negative results materially improve scientific credibility. Do not hide them.

---

## Task 8 — Create manuscript skeleton with observed results only

Create:

```text
paper/manuscript_v1.md
paper/abstract_v1.md
paper/title_candidates.md
```

Suggested structure:

```text
1. Introduction
2. Related Work
3. Problem Formulation
4. NeuroEvoScientist / Cognitive Architecture Co-Design
5. Experimental Protocol
6. Main Results
7. Task-Conditioned Transfer Analysis
8. Search-Efficiency Audit and Negative Results
9. Ablations and Cost Analysis
10. Limitations
11. Conclusion
```

Rules:

- no fabricated citations;
- no unsupported "first" claims;
- no result from Phase-14/15/16 as primary evidence unless explicitly labeled development/legacy;
- Phase-17/18/19 corrected-schema artifacts are the paper evidence base;
- every numerical sentence should point internally to a table/result artifact while drafting.

The abstract must not say ENSS is better than random search.

---

## Required Phase-19 deliverables

```text
configs/
  phase19_protocol.yaml

results/
  phase19_selection_lock.json
  phase19_holdout_results.csv
  phase19_cross_task_matrix.csv
  phase19_backbone_transfer.csv
  phase19_item_predictions.jsonl
  phase19_statistics.json

paper/
  contribution.md              # migrated
  method.md                    # migrated
  experiments.md               # migrated
  metrics.md                   # migrated
  related_work.md              # migrated
  expected_results.md          # replace expectations with observed-result status or archive clearly
  figures_plan.md              # updated to final figures
  manuscript_v1.md
  abstract_v1.md
  title_candidates.md

docs/
  phase19_results.md
  claim_audit.md               # final post-holdout claim state
```

Also update:

```text
status.json
CHANGELOG.md
```

---

## Phase-19 success gates

Phase-19 is complete only if:

- [ ] architectures/configurations are locked before holdout evaluation;
- [ ] GSM8K holdout excludes the first 100 search items;
- [ ] PubMedQA holdout and calibration sets are disjoint;
- [ ] cross-task frozen-architecture matrix is complete;
- [ ] 1.5B and 7B transfer results are complete (or a concrete documented environment blocker exists);
- [ ] per-item predictions are persisted;
- [ ] bootstrap CIs and paired tests are produced for key comparisons;
- [ ] claim audit is rewritten from holdout evidence;
- [ ] legacy paper terminology is removed;
- [ ] manuscript skeleton and abstract use only defensible claims;
- [ ] no algorithm/search modification was made after observing holdout results.

---

## Stop / decision rules

### If C2 survives holdout and preferably both backbones

Proceed to final manuscript polishing and venue targeting. This becomes the main paper story:

> **different tasks favor different capability-cost cognitive configurations, and automated co-design can discover those configurations under a unified search framework.**

### If C2 survives on 1.5B but not 7B

Publish the result as backbone-dependent task-conditioned co-design; do not claim universal architecture preferences.

### If C2 fails on untouched holdout

Do not run more search to chase the result. Reframe the paper around:

- systematic architecture landscape characterization;
- capability-cost tradeoffs of memory/reasoning/context choices;
- negative result that compact evolutionary search does not outperform random search;
- reproducible methodology and semantic audit.

### C3 / C5

Do not reopen the random-search or Mamba-performance claims during Phase-19. Phase-18 already provided decisive evidence for the current search space/protocol.

Scientific claim integrity takes priority over preserving the original project narrative.

---

## Executor instruction

Kimi should execute Phase-19 as a **frozen-protocol validation and paper-migration phase**, not redesign NeuroEvoScientist.

Before any holdout inference, commit the protocol + selection lock. After that commit, do not change the selected architectures or evaluation subsets.

Recommended commit sequence:

```text
[Phase-19a] lock holdout protocol and selected architectures
[Phase-19b] held-out and cross-backbone robustness results
[Phase-19c] migrate paper claims and create manuscript v1
```

When complete, update `status.json` and wait for Planner review before any new experiment or submission-oriented rewriting.
