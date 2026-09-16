# Phase 17 — Substrate Semantics Correction + Real Mamba Validation

## Why this phase exists

Phase-16 produced useful evidence for task-conditioned architecture selection, but Planner review found two claim-critical semantic problems that must be fixed before paper finalization:

1. `src/models/mamba_memory.py` is still a placeholder (`nn.Linear`) rather than a real Mamba/Mamba-2/SSM implementation. Therefore current results must **not** be described as validating Mamba neural memory.
2. In the real evaluator path, `compression={lora, qlora, int8}` currently controls exemplar verbosity/context budget. LoRA, QLoRA and INT8 are model adaptation/quantization techniques, not prompt-compression levels. The paper must not conflate them.

A third result also requires resolution:

3. `no_inherit` consistently outperforms full ENSS on GSM8K in Phase-16. Weight inheritance therefore cannot currently be claimed as a beneficial component.

The goal of Phase-17 is to make implementation semantics match paper terminology before scaling or writing final claims.

---

## Goal

Produce a semantically valid ENSS search space in which every named gene corresponds to the real mechanism it claims to represent, then run a focused experiment that answers:

> Does a real trainable Mamba/SSM memory substrate, with short candidate adaptation and genuine weight inheritance, improve the capability-efficiency Pareto frontier compared with non-Mamba memory substrates?

Do **not** expand model size or benchmark count until this is resolved.

---

## Task 1 — Fix the genome schema

Replace the overloaded current schema with explicit genes.

Recommended schema:

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
  - int8
```

Rules:

- `context_policy` controls exemplar/context verbosity only.
- `quantization=int8` must correspond to real model/runtime quantization if enabled; otherwise omit this gene from experiments.
- Remove the names `lora` and `qlora` from context-compression behavior.
- Add LoRA/QLoRA only if an actual adapter is instantiated and trained.
- Update serialization, search-space enumeration, CLI, result files and paper-facing names consistently.

Backward compatibility with old results is not required; old Phase-14/15/16 results should be tagged as `legacy-schema` and retained for audit only.

### Success check

A test must assert that each genome value maps to the actual intended mechanism, not merely a display label.

---

## Task 2 — Replace placeholder Mamba with a real implementation

Current placeholder:

```python
nn.Linear(hidden_size, hidden_size)
```

is not acceptable as a Mamba claim.

Implement one real path, in priority order:

1. official/standard `mamba_ssm` Mamba-2 block if supported in the A800 environment;
2. a maintained Transformers-compatible Mamba/Mamba-2 implementation;
3. if neither is technically viable, rename the gene to `recurrent_ssm_proxy` and remove all Mamba-specific paper claims.

Do not silently fall back from real Mamba to the proxy under the name `mamba`.

### Required behavior

The real Mamba memory path must:

- consume a sequence of experience embeddings, not a single independent vector;
- maintain/order-dependent state or sequence computation;
- produce a memory representation used by recall or downstream reasoning;
- expose trainable parameters;
- support `state_dict()` so parent-child inheritance can be measured exactly.

### Required tests

Add tests that verify:

- order sensitivity: permuting the same experience sequence changes memory output;
- state sensitivity: adding an episode changes subsequent recall representation;
- gradient flow through the Mamba substrate;
- `state_dict` contains real substrate parameters;
- memory outputs differ from the old linear proxy on the same inputs;
- no code path labels the placeholder as Mamba.

---

## Task 3 — Make weight inheritance scientifically meaningful

Phase-16 showed `no_inherit > ENSS` on GSM8K. Do not hide this result.

The reason inheritance is currently weak is that candidate substrate weights are not meaningfully trained before reproduction.

Introduce a **small, fixed adaptation budget** per candidate only for trainable substrate/adapters, with the LLM backbone frozen.

Example protocol:

```text
Frozen Qwen2.5-1.5B backbone
+ trainable memory substrate / adapter only
+ calibration split: small fixed set
+ N adaptation steps (same N for every candidate)
+ evaluate on disjoint validation subset
```

Recommended initial budget:

- 32–64 calibration samples
- 20–50 optimizer steps per candidate
- fixed optimizer / learning rate across all candidates
- no benchmark test-item leakage

Then compare:

- child initialized from inherited compatible parent substrate weights;
- child initialized from scratch;
- identical adaptation budget.

Record:

- pre-adaptation score;
- post-adaptation score;
- steps to threshold;
- final validation score;
- wall-clock adaptation cost.

Weight inheritance may only remain a positive contribution if it improves sample/step efficiency or final Pareto performance under this controlled protocol.

If it still hurts, remove inheritance from the core ENSS method and report it as a negative ablation/finding.

---

## Task 4 — Separate search fitness from reporting metrics

Do not rely on one weighted scalar as the main scientific conclusion.

For each candidate, persist raw objectives:

- capability;
- measured prompt/context tokens;
- measured latency;
- measured peak GPU memory where feasible;
- trainable parameter count;
- adaptation cost;
- quantized model footprint if real quantization is enabled.

Pareto selection must operate on explicitly documented objectives.

Any scalar `fitness` may be kept only for logging/visualization and must not obscure Pareto comparisons.

---

## Task 5 — Focused real experiment before scaling

Do not immediately repeat the full Phase-16 matrix.

First run a focused validation on one benchmark (GSM8K) with:

- Qwen2.5-1.5B frozen backbone;
- real `mamba2` substrate;
- retrieval and recency baselines;
- population 12–16;
- generations 6–10;
- seeds 0/1/2;
- candidate adaptation enabled;
- inheritance on/off paired comparison.

Minimum comparisons:

```text
ENSS(real Mamba + inheritance)
ENSS(real Mamba, no inheritance)
ENSS(no Mamba gene)
Random Search with equal evaluation budget
Fixed retrieval memory
Fixed recency memory
```

Only if the focused experiment passes the gates below should PubMedQA and larger runs be launched.

---

## Task 6 — Re-run task-conditioned validation only after semantic gate passes

After Task 5 succeeds, rerun GSM8K + PubMedQA under the corrected schema.

The paper-facing claim requires all of the following:

1. different tasks repeatedly select different substrate configurations across seeds;
2. real Mamba/SSM participates in an actual computation path when selected;
3. ENSS beats or improves the Pareto frontier over equal-budget random search;
4. memory removal degrades capability under controlled cost accounting;
5. any inheritance claim is supported by adaptation-speed or performance evidence.

---

## Paper-claim rules for Phase-17

Until this phase is completed:

### Allowed from Phase-16

- task-conditioned agent configurations were observed;
- episodic memory choice changes prompt context and measured capability/cost;
- ENSS showed a small advantage over equal-budget random search on GSM8K across 3 seeds;
- reasoning/context choices differ between GSM8K and PubMedQA.

### Not yet allowed

- "real Mamba neural substrate improves performance";
- "Mamba memory was validated";
- "LoRA/QLoRA compression improves efficiency";
- "weight inheritance improves ENSS";
- "neural architecture self-evolution" if the only learned neural component remains the frozen backbone.

Use precise wording in docs and results until corrected experiments exist.

---

## Required deliverables

```text
src/
  genome/                # corrected schema
  models/
    mamba_memory.py      # real Mamba/Mamba-2, or renamed proxy
  evolution/
    inheritance.py       # real compatible parameter transfer
  evaluator/             # corrected context/quantization semantics

configs/
  phase17_search_space.yaml
  phase17_adaptation.yaml

results/
  phase17_focused_matrix.csv
  phase17_inheritance_curve.json
  phase17_pareto.json

 docs/
  phase17_results.md
  claim_audit.md
```

`claim_audit.md` must list every paper claim and mark it as:

- supported;
- partially supported;
- unsupported;

with a pointer to the exact experiment/result artifact.

---

## Verification gates

Phase-17 passes only if:

- [ ] placeholder `nn.Linear` is no longer called Mamba;
- [ ] real Mamba/Mamba-2 computation passes order/state/gradient tests;
- [ ] context policy is no longer mislabeled LoRA/QLoRA/INT8;
- [ ] no train/test leakage in memory exemplars or adaptation split;
- [ ] inheritance comparison uses equal adaptation budget;
- [ ] raw Pareto objectives are persisted;
- [ ] 3-seed focused experiment completed;
- [ ] paper claim audit is updated honestly.

---

## Stop conditions

If real Mamba integration is unstable or provides no useful signal after controlled adaptation:

- do not spend more GPU time forcing the claim;
- rename the component accurately (`learned recurrent memory` / `SSM proxy`) or remove it;
- retain the stronger contribution: task-conditioned evolutionary search over agent memory/reasoning/context policies.

If inheritance remains harmful after meaningful substrate training:

- remove it from the core method;
- keep the negative result as an ablation.

Scientific correctness has priority over preserving the original feature list.

---

## Executor instruction

Kimi should implement this phase without redefining the research objective. Any unavoidable change to the core ENSS claim must be recorded in `issues/research_questions.md` and left for Planner review.

After completion, update `status.json`, `CHANGELOG.md`, and commit using:

```text
[Phase-17] correct substrate semantics and validate real Mamba adaptation
```
