# Kimi Code Prompt — R9 Document-Only Repair After Planner Review

Repository: https://github.com/yujian777555/NeuroEvoScientist
Role: Executor. GPT Planner retains approval authority.

Read:
- `planner/phase2_planner_review_r9.md`
- `planner/phase2_r7_method_research_v2.md`
- `planner/phase2_pilot_planner_decision_r6.md`
- `plans/phase2_g1_revised_protocol.md`
- current `status.json`

## Goal

Create `planner/phase2_r7_method_research_v3.md` as a document-only correction. Preserve R7/R8 history; do not overwrite them. Update only the `phase2_planning` object in `status.json`.

## Mandatory repairs

1. **TUNE/LCB validity:** TUNE currently selects features/thresholds and supplies the bootstrap bounds used to activate the policy. Do not describe those bounds as valid post-selection confidence guarantees. Preferred: treat TUNE as selection only and reserve all confirmatory inference for the frozen policy on a new untouched confirmation set. If proposing a separate calibration/gate split or nested cross-fitting, define it completely and acknowledge power costs. Distinguish global policy activation from per-question action-level uncertainty gating.
2. **Margin/confidence rule:** Resolve `delta=0.01` at TUNE versus primary confirmation CI lower bound >0. State whether delta is a practical effect margin or only a selection heuristic. Define one-sided/two-sided confidence levels and exact bootstrap quantile convention. Align the primary hypothesis and stop rule.
3. **Full-information terminology:** Remove unsupported off-policy “support failure” and effective-sample-size requirements from direct unweighted paired evaluation. If OOD/covariate support is intended, define it as a separate diagnostic, not propensity positivity.
4. **FCC conformal correctness:** Raw scores `s_i(a)=-G_i(a)` yield a marginal gain quantile, not per-instance routing. Either derive a valid conditional gain lower bound using a FIT-trained `Ghat_a(x)`, calibration residuals, exact sign/quantile, multiple-action coverage, exchangeability assumptions and shift limits—or drop FCC.
5. **Fallback naming:** B0 has lower total token consumption than B1 in R1. Call B1 a utility fallback/baseline, not a minimum-cost floor. Report B0 as a cheaper but low-utility option.
6. **RRC runtime signal:** Ground-truth wrongness is not known at inference time. Define a pre-action/verifiable failure signal and its costs without leakage, or drop RRC. Dropping RRC is acceptable.
7. **Data roles:** Preserve the locked protocol: BANK is exemplar content only; FIT fits/selects model class; TUNE has only predeclared tuning duties; opened LEVAL cannot be reused. Do not use BANK as labelled fitting/calibration data.
8. **Inference and resampling:** Predeclare the paired bootstrap unit (item vs source/duplicate cluster) based on the approved dataset's structure; do not inspect new IDs now. Define H2 near-tie threshold and wrong-action metric in advance. Define non-duplicative secondary controls and Holm family.
9. **Novelty:** Keep `NOVELTY_UNRESOLVED`. No claim of a new algorithm is allowed without a precise mechanism distinction. At most two candidates; FIDL-only is acceptable.
10. **No forced EC:** Keep EC out unless a real combinatorial bottleneck and equal-budget advantage are evidenced. No experiment is authorized now.

## Hard boundaries

- No GPU, inference, training, fitting, API calls, CPU preflight, benchmarks, permutation analysis, or dataset access.
- Do not access MATH-500.
- Do not reuse opened LEVAL for selection, calibration, or confirmation.
- Do not create/modify data locks.
- Do not modify R1 results, logs, papers, lock files, or historical artifacts.
- Do not claim full tests were run. Only static document checks are permitted.

## Delivery

- Add `planner/phase2_r7_method_research_v3.md`.
- Update only `phase2_planning` in `status.json`.
- Run document consistency checks, JSON parse, `git diff --check`, protected-path diff inspection.
- Commit and push, verify `HEAD == origin/main` and clean worktree.
- Report exact SHAs, files changed, checks actually run, and actual resource use.
- Stop for Planner R10 review.

Final state:
`R9_DOCUMENT_REPAIR_COMPLETE — WAITING FOR PLANNER R10 REVIEW`
