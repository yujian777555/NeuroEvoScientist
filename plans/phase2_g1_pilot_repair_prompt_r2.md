# Kimi Code — Phase-2 R2.1 document-only repairs

Repository: https://github.com/yujian777555/NeuroEvoScientist
Branch: `main`
Role: Executor. GPT remains Planner.

## Authority — read before doing anything

Read in full:
1. `plans/phase2_planner_review_r2.md`
2. `plans/phase2_planner_review_r1.md`
3. `plans/phase2_g1_revised_protocol.md`
4. `plans/phase2_r5_related_work_gap.md`
5. `plans/phase2_r5_overlap_matrix.csv`
6. `plans/phase2_g1_preflight_decision.md`
7. `status.json`

R2 verdict: **R1 repairs substantially accepted, but G1 is NOT PILOT-READY. GPU authorization remains 0.**

## Required repairs

### A. Complete the D2 pass gate

The current gate only requires positive paired-CI improvement over best fixed and beating shuffled labels. It does not require beating random and simple feature baselines, as R1 required.

Pre-specify a frozen candidate policy and require a locked LEVAL evaluation against:
1. best fixed config selected only on FIT/TUNE;
2. shuffled-label control(s), with shuffle count and seeds fixed before LEVAL;
3. reasonable random policy;
4. majority/action-frequency policy when applicable;
5. a simple feature baseline, at minimum length/numeric-density-only.

Define each paired contrast, statistic, confidence interval, and gate. Keep the primary contrast explicit. Do not select the candidate, baseline, threshold, or random seed based on LEVAL. Define a valid hierarchical/intersection-union rule or other multiplicity handling. Reporting a baseline is not equivalent to beating it.

### B. Make the pilot sample plan deterministic and unambiguous

The full partition proportions are approximately BANK=2,989, FIT=1,868, TUNE=1,121, LEVAL=1,495. The pilot currently uses 800 FIT+TUNE targets plus 300 LEVAL targets without exact counts or a deterministic sample-selection rule.

- Specify exact counts. A proportional 800-item split would be 500 FIT + 300 TUNE; use this or justify an alternative.
- Specify stable ID normalization, fixed seed, exact sample-selection algorithm, and SHA-256 of each selected ID list once an explicitly authorized CPU preflight is permitted.
- Clarify that the 300 LEVAL items are a predetermined subset of the 1,495 LEVAL partition, selected and hash-locked before any model outputs are generated.
- Resolve the contradiction between “predictor fitting on FIT” and “cross-fitting inside FIT∪TUNE.” Write an ordered pipeline:
  1. FIT-only fitting and any cross-fitting;
  2. TUNE-only hyperparameter/threshold selection;
  3. best-fixed selection procedure using only allowed train-side outcomes;
  4. one-time LEVAL evaluation.
- No LEVAL-based refitting, threshold adjustment, candidate selection, or result-driven resampling.

For this document-only round, do NOT fetch/load the dataset or create actual partition locks. State that immutable lock artifacts remain a future CPU-preflight deliverable, not already completed.

### C. Correct the unsupported precision claim

Remove the unconditional claim that n=300 “gives” a ±2–3pp CI.

For paired binary accuracy near zero difference, an illustrative approximation is:
`95% half-width ≈ 1.96 × sqrt(q / 300)`,
where q is the paired discordance rate. Example planning scenarios: q=5% ≈ ±2.5pp; q=10% ≈ ±3.6pp; q=20% ≈ ±5.1pp; q=40% ≈ ±7.2pp. These are analytic illustrations, not observed data; utility CIs also depend on token-cost variance.

Use existing paired logs only if they are accessible without running new inference; label them planning-only and explain transfer limitations. Otherwise present a sensitivity table and call the pilot a learnability screen with uncertain power. Do not claim guaranteed detection.

### D. Reconcile budget accounting

No new benchmark or GPU run.

- Verify from existing records what the 55 s/100 item-config timing includes.
- Explicitly state whether bank construction, cache misses, and all five configs are included.
- Avoid double-counting overhead; distinguish wall-clock time from aggregate GPU-active time.
- Reassess whether 0.97 h expected use leaves adequate margin below a 1.0 GPU-hour hard cap. If not, propose a justified revised cap or sample size, but do not authorize it yourself.
- Keep all budgets estimates, not execution permissions.

### E. Fix utility algebra and terminology

Correct the algebra to:
`lambda × 1000 / 10000 = 0.1 × 0.1 = 0.01`.

Replace “pre-registered” and “Pre-registered D2 pass” with “pre-specified and commit-locked before LEVAL inference,” unless formal external preregistration exists. Remove stale `VAL` references where the new partition is `LEVAL`.

### F. Extend the conformal / decision-aware routing scan

Add rows and a mechanism-level comparison for:

1. **Fang & Nalisnick, “Learning to Defer with an Uncertain Rejector via Conformal Prediction,” TMLR 2026**  
   Project: https://yiziruifang.com/project/uncertain-defer/  
   OpenReview: https://openreview.net/forum?id=wrLiUpfk4s

2. **Tan, Rangwala & Maddix, “Threshold-Aware Conformal Routing,” arXiv:2610.02487 (2026)**  
   https://arxiv.org/abs/2610.02487

Explain the scope distinctions: model-versus-human deferral and conformal rejector uncertainty are not the same as single-frozen-LLM scaffold routing to a token-cost floor; surrogate-versus-simulator threshold routing is adjacent decision-aware routing, not a direct LLM collision. Do not claim direct collision without evidence. Mark full-text/appendix/code verification honestly; if only abstract/project-page evidence was inspected, label it as such.

Keep M1/M2 novelty as NOT CLEARED unless new evidence justifies otherwise.

### G. Correct status.json semantics

Update only `phase2_planning`:
- change `next_gate` to R2.1 document repairs followed by Planner R3 review;
- separate resolved R1 items from remaining blockers;
- update `g1_protocol` to BANK/FIT/TUNE/LEVAL;
- update current reviewed deliverable SHA and current remote HEAD;
- clarify `last_commit` means latest substantive Executor deliverable commit if that is the intended meaning. Do not claim it equals the commit containing the final status update when it does not.
- preserve `gpu_authorized: 0`, `implementation_authorized: false`, `pilot_status: NOT AUTHORIZED / NOT EXECUTED`.

## Files to update

- `plans/phase2_r5_related_work_gap.md`
- `plans/phase2_r5_overlap_matrix.csv`
- `plans/phase2_g1_revised_protocol.md`
- `plans/phase2_g1_preflight_decision.md`
- `status.json` (only `phase2_planning`)

Do not edit the frozen V1/V2 papers, PDFs, supplementary archives, or historical F1/F2 result artifacts.

## Hard prohibitions

This is document-only:
- 0 GPU;
- no model inference or training;
- no controller implementation;
- no dataset fetching/loading or actual partition-lock generation in this round;
- no MATH-500 access;
- no new experiments;
- no claims that novelty has been cleared.

## Commit and stop protocol

Commit and push the document repairs to `main`. Verify the latest remote commit and report the exact SHA, file diffs, and tests/checks run. Report the local working-tree state as observed, not assumed.

Then stop and wait for Planner R3. Do not begin CPU preflight or Pilot without separate explicit authorization.
