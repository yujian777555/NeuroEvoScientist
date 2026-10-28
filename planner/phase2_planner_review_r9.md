# Planner R9 Review — R8 Full-Information Method Proposal

Date: 2026-10-28
Repository: https://github.com/yujian777555/NeuroEvoScientist
R8 document commit: `a16f5ab707160d02fdb9e2e1c03a3cbb202a0a72`
R8 status commit: `40532946c522f8f97716743013b6b7c922b04eb3`
Reviewed: `planner/phase2_r7_method_research_v2.md`, `status.json`, the frozen R6 decision, and the G1 partition-role protocol.

## Verdict

**R8 is a meaningful statistical repair, but the method proposal needs another document-only revision. FIDL is the only candidate worth clarifying; it is not yet approved for implementation or experiment. FCC is currently mis-specified as a per-question conformal router. RRC has an unresolved runtime-observability gap and may be dropped.**

R6 remains authoritative: Pilot R1 is frozen as `INCONCLUSIVE_NULL`; no inference, CPU preflight, fitting, data access, or experiment is authorized.

## What R8 gets right

1. It correctly replaces the mismatched inverse-propensity/DR formulation with direct full-information paired evaluation.
2. It separates H1 action heterogeneity, H2 feature predictability, and H3 fresh-set policy superiority.
3. It accurately treats the 0.8207188 hindsight value as an optimistic in-sample upper bound, not a deployable result.
4. It reports SHUFFLE's unconditional counts and conditional interpretation without claiming success.
5. It does not force EC into a small supervised policy-learning problem.
6. It keeps all candidates' novelty unresolved and requests no execution.

## Blocking issues for R9

### R9-A — TUNE selection and confidence-bound semantics

The draft uses TUNE to select the feature set and thresholds, and also computes paired bootstrap lower confidence bounds on TUNE to decide whether to activate the candidate. Because the same TUNE outcomes are used for selection and for the bound, the nominal interval is not a valid post-selection confidence guarantee without additional separation or correction.

R9 must choose one clear interpretation:
- **Preferred simple design:** TUNE is model/threshold selection only. Its LCB is explicitly a selection heuristic, not a calibrated inferential guarantee. The only confirmatory inference is the frozen policy's paired comparison on the new untouched confirmation set.
- **Alternative:** define a separate, pre-specified gate/calibration split or nested cross-fitting procedure that does not reuse the same observations for threshold selection and the claimed bound. Explain the power cost with the small TUNE sample.

Also distinguish a **global policy-level gate** (activate the entire policy or fall back to B1) from a **per-item confidence gate** (choose an action only when its item-level predicted gain bound clears a threshold). The current text mixes the idea of per-question routing with a TUNE-level mean policy bound. State which mechanism FIDL actually proposes. Do not claim per-item wrong-action reduction unless an inference-time per-item uncertainty mechanism is defined and testable.

### R9-B — Primary margin and confidence level are inconsistent/underspecified

The TUNE gate requires both one-sided lower bounds to exceed `delta=0.01`, but the primary confirmation hypothesis only requires the candidate-minus-BEST-FIXED CI lower endpoint to exceed zero. Clarify whether 0.01 is:
- a practical minimum-effect margin that must also be met in confirmation, or
- only an internal TUNE selection threshold, with confirmation testing superiority over zero.

Give the rationale for the margin in utility units and define the exact one-sided confidence level/quantile. “95% CI lower bound” and “one-sided 95% LCB” are not interchangeable labels unless the quantile convention is specified. The primary endpoint, effect margin, and stop rule must agree.

### R9-C — Remove leftover off-policy terminology from full-information evaluation

The draft says “support failure” is a FIDL stop condition and that direct policy-difference confidence bounds include “support, effective sample size, and interval width.” In an unweighted full-information paired evaluation where every action outcome is observed per item, action-propensity support and importance-weighted effective sample size are not automatically relevant.

Remove these terms unless a distinct, valid definition is supplied. If the intended concern is covariate extrapolation/OOD, define a feature-space support diagnostic separately, specify how it is frozen using FIT/TUNE, and make clear that it is a diagnostic rather than an off-policy positivity guarantee. Report actual sample size and interval width.

### R9-D — FCC formula does not currently define per-question conformal routing

The proposed score (s_i(a)=-G_i(a)) uses raw observed gains without a fitted conditional gain predictor. Its quantile describes the marginal distribution of per-item gains for an action; the rule (-q_a>delta) would accept or reject that action globally, not select a configuration based on the current question's features.

If FCC is retained, define a fitted predictor (hat G_a(x)) trained only on FIT and a calibration residual construction that yields a lower bound such as (hat G_a(x)-q_a), with the sign/quantile convention fully specified. Explain simultaneous coverage or multiplicity across actions, the exchangeability assumption, and what happens under shift. Do not call marginal action-level quantiles per-instance conformal guarantees. If this cannot be made rigorous and useful, retire FCC rather than keeping it as a nominal second candidate.

### R9-E — B1 is not the minimum-token “cost floor”

R1's B0 consumes fewer total tokens than B1, while B1 has much higher observed utility. B1 can be the predeclared **utility fallback/baseline**, but not the literal minimum-cost floor. Replace “B1 cost floor” with accurate terminology throughout, and separately report the lower-token B0 option and its accuracy/utility trade-off. Do not imply B1 is the cheapest configuration.

### R9-F — RRC lacks a defined inference-time recovery signal

RRC says to identify items where the current configuration fails and then escalate. Ground-truth correctness is generally unavailable at runtime. A residual wrong-set on labelled development data does not itself tell the deployed controller which unseen item's answer is wrong.

Either specify a pre-action/inference-time failure-risk or verifiable recovery signal, its cost, and how it is trained without leakage, or drop RRC. Given its Adaptive-Solver overlap and extra cumulative generation cost, dropping it is acceptable and may be preferable.

### R9-G — Data roles, resampling unit, and secondary hypotheses

- Preserve the locked G1 roles: `BANK` is exemplar-bank content only, not a general labelled fitting/calibration partition. `FIT` is for model selection/fitting; `TUNE` for the explicitly predeclared tuning role; opened `LEVAL` is not reusable. If the candidate does not use exemplars, it should not consume BANK labels.
- Predeclare the resampling unit for paired bootstrap: item-level only if items are defensibly independent; otherwise use the appropriate source/duplicate cluster. Do not inspect new dataset IDs to decide this before authorization.
- Define the “near-tie” subset and wrong-action metric in H2 before any new confirmation outcomes are accessed. Otherwise H2 remains exploratory.
- Clarify the exact secondary-comparison family and how the no-LCB, direct-GBT, and FIDL variants differ so the Holm family does not contain duplicate or ambiguous controls.
- Keep sample-size/power claims cautious; a proposed `n>=500` is not a power guarantee. A final sample size and dataset need separate approval.

## Required R9 deliverable

Create `planner/phase2_r7_method_research_v3.md` and update only `phase2_planning` in `status.json`.

The v3 document must:
1. preserve the valid R8 full-information correction and frozen R1 findings;
2. resolve R9-A through R9-G or explicitly drop the candidate that cannot be repaired;
3. retain no more than two candidates, and it is acceptable to retain only FIDL;
4. keep novelty `NOVELTY_UNRESOLVED` unless a mechanism-level distinction is substantiated;
5. provide a corrected pre-registration draft only, not execute it;
6. keep LEVAL sealed, do not access MATH-500, and require separate authorization for any fresh confirmation set;
7. leave all R1 results, logs, paper files, lock files, and historical artifacts unchanged.

Only static document checks are allowed. No web/API calls are required for this repair, no code implementation, no CPU preflight, no dataset access, no model fitting, and no GPU use.

After committing and pushing, verify `HEAD == origin/main` and a clean worktree. Report only checks actually performed and stop for Planner R10 review.

## Final decision

**R8 STATISTICAL REPAIR ACCEPTED — METHOD SPECIFICATION REQUEST CHANGES — NO EXPERIMENT AUTHORIZED.**
