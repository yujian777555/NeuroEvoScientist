# Kimi Code — Phase-2 R3 document-only repair (prepare for Planner R4)

Repository: https://github.com/yujian777555/NeuroEvoScientist
Branch: main
Role: Executor. GPT is Planner.

## Authority: read these first
1. `plans/phase2_planner_review_r3.md`
2. `plans/phase2_g1_revised_protocol.md` (v3)
3. `plans/phase2_g1_preflight_decision.md` (v3)
4. `plans/phase2_r5_related_work_gap.md`
5. `plans/phase2_r5_overlap_matrix.csv`
6. `status.json`

R3 verdict: R2.1 substantially accepted, but G1 is not ready for CPU preflight. This round is document/status only. GPU authorization = 0.

## Required fixes

### 1. Make every D2 control rule operational
The candidate must beat BEST-FIXED, SHUFFLE, RANDOM, MAJORITY, and SIMPLE-FEAT. Explicitly define the statistical rule for each control:
- BEST-FIXED: paired per-item utility difference, 10,000-resample paired bootstrap 95% CI, lower bound > 0; exact McNemar for binary accuracy remains secondary.
- SHUFFLE and RANDOM: define how each of the 1,000 null policies is trained/generated and evaluated on the same locked LEVAL items, deterministic seeds, empirical percentile/p-value rule, and the treatment of ties.
- MAJORITY and SIMPLE-FEAT: specify paired per-item utility contrasts against the frozen candidate and require the pre-specified 95% paired-bootstrap CI lower bound > 0, or provide a fully justified alternative.
- State the resampling unit (LEVAL item; if any dependence clusters exist, state how they are handled), bootstrap seed, and the intersection-union pass logic.
- No candidate, threshold, seed, baseline, or tie-break may be chosen after LEVAL outputs are observed.

### 2. Resolve the 45-minute abort contradiction
The current estimate is 45.8 minutes before 15% overhead and about 52.7 minutes after overhead, while the abort rule is 45 minutes. These cannot all stand together.
Using existing logs only (no benchmark), choose one defensible route:
- reduce evaluation count enough that the stated worst-case + overhead fits under a 45-minute abort with explicit safety margin; or
- revise the wall-clock abort and show a defensible margin below the proposed one-hour limit.
If reducing sample count, give a statistical/design rationale and mark power as uncertain; do not invent guaranteed precision.
Clearly distinguish wall-clock time from aggregate GPU-active time. Historical logs did not meter GPU-active time, so define the instrumentation and fail-safe. If the aggregate GPU-hour cap cannot be enforced reliably, state the limitation instead of pretending wall-clock and GPU-active hours are identical.
The budget is only a request; it is not authorization.

### 3. Make feature selection and best-fixed selection non-overlapping
The current protocol assigns feature selection to both FIT cross-fitting and TUNE.
Write one deterministic pipeline. For example:
- FIT internal CV selects only predictor class/regularization among a predeclared grid;
- TUNE selects from a predeclared feature-set/threshold grid;
- final candidate, feature set, thresholds and all seeds are frozen before LEVAL.
Alternatively use another fully specified nested scheme, but do not let FIT and TUNE ambiguously make the same choice.
Define the best-fixed rule precisely: either FIT cross-fitted utility selects it and TUNE is confirmation-only, or a pre-specified FIT+TUNE rule selects it. State the tie-break. LEVAL must never influence selection.

### 4. Define the full partition-generation algorithm, not only subset selection
Current v3 describes how to choose pilot subsets inside partitions but does not fully specify how the source train IDs are assigned to BANK/FIT/TUNE/LEVAL.
In the document, specify:
- stable ID normalization (including exact handling of Unicode normalization and whitespace);
- a namespaced partition seed/hash function and deterministic global ordering;
- exact partition counts that sum to 7,473: BANK=2,989, FIT=1,868, TUNE=1,121, LEVAL=1,495 (if using alternative rounding, explicitly define it);
- independent/namespaced pilot-subset selection from FIT/TUNE/LEVAL, with FIT=500, TUNE=200, LEVAL=300;
- exact lock artifacts to be created only during a future authorized CPU preflight: ID lists, ordered-list SHA-256, source revision/hash, partition hashes, exact/normalized duplicate checks against historical evaluation splits.
Do not create those actual lock artifacts or load data in this document-only round. State clearly that all IDs/hashes remain PLANNED.

### 5. Correct status provenance
Update only `status.json.phase2_planning`:
- `reviewed_commit` and `reviewed_executor_deliverable_commit` should refer to the current substantive deliverable `bd21c3363b603606cfefa1ee95ade59f9ae0681d` until the new repair commit exists;
- record the remote HEAD observed at the start of this round as `99a621738156b6626e1960d00652967e549fbc23`;
- clearly separate the R3 document-repair commit from the later status-only commit;
- set next gate to Planner R4 review;
- keep `gpu_authorized: 0`, `implementation_authorized: false`, `pilot_status: NOT AUTHORIZED / NOT EXECUTED`;
- preserve all unrelated status.json fields.

## Files to update
- `plans/phase2_g1_revised_protocol.md`
- `plans/phase2_g1_preflight_decision.md`
- `status.json` (only `phase2_planning`)

Do not change the R5 verdict or claim novelty has been cleared. Do not edit frozen V1/V2 papers, PDFs, supplements, or historical F1/F2 results.

## Forbidden
No GPU, inference, training, controller implementation, dataset fetching/loading, actual partition locks, MATH-500 access, or CPU preflight. No new experiment. Do not treat the proposed <=1.0 GPU-hour request as approved.

## Commit, verify, stop
Commit and push the document-only repair to main. Verify remote HEAD, the file diffs, JSON validity, and any applicable checks actually run. Do not claim local clean status unless observed directly. Report exact SHA, file changes, D2 pass rules, final sample/budget/abort arithmetic, and unresolved limitations. Then stop for Planner R4. No further action without separate explicit authorization.
