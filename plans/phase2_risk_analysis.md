# Phase-2 Risk Analysis — TACC

Date: 2026-10-14
Status: DESIGN ONLY. Companion to `phase2_controller_design.md` and
`phase2_experiment_design.md`. Purpose: enumerate failure modes *before*
any code, with kill criteria and mitigations.

---

## R1 — No learnable within-task variance (highest risk)

**What Phase-1 showed:** configuration effects were demonstrated at the
*task level* (GSM8K ≠ PubMedQA ≠ QASPER optima). Nothing in Phase-1
establishes that, *within* one benchmark, different items want different
configurations. If GSM8K items are uniformly best served by one CoT config,
TACC reduces to the fixed choice and H1 fails.

- **Likelihood:** medium-high.
- **Impact:** project-defining.
- **Mitigation:** Gate-1 variance probe on GSM8K *train* before any
  controller training (cheap, uses existing evaluators).
- **Kill/redirect criterion:** if per-item utility-argmax agrees with the
  global argmax on ≥ ~95% of train items, instance-level adaptation is
  pointless within-task. Redirect: TACC becomes *task-level* conditioning
  (domain/features → config), evaluated cross-benchmark — still a valid,
  Phase-1-consistent study, and the within-task null is reported.

## R2 — Noisy supervision labels

Labels are per-item utility argmax over configs, from bounded train
subsets. Phase-1 CIs (±5pp at n=300) imply label noise at small n.

- **Mitigation:** label matrix uses as many train items as the budget
  allows; ties and near-ties (within CI) collapse into a
  "no-preference" class the controller may select without penalty;
  sensitivity to λ reported.

## R3 — Controller overhead exceeds savings

An encoder + policy that costs more than the tokens it saves is a negative
result. F2 showed the cheapest adequate config uses 67k total tokens per
300 items — margins are thin.

- **Mitigation:** controller must be orders of magnitude cheaper than the
  backbone call (small frozen encoder, CPU OK); overhead reported in every
  cost table; B-min (B1) is the cost floor to beat jointly, not just on
  accuracy.

## R4 — Learning the task ID, not task characteristics

A controller that keys on domain tags only re-learns Phase-1's
per-task argmax — which Phase-1 already showed fails to generalize.

- **Mitigation:** B-tag baseline must be beaten on *transfer* sets
  (SVAMP/MATH), where tag rules from GSM8K don't apply; ablation with
  domain tag removed from features.

## R5 — Novelty positioning vs. LLM routing literature

TACC is conceptually adjacent to **LLM routing / cascading**
(RouteLLM, FrugalGPT, hybrid model routing) and to adaptive computation
(mixture-of-experts at the scaffold level). A reviewer may read TACC as
"routing, but between prompts."

- **Mitigation (required before Gate-2):** a focused related-work audit on
  routing/cascading/adaptive-inference work; position precisely: existing
  routers choose *which model*; TACC conditions *how one frozen model is
  scaffolded* (reasoning/memory/context), and the contribution is the
  audited transfer/cost analysis, not the routing idea. If the audit finds
  an existing task-conditioned *scaffold* router with transfer evaluation,
  this direction must be re-scoped with the Planner — flag it, do not
  paper over it.

## R6 — Reward hacking / degenerate policies

Utility with λ may collapse the controller to always choosing the cheapest
config (all-direct) or the highest-accuracy one (all-B2), i.e. a constant
policy wearing a controller's clothes.

- **Mitigation:** selection-distribution reporting is mandatory; a constant
  policy is automatically compared to its fixed equivalent and must win on
  utility to count as adaptive; λ sensitivity sweep on train only.

## R7 — Scope creep (process risk)

The direction could drift into RL training, new substrates, or NAS — all
explicitly out of scope.

- **Mitigation:** configuration space frozen to Phase-1-validated configs;
  no new substrates; any new benchmark requires a new pre-inference lock;
  GPU envelope ≤ 5 GPU·h total; the frozen V1/V2 paper artifacts remain
  untouched.

## R8 — Reproducibility burden

A learned controller adds trainable state to a previously fully-frozen
pipeline.

- **Mitigation:** controller weights, label matrix, λ, seeds, and config
  set committed as one lock before Gate-3; the F2 forensic verifier is
  extended (read-only) to cover the new artifacts; CPU tests for feature
  extraction and policy determinism.

---

## Summary risk matrix

| Risk | Likelihood | Impact | Gate that detects it |
|---|---|---|---|
| R1 no within-task variance | med-high | project-defining | Gate 1 (cheap probe) |
| R2 noisy labels | medium | medium | Gate 2 (CI collapse rule) |
| R3 overhead > savings | medium | medium | Gate 3 (cost tables) |
| R4 task-ID learning | medium | high | Gate 3 (transfer sets) |
| R5 novelty vs routing | medium | high | pre-Gate-2 lit audit |
| R6 degenerate policy | medium | medium | Gate 3 (selection dist.) |
| R7 scope creep | low-med | process | standing rule |
| R8 reproducibility | low | medium | Gate 2 lock + verifier |

**Recommended next action:** Planner review of the three documents, then
the pre-Gate-2 routing-literature audit (R5) and the Gate-1 variance probe
(R1) — in that order, both cheap, both capable of redirecting the project
before any serious compute is spent.
