# Phase 21 — Final Audit, Generalization Diagnostics, and Manuscript Lock

## Status

**Final research-audit phase. No new algorithm development.**

Phase-20 delivered a corrected structured search space, a third long-context task, pre-registered holdout evaluation, cross-backbone transfer, and mechanism artifacts. It also revealed the central limitation:

- task-conditioned search selects different architectures on dev/search splits;
- only GSM8K shows a clear own-task holdout advantage;
- PubMedQA and QASPER dev-selected architectures do not generalize as the best holdout configurations;
- C3 (evolution > random) and C5 (Mamba performance advantage) remain permanently closed.

Phase-21 exists to remove the last semantic/confounding issues, diagnose QASPER-7B behavior, and lock a submission-ready manuscript. Do not add new search features or tune toward better results.

---

# Task 1 — Task-Aware Phenotype Canonicalization

Planner audit of Phase-20 found that `input_context_budget` is included in every structured genome/hash, but it only changes computation for long-context tasks such as QASPER.

Therefore on GSM8K and PubMedQA, different `input_context_budget` values can represent identical effective computation while being counted as distinct phenotypes.

Implement a task-aware effective phenotype, e.g.:

```python
effective_genome_for_task(genome, benchmark)
task_phenotype_hash(genome, benchmark)
```

Rules:

- QASPER/long-context tasks: `input_context_budget` remains active.
- GSM8K/PubMedQA: normalize `input_context_budget=None` before dedup/hash.
- Continue all existing conditional normalization (no-memory, retrieval-only genes, Mamba-only genes, etc.).
- Cache keys and search dedup must use the effective task phenotype where appropriate.
- Add tests proving architectures differing only in inactive task-specific genes hash identically for GSM8K/PubMedQA but not for QASPER.

## Sensitivity rerun

After the fix, rerun **dev/search only** for:
- GSM8K seeds 0/1/2
- PubMedQA seeds 0/1/2

Use the same Phase-20 search budgets.

This is a sensitivity audit, not a new holdout experiment. Do **not** substitute new architectures into Phase-20 holdout results after seeing holdout data.

Report whether task-aware dedup changes:
- selected architecture families;
- phenotype diversity;
- duplicate rate;
- C2a search-side distribution conclusion.

If it changes materially, downgrade C2a. If it does not, report robustness to the dedup correction.

---

# Task 2 — Fix the Memory-Ablation Interpretation

The Phase-20 `no_memory` configuration is explicitly:

> A_gsm phenotype with memory disabled.

Therefore:
- `A_gsm vs no_memory` on GSM8K is a controlled memory ablation;
- `A_pubmed vs no_memory` and `A_qasper vs no_memory` are **not** pure memory ablations because reasoning/context genes differ.

Do not use the latter comparisons to claim memory causality.

Update:
- `docs/claim_audit.md`
- `docs/phase20_results.md`
- `paper/manuscript_v1.md`

C4 must be stated only where a same-genome memory on/off comparison exists. Preserve Phase-19 evidence if it was controlled; do not mix confounded Phase-20 comparisons into the causal claim.

If a controlled PubMedQA/QASPER memory ablation is desired, run the exact same frozen genome with memory enabled vs disabled. Treat it as a pre-specified audit comparison, not architecture reselection.

---

# Task 3 — Diagnose QASPER 7B Collapse Before Naming It “Backbone Dependence”

Phase-20 shows a striking pattern:
- A_qasper: 0.1379 (1.5B) -> 0.0064 (7B)
- fixed retrieval/recency/hybrid/Mamba2 similarly collapse near zero
- A_gsm and no_memory remain around 0.19–0.21 on QASPER 7B.

This strongly suggests an interaction between exemplars/prompting and the 7B backbone, but the current evidence does not identify the mechanism.

Do not call this a pure model-capability failure yet.

Run a **diagnostic-only**, frozen-protocol analysis on a fixed small set of QASPER items. No tuning.

For representative configurations:
- A_qasper
- A_gsm
- no_memory
- fixed_retrieval

and both 1.5B / 7B, persist:
- raw generated text;
- extracted final answer;
- marker (`####`) compliance;
- output token length;
- empty/degenerate-output rate;
- normalized F1 on extracted answer;
- normalized F1 on whole continuation (diagnostic only);
- prompt length;
- exemplar count;
- input context budget.

Classify the failure mode:
1. answer-extraction / formatting mismatch;
2. exemplar overload / context distraction;
3. generation degeneration;
4. genuine answer-quality degradation;
5. mixed/unclear.

No prompt change is allowed based on these diagnostics for the main Phase-20 result.

Required artifact:
- `results/phase21_qasper7b_diagnostic.json`
- `docs/phase21_qasper7b_diagnostic.md`

---

# Task 4 — Complete Mechanism Capture

Current Phase-20 mechanism cases contain QASPER entries with `output=null`.

Fix QASPER prediction logging to persist:
- model;
- config name;
- raw output;
- extracted answer;
- score;
- recalled exemplars;
- item index.

Regenerate a small mechanism-only capture for QASPER (no need to rerun the full matrix).

Final mechanism section must include:
- at least 2 successful and 2 failed GSM8K cases;
- at least 2 PubMedQA cases;
- at least 2 QASPER cases with actual raw outputs;
- at least one QASPER 1.5B vs 7B paired failure case.

---

# Task 5 — Final Claim Lock

After Tasks 1–4, freeze the paper claims.

## Core claims allowed

1. Cognitive architecture choices (reasoning, memory/exemplar policy, context allocation) materially change capability-cost behavior.
2. Automatic structured co-design can discover strong configurations, with a large held-out gain on GSM8K over simple fixed baselines.
3. Search-side architecture preferences differ by task, but dev-selected task-specific architectures do **not** universally generalize as the best holdout configurations.
4. Task/backbone interactions are substantial and must be evaluated explicitly.
5. The work provides a leakage-safe, auditable architecture-search protocol with per-item statistics and negative-result reporting.

## Claims that must remain limited or closed

- C2b universal own-task superiority: **unsupported**.
- ENSS > random search: **closed**.
- Mamba improves performance: **closed**.
- universal memory benefit: only claim where controlled same-genome ablation supports it.
- full neural architecture self-evolution: **not allowed**.
- QASPER 7B “backbone dependence” as a causal explanation: only after Task 3 diagnosis; otherwise say “backbone–prompt/configuration interaction”.

## Recommended paper framing

Prefer:

> **Task-Conditioned Cognitive Architecture Co-Design for LLM Agents: A Controlled Study of Generalization, Cost, and Failure Modes**

The strongest scientific story is now not “evolution finds universally optimal task-specific brains.” It is:

> architecture choices matter substantially; automatic search exposes different task-conditioned preferences, but those preferences can overfit small search splits and interact strongly with backbone scale. A rigorous held-out audit is necessary to distinguish search-side specialization from generalizable architecture advantage.

This negative/diagnostic result is part of the contribution, not something to hide.

---

# Task 6 — Manuscript Finalization

Update/create:

```text
paper/
  manuscript_v2.md
  abstract_v2.md
  contribution.md
  method.md
  experiments.md
  limitations.md
  phase21_tables.md
  phase21_figures_data.json

docs/
  claim_audit.md
  phase21_final_audit.md
```

Manuscript requirements:
- no legacy LoRA/QLoRA-as-context wording;
- no “Mamba improves performance” claim;
- no ENSS > random claim;
- distinguish dev/search results from untouched holdout results;
- state that PubMedQA/QASPER task-selected architectures failed to dominate on holdout;
- separate controlled causal ablations from cross-configuration comparisons;
- discuss small dev-set overfitting explicitly;
- report QASPER-7B failure diagnosis with its uncertainty.

---

# Stop Rule

After this phase, stop experimental development unless a reviewer later requests a specific additional experiment.

No Phase-22 algorithm expansion.

The next step after Phase-21 is:
1. venue targeting;
2. manuscript polishing;
3. figure/table production;
4. submission checklist.

Suggested commit message:

`[Phase-21] final generalization audit and manuscript lock`
