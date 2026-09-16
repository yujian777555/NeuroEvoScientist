# Phase 18 — Corrected Dual-Benchmark Replication + Search-Efficiency Audit

## Why this phase exists

Phase-17 corrected the claim-critical semantics and completed the focused GSM8K validation under the new schema. It also established three important facts:

1. real Mamba-2 is correctly implemented and trainable, but it did **not** win under the current protocol;
2. weight inheritance changed from harmful to weakly positive after substrate adaptation, but evidence is still small (`n=2` inherited candidates);
3. ENSS is much better than fixed hand-designed baselines, but under the Phase-17 focused GSM8K protocol it is essentially tied with equal-budget Random Search.

Therefore the next phase must **freeze the method** and answer the two remaining paper-critical questions without further feature creep:

- Does task-conditioned architecture differentiation still hold under the corrected Phase-17 schema on both GSM8K and PubMedQA?
- Does ENSS offer any measurable search-efficiency / Pareto-discovery advantage over equal-budget random search when the evaluation budget is smaller than the search space?

Do not attempt to rescue the Mamba claim. Do not add new architecture families unless required to correct a bug.

---

## Goal

Produce the final evidence package needed to decide the paper's defensible core claim:

> ENSS performs task-conditioned evolutionary co-design over real agent memory substrates, reasoning strategies, and context policies, and should be judged by its ability to discover strong Pareto configurations efficiently under a constrained evaluation budget.

Phase-18 is an **audit / replication phase**, not an algorithm-development phase.

---

## Frozen method and schema

Use the Phase-17 corrected schema only:

```yaml
memory:
  - recency
  - retrieval
  - mamba2
  - hybrid

reasoning:
  - direct
  - cot
  - verify
  - planner

context_policy:
  - full
  - truncated
  - answer_only

quantization:
  - fp16
```

Do not reintroduce the legacy `lora/qlora/int8-as-context-policy` semantics.

The current discrete space contains 4 × 4 × 3 = 48 paper-facing configurations (FP16 fixed).

This fact is central to the Phase-18 design: previous `population=16 × generations=10 = 160` budgets exceed the 48-point space, which makes Random Search artificially strong and makes search-algorithm differences hard to interpret.

---

## Task 1 — Re-run task-conditioned validation under the corrected schema

Run both benchmarks with exactly the same corrected Phase-17 semantics:

- GSM8K
- PubMedQA

Required methods:

```text
ENSS
Random Search
Fixed Recency
Fixed Retrieval
Fixed Mamba2
Fixed Hybrid
No Memory
```

Optional secondary ablations if cheap:

```text
No Pareto
No Inheritance
```

### Reproducibility

Use at least:

```text
seeds = {0,1,2}
```

Prefer 5 seeds if cached evaluation makes this affordable.

Use the same frozen Qwen2.5-1.5B backbone, corrected train/calibration/eval split discipline, and no test leakage.

### Required task-conditioned evidence

Do not report only one best architecture.

For each task report:

- best architecture per seed;
- Pareto-set architecture composition;
- frequency of each memory / reasoning / context-policy gene in the final Pareto set;
- capability / token cost / latency / adaptation cost;
- architecture-selection stability across seeds.

The corrected-schema task-conditioned claim is supported only if the two benchmarks repeatedly favor meaningfully different configurations or Pareto-set compositions.

---

## Task 2 — Establish the 48-point architecture landscape

Because the corrected paper-facing search space has only 48 configurations, create a controlled landscape reference rather than guessing whether evolution helps.

Evaluate all 48 configurations for each benchmark under a fixed evaluation protocol where feasible.

Required output per architecture:

```text
benchmark
architecture_id
memory
reasoning
context_policy
capability
prompt_tokens
latency
trainable_parameter_count
adaptation_cost
raw Pareto objectives
```

This exhaustive table is an **analysis oracle**, not a search method baseline.

Purpose:

- identify the true global Pareto front;
- quantify landscape ruggedness;
- measure how quickly ENSS / Random discover near-Pareto points;
- prevent overclaiming from one lucky seed.

If full 48-point adaptation is too expensive, use one deterministic / cached evaluation per architecture and document the approximation explicitly.

---

## Task 3 — Fair ENSS vs Random search-efficiency study

Do not compare methods using 160 evaluations over a 48-point space.

Use constrained budgets smaller than the search space, for example:

```text
B ∈ {12, 24, 36, 48}
```

For each budget, benchmark, and search method, run multiple independent search seeds.

Recommended:

```text
10–20 search seeds
```

Because the architecture evaluations are expensive, reuse the fixed landscape table as a lookup oracle for the **search-policy audit** where scientifically valid. The search algorithm must still make decisions online using only points exposed up to that step.

Compare:

```text
ENSS
Equal-budget Random Search
```

Optional:

```text
No-Pareto / scalar GA
```

### Primary search-efficiency metrics

Report all of the following:

1. best capability vs number of evaluated architectures;
2. Pareto hypervolume vs evaluations;
3. hypervolume regret to the exhaustive global Pareto front;
4. probability of hitting an epsilon-Pareto configuration by budget B;
5. evaluations-to-threshold;
6. area under the best-so-far / hypervolume curve.

Do not use one weighted scalar fitness as the main comparison.

### Interpretation rule

If ENSS does not consistently beat Random on these sample-efficiency metrics:

- mark `ENSS > Random` as unsupported;
- remove search-superiority language from the abstract/contributions;
- keep evolutionary search as the implementation mechanism rather than a claimed superiority result.

Do **not** expand the space merely to manufacture a win.

---

## Task 4 — Resolve the inheritance claim with an adequately sized paired test

Phase-17 inheritance evidence is directionally positive but only `n=2` inherited candidates.

Run a paired inheritance study with enough compatible parent→child cases to make the claim interpretable.

Target:

```text
>= 20 compatible inherited child cases
>= 20 matched scratch controls
```

For each pair use identical:

- architecture compatibility constraints;
- calibration data;
- optimizer;
- learning rate;
- adaptation steps;
- evaluation set.

Persist:

```text
pre_adaptation_loss
post_adaptation_loss
pre_capability
post_capability
wall_clock
steps_to_threshold
```

Use paired statistics / bootstrap confidence intervals.

### Interpretation rule

If the inheritance benefit remains weak or inconsistent:

- demote inheritance from a core contribution to an optional efficiency mechanism / appendix result.

Do not keep it as a headline contribution without adequate evidence.

---

## Task 5 — Freeze the Mamba conclusion

Phase-17 triggered the stop condition:

- Mamba2 is real and valid;
- Mamba2 was not selected as the winning substrate;
- no performance superiority claim is supported.

Phase-18 must **not** spend additional GPU budget trying to make Mamba win.

Allowed paper wording:

> The search space includes a real trainable Mamba-2 memory substrate; under our tested protocol, the evolutionary search preferred simpler recency/hybrid memory, illustrating that ENSS can reject a more complex substrate when it is not beneficial.

This negative result is scientifically useful.

Forbidden wording:

- "Mamba improves agent memory performance";
- "Mamba is a key source of ENSS gains";
- any equivalent unsupported claim.

---

## Task 6 — Final claim audit and paper gate

Update `docs/claim_audit.md` using only corrected-schema Phase-17/18 evidence.

Legacy Phase-14/15/16 results may be discussed as development history but must not be used as final paper evidence if their schema semantics conflict with Phase-17.

Required final claim statuses:

### C1 — Automated search beats fixed manually chosen architectures

Expected: likely supported, but verify on both corrected-schema benchmarks.

### C2 — Different tasks favor different cognitive architectures

Must be re-established under corrected schema on GSM8K + PubMedQA.

### C3 — ENSS is more sample-efficient than equal-budget Random Search

Must be decided by Task 3. Supported or removed; no ambiguous wording.

### C4 — Episodic memory choice materially changes capability/cost

Verify under corrected schema.

### C5 — Mamba improves performance

Remain unsupported / explicitly negative unless new evidence appears incidentally. Do not target it.

### C6 — Weight inheritance improves adaptation efficiency

Decide from Task 4 with adequate sample size.

### C7 — Context policy trades capability for token cost

Validate and report with real token counts.

### C8 — Neural architecture self-evolution

Use cautious wording. The safest current formulation is:

> evolutionary co-design of agent cognitive architecture over trainable memory substrate, reasoning policy, and context policy with a frozen LLM backbone.

Do not imply full backbone neural architecture search.

---

## Required deliverables

```text
configs/
  phase18_eval.yaml
  phase18_search_efficiency.yaml

results/
  phase18_dual_benchmark.csv
  phase18_landscape.csv
  phase18_search_efficiency.csv
  phase18_pareto_fronts.json
  phase18_architecture_distribution.json
  phase18_inheritance_pairs.csv

src/scripts/
  aggregate_phase18.py
  analyze_search_efficiency.py

paper/
  phase18_tables.md
  phase18_figures_data.json

docs/
  phase18_results.md
  claim_audit.md        # updated final audit
```

Preserve raw run logs outside committed large artifacts as before; commit compact aggregated evidence.

---

## Figures / tables Phase-18 must enable

### Figure A — Task-conditioned architecture distributions

GSM8K vs PubMedQA gene frequencies / Pareto-set composition.

### Figure B — Search efficiency

Pareto hypervolume or regret vs number of architecture evaluations:

```text
ENSS vs Random
```

with confidence intervals over search seeds.

### Figure C — Capability vs cost Pareto fronts

One panel per benchmark using the exhaustive 48-point landscape.

### Table A — Corrected-schema main results

Fixed baselines + ENSS + Random on both benchmarks.

### Table B — Inheritance paired study

Inherited vs scratch adaptation efficiency.

---

## Verification gates

Phase-18 passes only if:

- [ ] GSM8K + PubMedQA corrected-schema runs complete;
- [ ] no legacy gene semantics leak into Phase-18 results;
- [ ] architecture landscape / global Pareto reference is available;
- [ ] ENSS vs Random compared at budgets below full-space coverage;
- [ ] search-efficiency confidence intervals reported;
- [ ] task-conditioned architecture shift tested under corrected schema;
- [ ] inheritance paired sample size is no longer `n=2`;
- [ ] Mamba negative result is preserved honestly;
- [ ] final claim audit has no unresolved headline claim;
- [ ] paper tables / figure data can be generated directly from committed aggregates.

---

## Decision after Phase-18

If C1 + C2 + C4 are supported and C3 is supported:

> Proceed to paper writing with evolutionary search efficiency as a central contribution.

If C1 + C2 + C4 are supported but C3 is not:

> Proceed with a narrower paper: automated task-conditioned agent cognitive co-design; evolution is the search engine, not a claimed superior optimizer.

If C2 fails under the corrected schema:

> Do not proceed to final paper framing yet; reassess whether the task-conditioned architecture claim is real.

No further method changes should be made after Phase-18 unless one of these gates fails for a clearly diagnosed implementation reason.

---

## Executor instruction

Kimi should treat Phase-18 as a frozen-method scientific audit. Do not redesign ENSS, add new modules, enlarge the space to force positive results, or optimize specifically for a desired claim.

After completion:

1. update `status.json`;
2. update `CHANGELOG.md`;
3. update `docs/claim_audit.md`;
4. commit all compact aggregate outputs;
5. report whether C1–C8 are supported / partially supported / unsupported.

Commit message:

```text
[Phase-18] corrected dual-benchmark replication and search-efficiency audit
```
