# Kimi Code — Phase-2 R4 document-only protocol repair

Repository: https://github.com/yujian777555/NeuroEvoScientist
Branch: main
Role: Executor. GPT is Planner.

## Authority — read first

Read the actual current remote versions of:
1. `plans/phase2_planner_review_r4.md`
2. `plans/phase2_g1_revised_protocol.md` (v4)
3. `plans/phase2_g1_preflight_decision.md` (v4)
4. `plans/phase2_r5_related_work_gap.md`
5. `plans/phase2_r5_overlap_matrix.csv`
6. `status.json`

R4 verdict: **CONDITIONAL HOLD**. R3 repairs are substantial, but the protocol is not ready for CPU preflight. The only authorization this round is document/status repair. GPU authorization remains 0.

Before editing, fetch the current remote `main`, verify its HEAD and working tree, and inspect diffs. Do not assume the reported SHA is still HEAD or discard any commit.

## Required R4 repairs

### R4-A — unify model outputs, targets, selection metric, and hyperparameter grids

The current grid mixes ridge regression on Δu, logistic classification over best-config labels, and a GBT whose target/objective is unspecified, while selecting all models by Δu-prediction R². The α grid is not meaningful for every model class.

Define a single coherent policy contract. Recommended option:
- Every candidate class must produce a deterministic per-item configuration/action choice.
- Ridge may predict per-action Δu values and choose the max.
- Logistic may predict best-config action probabilities and choose the max.
- If retaining GBT, state the exact estimator (classifier or regressor), target, and all fixed/hyperparameters.
- Select among candidate classes using one common FIT cross-validation score: mean realized held-out utility of the action each model chooses, calculated from the already-available per-config outcomes. Do not use Δu R² to select a classifier that does not predict Δu.
- Define class-specific hyperparameter grids (e.g. ridge α; logistic C; GBT parameters) and deterministic tie-breaks. Do not apply a nonexistent α to GBT.
- Define the final fitting order explicitly: FIT-only cross-validation selects class/hyperparameters; fit separate FIT-only candidate models for each predeclared feature set so TUNE can compare F0/F1; TUNE selects the feature set and thresholds only; refit the frozen selected policy on FIT only using the selected feature set; then freeze it before any LEVAL access. TUNE labels must not be added to the fitting set unless the protocol explicitly redesigns and freezes that rule before LEVAL.
- Define exact action/config tie-breaks and how a model failure is handled.

If you choose a different coherent design, explain why it is statistically sound and keep every choice pre-specified. No model implementation is authorized in this round.

### R4-B — resolve SIMPLE-FEAT identity

The current SIMPLE-FEAT is the same pipeline restricted to F0, but the candidate may also choose F0. In that case, candidate and comparator are identical, so a strict positive-CI gate is impossible.

Recommended conservative rule:
- If TUNE selects F0, trigger a pre-specified NO-GO/early-stop **before any LEVAL outputs are generated or inspected**; report that the candidate cannot pass the required distinct-baseline gate and do not open LEVAL.
- If TUNE selects F1, proceed with the frozen F1 candidate and compare it against the locked F0 SIMPLE-FEAT baseline on LEVAL.

You may instead define a genuinely distinct simple-feature baseline, but fully specify it and justify its fairness. Do not change it after LEVAL. Make the early-stop branch and its status/result terminology explicit.

### R4-C — make SHUFFLE replay the adaptive pipeline fairly

The current SHUFFLE shuffles FIT labels but retains original TUNE-based feature/threshold selection, giving the candidate and null controls different selection opportunities.

Specify the null procedure so every replicate replays the same adaptive selection pipeline:
- break the association between features and per-item target/outcome vectors in FIT and TUNE separately using predeclared permutation seeds;
- re-run FIT cross-validation/model-class and hyperparameter selection;
- re-fit the candidate on permuted FIT targets;
- re-run TUNE feature-set and threshold selection on permuted TUNE targets;
- score the resulting frozen policy on the same locked LEVAL item outcomes/completions, which remain untouched for fitting/tuning.
Use already-frozen per-config LLM outputs for these CPU-side permutations; do not issue new model calls for each shuffle.
- State exactly what is permuted for regression targets versus best-config labels, how the within-item configuration outcomes remain paired, and how ties are handled.
- Keep 1,000 shuffles, deterministic seed stream, and the pre-specified mid-rank rule unless a justified alternative is approved before LEVAL.
- State a CPU-side workload/timeout expectation for the 1,000 refits. This does not grant permission to run CPU preflight now.

If you propose a narrower conditional null instead, specify its exact null hypothesis and explain why it is fair given TUNE adaptation. Planner R5 must review it.

### R4-D — make endpoint hierarchy consistent

Section 3 uses utility at λ=0.1 as the primary D2 pass/fail endpoint, while Section 4 says raw accuracy/tokens/Pareto are primary and utility is secondary.

For this learnability pilot, recommended resolution:
- declare utility at locked λ=0.1 as the primary D2 pass/fail endpoint;
- report raw accuracy, prompt tokens, completion tokens, and the accuracy-token Pareto as mandatory separate outcomes, not collapsed into utility;
- remove the contradictory sentence calling utility merely secondary for the D2 gate;
- retain that λ=0.1 is exploratory-informed, not a deployment-optimal price; include the predeclared sensitivity analysis without choosing λ from LEVAL.

If you instead retain raw accuracy/Pareto as the primary endpoint, redesign the pass/fail gate consistently before LEVAL and explain the alternative. No post-hoc endpoint selection.

### R4-E — remove bias from missing-output handling

Do not drop a difficult LEVAL item from every contrast simply because one configuration is missing. Define the rule before any inference.

Preferred conservative rule: if any required config output is missing/invalid for any LEVAL item, mark the confirmatory run INCOMPLETE/INVALID, report the missing count, and do not declare D2 PASS; no selective retries or item deletion. If using a scoring penalty instead, specify correctness and token-cost accounting exactly. Apply the same failure policy to all baselines.

### R4-F — finish canonical ID/hash specification

Apply a single normalization contract to both source-provided IDs and fallback question-derived IDs:
- canonical string conversion for source IDs;
- Unicode NFC;
- strip leading/trailing whitespace and collapse internal whitespace runs;
- empty or duplicate normalized IDs cause preflight failure;
- UTF-8 byte encoding and exact SHA-256 input construction;
- deterministic sort by (digest, normalized ID) to resolve any equal digest keys.
Specify the fallback ID construction and ensure the partition and subset namespaces cannot collide.

Keep exact partition counts and planned subset counts unchanged unless the R4 review justifies a documented alternative. Do not create actual IDs, hashes, locks, or load data in this round.

### R4-G — fully define bootstrap CI

Specify the bootstrap interval construction (e.g. two-sided percentile 95% CI using the 2.5th and 97.5th percentiles, a named quantile interpolation convention, 10,000 item-level paired resamples, locked seed). Use the same sampled item indices across the configurations in each replicate. Apply consistently to all bootstrap contrasts and state that lower bound > 0 is the pass rule.

### R4-H — status provenance and pointers

Update only `status.json.phase2_planning`. Correct stale fields:
- `planner_review` / `executor_prompt` must point to the current R4 review/prompt, not R2.
- Update the `documents` list and `open_items` / `authorized_now` so they describe the current R4 repair and subsequent Planner R5 review.
- Record the actual remote HEAD observed at start of this round, the R4 substantive deliverable commit, and any later status-only commit separately.
- Do not self-reference the final status-update commit.
- Keep `gpu_authorized: 0`, `implementation_authorized: false`, `pilot_status: NOT AUTHORIZED / NOT EXECUTED`.
- Preserve every unrelated `status.json` field.

## Files permitted to change

Only:
1. `plans/phase2_g1_revised_protocol.md`
2. `plans/phase2_g1_preflight_decision.md`
3. `status.json` (only `phase2_planning`)

Do not edit R4 review/prompt after creation, R5 literature documents, frozen V1/V2 papers/PDFs/supplements, or historical F1/F2 results.

## Hard prohibitions

This is document-only:
- no GPU;
- no inference or training;
- no controller implementation;
- no dataset download/loading;
- no CPU preflight;
- no actual partition/subset locks;
- no MATH-500 access;
- no new experiment;
- no novelty-clearance claims.

## Commit, verify, stop

1. Inspect diffs and check all R4-A…R4-H items against the actual documents.
2. Run only appropriate document-level checks; report exactly what ran. Do not claim tests were rerun unless they were.
3. Commit and push the two document updates.
4. Verify remote `main` and exact SHA.
5. Update `status.json.phase2_planning` in a separate status-only commit, recording the substantive deliverable commit and pre-status-update HEAD accurately.
6. Verify final remote HEAD, file contents, and working-tree state if available.
7. Report all unresolved issues honestly.

Final status:
**R4 DOCUMENT REPAIRS COMPLETE — STOP AND WAIT FOR PLANNER R5 REVIEW**

After pushing, stop. Do not begin CPU preflight, data access, or GPU Pilot without separate explicit authorization.
