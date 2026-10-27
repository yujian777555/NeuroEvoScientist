# Planner R6 Decision — Phase-2 Pilot R1

Date: 2026-10-27
Repository: https://github.com/yujian777555/NeuroEvoScientist
Pilot result commit: `6150532d0b7be5a4172e452699d45071128b96ea`
Pilot status commit: `c2aeea5fb2132043c96b8b9f9f688eeac647f10e`
Reviewed remote main tree at start: `c2aeea5fb2132043c96b8b9f9f688eeac647f10e`

## Decision

**NO-GO for further experiments on the current TACC/GBT-F1 controller and current hypothesis. STOP at Pilot R1.**

The reported `INCONCLUSIVE_NULL` status is correct and must remain unchanged. The pilot does not establish controller superiority or a validated learnability result. Do not run a larger version of the same experiment, do not add SHUFFLE replicates post hoc, and do not tune the current controller against the already-opened LEVAL set.

This is a static Planner review of the actual GitHub result report, final_stats.json, frozen_selection.json, derived manifest, stage-1 manifest, raw-result file inventory, inference logs, and the independent recomputation log. The report's 219-test and raw-record verification results are recorded as Executor-reported checks; this review did not rerun the VM tests or independently recompute every raw row.

## Evidence supporting NO-GO

### 1. All three confirmatory utility contrasts fail

| Contrast | Candidate utility difference | 95% paired bootstrap CI | Gate |
|---|---:|---:|---|
| Candidate − BEST-FIXED (B2) | -0.0130702 | [-0.0562722, 0.0270257] | FAIL |
| Candidate − MAJORITY (B1) | -0.0091458 | [-0.0459168, 0.0275942] | FAIL |
| Candidate − SIMPLE-FEAT | -0.0066388 | [-0.0466694, 0.0331997] | FAIL |

Every interval spans zero, and every observed mean difference is negative. This is not proof of equivalence, but it provides no evidence of a positive utility advantage under the predeclared gate.

### 2. The candidate is strictly dominated by B1 on observed accuracy and total tokens

On the 300 LEVAL items:
- Candidate: 63.33% accuracy; 100,614 prompt + 60,727 completion = 161,341 total tokens.
- B1/MAJORITY: 64.00% accuracy; 24,804 prompt + 62,164 completion = 86,968 total tokens.

Thus the candidate has 0.67 percentage points lower accuracy and uses 74,373 more total tokens (about 85.5% more) than B1. B1 is better on both reported dimensions in this pilot. The candidate cannot be presented as a cost-efficiency improvement over B1.

Against B2, the candidate uses about 40.1% fewer total tokens but loses 1.67 accuracy points and has lower utility. Against SIMPLE-FEAT, the candidate saves only 835 total tokens over 300 items (~0.5%) while losing 0.67 accuracy points and utility. These trade-offs do not rescue the confirmatory claim.

### 3. SHUFFLE is inconclusive under the frozen rule

- Total permutation replicates: 1,000.
- F0-NO-GO: 749 (74.9%).
- Valid F1-scored replicates: 251 (25.1%).
- Invalid/error replicates: 0.
- Required valid replicates: at least 950.
- Conditional mid-rank percentile: 0.378486.

Because 251 < 950, the SHUFFLE gate is `INCONCLUSIVE_NULL`. Do not reinterpret it as a pass or as a definitive null rejection. RANDOM passing does not compensate for the failed fixed-baseline gates or the inconclusive SHUFFLE gate.

### 4. Resource accounting

- GPU inference wall time: 787.84 s.
- NVML-active integral reported: 329.04 s = 0.0914003 aggregate GPU-hours.
- CPU permutation analysis: 13,692.45 s wall time; 523,065.42 CPU-seconds (~145.30 CPU-hours).

GPU use was within the 1.0 GPU-hour ceiling. The remaining GPU allowance is not a reason to spend more compute on an unsupported hypothesis.

## Reproducibility notes to preserve

- The result report says 5,000 generations: 3,500 Stage-1 evaluations plus 1,500 LEVAL evaluations (five fixed configurations × 700 FIT/TUNE items plus five × 300 LEVAL items).
- The stage-1 manifest reports the frozen F1 candidate, 300 LEVAL records per fixed configuration, and the NVML active-time integral.
- The first inference attempts have logged failures (including a missing output directory and a stage-input length mismatch) before the later `inference_resume2.log` completed. Preserve these logs and describe the recovery honestly; do not delete them.
- The inference logs contain LogisticRegression `ConvergenceWarning` messages at max_iter=1000 during the candidate model-selection grid. The selected model was GBT, but these warnings should be documented as a model-selection limitation. They do not authorize changing the grid or reusing LEVAL to rerun selection.
- The independent recomputation log reports matching summary statistics and gate outcomes. This review has not independently rerun the 219-test suite or all row-level recomputations.

## Authorized next steps

1. Freeze Pilot R1 artifacts and status as `INCONCLUSIVE_NULL`.
2. Do not rerun inference, add permutations, alter thresholds, change the model grid, or reuse LEVAL for another candidate.
3. A materially different method may be considered only as a new research proposal, with a fresh novelty audit, new untouched confirmation set, and a pre-specified protocol before any new inference.
4. Do not claim that DEFLECT or MEMROUTE novelty is established. Do not update the paper with claims of controller superiority.
5. No further CPU or GPU work is authorized by this decision.

## Final status

**PILOT R1 REVIEWED — NO-GO FOR CURRENT TACC CONTROLLER — FREEZE RESULTS — NO FURTHER EXPERIMENT AUTHORIZED.**
