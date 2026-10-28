# Kimi Executor Prompt — R8 Document-Only Repair for NeuroEvoScientist

Role: Executor. GPT Planner owns approval. Repository: https://github.com/yujian777555/NeuroEvoScientist.

Read first:
- `planner/phase2_planner_review_r8.md`
- `planner/phase2_r7_method_research.md`
- `planner/r7_evidence_summary.json`
- `planner/phase2_pilot_planner_decision_r6.md`
- `phase2/pilot_r1/analysis/final_stats.json`
- `phase2/pilot_r1/results/stage1/run_manifest.json`
- current `status.json`

## Task
Produce `planner/phase2_r7_method_research_v2.md` correcting the estimator mismatch and the research design. This is document-only work.

### Mandatory statistical correction
Pilot R1 evaluates all five configurations for every evaluated item. That is full-information per-item action outcome data. The current RCDR formula's logged-action inverse-propensity residual does not match this data-collection design.

Choose the full-information setting unless you can establish from the actual committed manifests and records that only one action's outcome was observed per item. Do not guess.

For full-information policy learning:
- define per-item utilities and pairwise action differences;
- fit policy models only on FIT, tune only on TUNE;
- use nested selection/cross-fitting where appropriate to avoid in-sample policy evaluation;
- evaluate the frozen policy on a new untouched confirmation set using direct paired per-item outcomes;
- do not call this doubly robust;
- use a predeclared confidence rule and clear multiplicity handling;
- report accuracy, prompt/completion tokens, controller overhead and offline analysis cost separately.

If you instead propose a genuine partial-feedback design, explicitly define the randomized logging policy, known action propensities, positivity/support conditions, observed feedback protocol, estimator, and added data/compute cost. Do not authorize or execute that design.

### Other required corrections
1. Describe the hindsight oracle 0.8207188 only as an optimistic in-sample upper bound; it is not statistical significance or evidence of feature-predictable gains.
2. Separate action heterogeneity, feature predictability, and out-of-sample policy superiority as three distinct hypotheses.
3. Rework the SHUFFLE/negative-control plan: state the unconditional denominator, F0-NO-GO handling, and what the conditional mid-rank means. Do not discard invalid/NO-GO runs silently or blindly inherit an irrelevant gate.
4. Re-audit closest work for full-information contextual policy learning, pairwise utility/ranking, safe policy improvement, LCB selection, selective prediction, conformal routing, and LLM scaffold routing. Keep novelty `NOVELTY_UNRESOLVED` unless evidence supports a precise distinction.
5. Keep at most three method candidates. Rank them with reasons and explicit falsification criteria.
6. Do not include EC in the primary method unless the combinatorial-search bottleneck and equal-budget advantage are empirically justified. No experiment is permitted now, so EC necessity remains unproven.
7. Provide a pre-registration draft only. A new untouched confirmation set requires separate approval; do not reuse LEVAL and do not access MATH-500.

## Hard boundaries
- No CPU preflight or benchmarks.
- No dataset access, downloading, ID inspection, lock creation, or MATH-500 access.
- No model fitting, training, inference, API calls, GPU use, or permutation analysis.
- Do not modify Pilot R1 results, logs, lock files, paper, V1/V2 artifacts, or historical results.
- Do not change thresholds or run any new experiment.
- Do not claim tests were run unless actually run. This round should require only static document checks.
- Do not use `git reset --hard` or discard concurrent commits.

## Delivery
- Add `planner/phase2_r7_method_research_v2.md`.
- Update only `phase2_planning` in `status.json`.
- Preserve the old R7 document as history.
- Run document-only consistency checks, `git diff --check`, JSON parse, and verify no protected paths changed.
- Commit and push; verify `HEAD == origin/main` and worktree clean.
- Report exact commit SHA, files changed, checks actually run, and resource use.
- Stop for Planner R9 review.

Final state string:
`R8_DOCUMENT_REPAIR_COMPLETE — WAITING FOR PLANNER R9 REVIEW`
