# Planner R8 Review — R7 Method Research

Date: 2026-10-28
Repository: https://github.com/yujian777555/NeuroEvoScientist
R7 research commit: `400b5a2295bc1fd85b8fb14cfbeaa5ea03298b10`
R7 status commit: `bc37d161261b7f1d2c6e1699daf372dbf8e0655c`
Reviewed artifacts: `planner/phase2_r7_method_research.md`, `planner/r7_evidence_summary.json`, `status.json`, and R6 decision.

## Verdict

**R7 is accepted as a useful failure analysis, but RCDR is NOT approved as currently specified. Request a narrow document-only R8 correction before deciding whether any new method merits preflight.**

No experiment, CPU preflight, data access, model fitting, API call, or GPU work is authorized. The current TACC/GBT-F1 Pilot R1 remains frozen as `INCONCLUSIVE_NULL`; R6's NO-GO remains authoritative.

## What R7 gets right

1. It accurately preserves the negative Pilot R1 result and does not claim a validated controller advantage.
2. The code-path reconstruction is concrete: F0/F1 features, direct per-action utility-difference regressors, hard argmax with delta/shift fallback, and the limited interpretation of ShiftDetector.
3. It distinguishes hindsight oracle headroom from evidence that a policy can predict the best action.
4. It correctly concludes that EC is not currently justified. EC-RuleSearch is conditional and ranked last, rather than added to satisfy a label.
5. It labels RCDR, SCC, and EC-RuleSearch novelty as unresolved and proposes no execution this round.

## Blocking technical issue: the proposed DR estimator does not match the available feedback

The R1 dataset evaluates all five configurations on the same questions: 3,500 Stage-1 generations plus 1,500 LEVAL generations, with each of the five configurations represented for each evaluated item. Therefore, for those benchmark items, the observed data are **full-information per-item action outcomes**, not a single logged action and its reward.

The proposed RCDR formula uses a logged action (A_i), a logging propensity (h(A_i\mid x_i)), and an inverse-propensity residual. That construction is intended for partial-feedback/off-policy data. In the current full-information design, all (U_i(a)) are observed, so the propensity-weighted residual is unnecessary and risks solving the wrong statistical problem.

For a new method, the natural evaluation on an untouched set is direct paired full-information policy evaluation:
`V(π)-V(π0) = n^{-1} Σ_i [U_i(π(x_i))-U_i(π0(x_i))]`
for deterministic policies, with a paired item-level uncertainty interval. For stochastic policies, average the observed per-item utility over the policy's action distribution. Policy fitting still requires strict train/tune/confirmation separation or cross-fitting to control overfitting, but this does not make the evaluation doubly robust.

R8 must choose and justify one of two distinct settings:
- **Full-information contextual policy learning** (fits the current experimental design): predict per-action utilities or pairwise differences; use cross-fitting and conservative baseline-relative selection; evaluate on a fresh untouched set using observed paired outcomes.
- **Partial-feedback/off-policy learning**: change the data-collection design to observe only selected actions with a known randomized logging policy and valid propensities. This would be a different and more expensive study, requiring separate approval.

Do not call a direct supervised utility model “doubly robust.” Do not introduce inverse propensity weights without a genuine logging policy and a clear partial-feedback estimand.

## Additional required corrections

### R8-A — Oracle language
The 0.8207188 hindsight oracle is an optimistic in-sample upper bound computed using each item's observed outcomes. It shows potential action-space headroom, but is not a statistically significant gain, not a deployable policy, and not evidence that question features can predict that gain. Replace any wording like “significantly higher” with “numerically much higher hindsight upper bound” unless a valid inferential comparison is supplied.

### R8-B — Separate three claims
Distinguish:
1. action outcomes vary across items;
2. action differences are predictable from pre-action features;
3. a learned policy beats the strongest fixed baseline on fresh data.
The pilot supports the first claim and gives a large hindsight upper bound, but does not establish the second or third.

### R8-C — Rewrite the primary estimator and evaluation plan
For the full-information setting, define:
- exactly how per-action utility differences are constructed;
- the policy-training loss and candidate class;
- nested FIT/TUNE selection without LEVAL reuse;
- direct paired utility difference on a new untouched confirmation set;
- a predeclared one-sided or two-sided confidence rule and multiplicity treatment;
- how uncertainty-aware abstention is calibrated without claiming distribution-free guarantees that have not been proven;
- a clear compute/cost metric that separately reports generation tokens, controller inference/training cost, and offline analysis cost.

The primary gate should be scientifically interpretable and should not blindly inherit the old SHUFFLE gate if that gate's 25.1% valid rate is unrelated to the new estimand. If shuffled-label controls remain, specify the complete selection pipeline, the unconditional denominator, the treatment of F0-NO-GO, and the interpretation of conditional statistics. Do not quietly drop invalid replicates.

### R8-D — Novelty and closest prior work
RCDR's combination remains `NOVELTY_UNRESOLVED`. After fixing the estimator mismatch, perform a targeted mechanism-level comparison with:
- direct-method contextual policy learning with full feedback;
- pairwise utility/ranking models;
- safe policy improvement and lower-confidence-bound selection;
- selective prediction / learning-to-defer;
- conformal threshold routing;
- cost-aware LLM strategy/scaffold routing.

State what exact mechanism remains beyond those prior methods. If the contribution is only “apply DR/LCB to a new LLM scaffold dataset,” reject the novelty claim.

### R8-E — No EC by default
Keep EC out of the primary candidate unless evidence establishes a combinatorial search bottleneck and an equal-real-evaluation-budget advantage over exhaustive search (when feasible), random search, and local greedy search. Do not add EC to make the work look aligned with the lab label.

### R8-F — Data and authorization
- Do not reuse the opened LEVAL set for candidate selection, calibration, or independent confirmation.
- Do not access MATH-500.
- A fresh confirmation set and its exact IDs, revision, hashes, overlap checks, and contamination caveats require separate Planner review.
- No CPU preflight, dataset access, model fitting, API calls, or GPU run is authorized by this review.

## Required R8 deliverable

Create `planner/phase2_r7_method_research_v2.md` and update only the Phase-2 planning section in `status.json`.

The revised proposal must:
1. retain the valid R7 failure diagnosis;
2. correct the full-information versus partial-feedback mismatch;
3. reformulate RCDR or replace it with a statistically appropriate full-information candidate;
4. retain at most three candidates and explicitly rank them;
5. update the primary estimand, uncertainty rule, baselines, and data separation;
6. state novelty as unresolved unless the closest-work comparison supports a narrower claim;
7. provide a pre-registration draft only—not run it;
8. leave Pilot R1 artifacts, the paper, frozen results, and lock files unchanged.

Commit and push the document-only revision, verify remote synchronization and clean worktree, report actual checks without claiming tests that were not run, then stop for Planner R9 review.

## Final decision

**R7 DIAGNOSTIC ACCEPTED — RCDR FORMULATION REQUEST CHANGES — NO EXPERIMENT AUTHORIZED.**
