# Kimi Code — Phase-2 R5 document-only protocol repair

Repository: https://github.com/yujian777555/NeuroEvoScientist
Branch: main
Role: Executor. GPT is Planner.

## Authority — read the current remote versions first

1. `plans/phase2_planner_review_r5.md`
2. `plans/phase2_g1_revised_protocol.md` (v5)
3. `plans/phase2_g1_preflight_decision.md` (v5)
4. `plans/phase2_controller_design.md`
5. `plans/phase2_r5_related_work_gap.md`
6. `plans/phase2_r5_overlap_matrix.csv`
7. `status.json`

R5 verdict: **CONDITIONAL HOLD**. R4 fixes are substantially accepted, but protocol v5 still has comparator-threshold, ID, feature-reproducibility, permutation-null, deterministic-randomness, majority-tie, and budget-scope ambiguities. This round authorizes document-only changes. GPU authorization remains 0.

Before editing, fetch the current remote `main`, observe its HEAD, check working-tree status and inspect the real diffs. Do not assume a reported SHA is current; do not reset or discard commits.

## Required R5 repairs

### R5-A — define SIMPLE-FEAT thresholds in F0 space

The current protocol reuses the candidate's F1-selected delta/tau for SIMPLE-FEAT even though SIMPLE-FEAT uses F0 scores and an F0-only shift detector. These score and shift-distance scales are not generally comparable.

- Keep the selected model class/hyperparameters fixed as predeclared.
- Fit the F0 policy on FIT only.
- On TUNE, select SIMPLE-FEAT's own `delta` from the existing frozen grid and `tau` from the F0-specific TUNE shift-score percentiles (90/95/99), using realized utility at locked lambda=0.1.
- Specify deterministic tie-breaks and final FIT-only refit/freeze.
- Keep the F1 candidate's own F1-space thresholds independently selected on TUNE.
- Both candidate and comparator must be frozen before LEVAL.
- If a different method is proposed, justify score-scale comparability from the written definitions, not unsupported assertions.

Do not access LEVAL or change the F0 early NO-GO rule.

### R5-B — remove ambiguity from canonical fallback IDs

Rewrite the ID rule so every canonical ID has exactly one namespace prefix:
- Source ID: `src:` + normalized source scalar.
- Fallback ID: `q:` + lowercase SHA-256 hex of UTF-8 bytes for `question\0` followed by normalized question text.
- State explicitly that `q:` is applied exactly once, not once to the question text and again to the hash.
- Define exactly when source IDs are considered missing/unusable and fallback is used.
- Preserve NFC, trim, internal-whitespace collapse, empty/duplicate failure, UTF-8 and deterministic ordering rules.

Do not generate actual IDs or lock files.

### R5-C — fully specify the frozen features and embedding encoder

The current protocol uses a generic “frozen query embedding” and F0 “question length/numeric density”, which are not reproducible enough for confirmatory evaluation.

In the protocol and, if needed, the controller design document (but respect the file-scope rule below), specify:
- exact embedding model ID and immutable revision/weight hash;
- tokenizer ID/version, text normalization, truncation/max length, pooling method, output normalization, dimension and deterministic inference settings;
- exact question-length feature definition;
- exact regex/token rule for numeric tokens and exact numeric-density denominator;
- required package/runtime versions and how cached embedding outputs will be hashed/validated;
- that all embedding vectors and feature extraction are fixed before LEVAL and never use outcomes.

Do not download or load the encoder, do not access the dataset, and do not generate embeddings this round. If the exact model/revision cannot be responsibly fixed from existing project metadata, record the blocker and stop for Planner R6 rather than inventing a hash.

### R5-D — define the SHUFFLE null when a replicate selects F0

The current protocol excludes F0-NO-GO replicates and computes the percentile over valid F1-selected replicates. This is a conditional null and must be explicitly justified.

- State the null estimand and that the percentile is conditional on a permutation replicate selecting F1, if retaining this approach.
- Explain why conditioning on F1 selection matches the observed candidate's pre-LEVAL eligibility event.
- Mandate reporting: total replicates, F0-NO-GO count/rate, other invalid/failure count, valid F1-scored count M, and the conditional mid-rank percentile.
- Preserve `M < 950 => INCONCLUSIVE_NULL`.
- If a valid conditional interpretation cannot be justified, propose an alternative predeclared statistic for NO-GO replicates and explain it for Planner review. Do not silently drop replicates or alter the denominator after outcomes.

### R5-E — make permutations bit-reproducible and correct fit-count terminology

Fisher–Yates plus a seed is insufficient unless the random integer stream is specified.

- Name the exact PRNG algorithm and version/runtime, and the seed-to-stream procedure; or define a fully specified hash-based deterministic permutation algorithm with exact bytes, ordering and tie-breaks.
- Keep FIT/TUNE permutation streams independent and namespaced.
- Explain what one “policy-fit invocation” means versus individual estimator fits. Ridge/GBT use one regressor per non-B1 action, so do not describe 103 policy-fit invocations as 103 underlying estimator fits.
- Reconcile the worst-case fit-count arithmetic and retain the provisional four-CPU-hour timeout only as a future proposal pending an authorized two-replicate smoke test.
- No CPU preflight or smoke test is authorized in this round.

### R5-F — define MAJORITY frequency tie-breaking

Replace “ties per §2” for MAJORITY frequency ties with an explicit rule. Recommended: among configurations with the same highest observed best-action frequency on FIT, choose the first in the frozen order `(B1, B0, B3, REF, B2)`. Distinguish this from per-item utility ties.

### R5-G — separate GPU inference budget from CPU permutation-analysis timeout

State clearly:
- 55-minute wall-clock fail-safe and 60-minute cap apply to the GPU inference/data-collection phase only;
- CPU permutation replay is a separate analysis phase with its own proposed timeout/checkpoint rules;
- the four-CPU-hour timeout is provisional and not authorized;
- the CPU phase is not included in aggregate GPU-hour accounting;
- incomplete or timed-out permutation analysis yields INCONCLUSIVE/INCOMPLETE, never a partial-null PASS.

Do not alter the <=1.0 aggregate GPU-hour request; it remains unapproved.

## File-scope rule

Permitted files:
1. `plans/phase2_g1_revised_protocol.md`
2. `plans/phase2_g1_preflight_decision.md`
3. `status.json`, only the `phase2_planning` object

Do not modify the R5 review or this prompt, R5 literature files, controller design, frozen V1/V2 papers/PDFs/supplements, or historical F1/F2 results. If exact feature metadata cannot be responsibly specified from current approved sources, stop and report the blocker rather than expanding scope.

## Forbidden this round

No GPU, inference, training, controller implementation, dataset download/loading, embedding generation, CPU preflight, actual partition/subset locks, MATH-500 access, or new experiment. Do not claim M1/M2 novelty is cleared.

## Verification, commits, and stop

1. Check each R5-A…R5-G against the actual revised protocol.
2. Verify ID canonicalization examples and SHA input-byte definitions are unambiguous.
3. Verify F0/F1 candidate and baseline thresholds are separately specified and frozen before LEVAL.
4. Verify permutation null conditioning, denominator, seed/PRNG, fit-count unit, and timeout scope are explicit.
5. Verify partition counts (2,989/1,868/1,121/1,495 = 7,473), subsets (500/200/300), evaluation count (5,000), lambda algebra, and 52.7 < 55 < 60 arithmetic.
6. Run document-level checks actually available; report exactly what ran. Do not claim model/unit tests passed unless actually run.
7. Inspect diffs; only permitted files may change.
8. Commit and push the substantive document changes to `main`; verify remote HEAD.
9. Update only `status.json.phase2_planning` in a separate status-only commit. Record the actual starting remote HEAD, substantive R5 deliverable SHA, prior R4 status-only SHA `c80d90d4d8901c2e110680751ddb2b02c4eed09f`, and current pre-status-update HEAD. Do not self-reference the commit that contains the final status value.
10. Verify final remote HEAD, status JSON and working-tree state if available.

Final status:
**R5 DOCUMENT REPAIRS COMPLETE — STOP AND WAIT FOR PLANNER R6 REVIEW**

If any requested feature/model detail cannot be fixed without inventing facts or downloading artifacts, do not improvise. Record it as unresolved and stop for Planner R6. No CPU preflight or GPU Pilot without separate explicit approval.
