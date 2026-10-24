# Phase-2 G1 Preflight Decision v5 — Executor Report (2026-10-24)

Authority: `plans/phase2_planner_review_r4.md`,
`plans/phase2_g1_pilot_repair_prompt_r4.md`.
Scope executed: document-only repair of
`plans/phase2_g1_revised_protocol.md` (v5), this report, and a separate
status-only update to `status.json.phase2_planning`.

**Boundary:** 0 GPU, 0 inference, 0 training, no controller implementation,
no dataset access, no partition/subset locks, no CPU preflight, no
MATH-500 access, and no changes to frozen V1/V2 papers, PDFs,
supplements, or historical F1/F2 results.

## R4 issue-by-issue resolution

| Item | Result | Actual repair in protocol v5 |
|---|---|---|
| R4-A — inconsistent predictor contract | DONE | §3 defines one action-score/action contract for every class. Ridge and GBT regress per-action `u_i(c)-u_i(B1)`; multinomial logistic predicts best-action probabilities and scores `p_i(c)-p_i(B1)`. All classes are selected by the same held-out **realized utility of chosen actions**, not Δu-R². Independent grids: ridge alpha, logistic C, GBT n_estimators/max_depth with fixed loss/learning_rate/subsample/seed. FIT selects class/hyperparameters; TUNE selects only feature set and thresholds; final FIT-only refit follows TUNE. Deterministic tie, fit-failure, and invalid-output rules are explicit. |
| R4-B — SIMPLE-FEAT can equal candidate | DONE | If TUNE selects F0, status is `NO-GO_IDENTICAL_TO_SIMPLE-FEAT` before any LEVAL output is generated or inspected; no doomed comparison and no baseline substitution. Only F1 proceeds. SIMPLE-FEAT uses the same class/hyperparameters/thresholds but F0 throughout, including its shift detector. |
| R4-C — SHUFFLE retains original TUNE information | DONE | §3.4 permutes the complete per-config outcome vector independently within FIT and TUNE, recomputes both regression targets and classification labels, and replays the full adaptive pipeline (FIT CV, feature models, TUNE feature/threshold selection, final FIT refit) for all 1,000 replicates. Within-item config outcomes remain paired; LEVAL outcomes are used only for final scoring. No new LLM calls are required. Valid-replicate and `INCONCLUSIVE_NULL` rules are explicit. |
| R4-D — contradictory endpoint hierarchy | DONE | Utility at locked lambda=0.1 is the primary D2 pass/fail endpoint. Raw accuracy, prompt tokens, completion tokens, and accuracy–token Pareto are mandatory separate secondary outcomes. Lambda remains exploratory-informed and cannot be selected from LEVAL. |
| R4-E — complete-pair deletion bias | DONE | Any missing/invalid required output on any LEVAL item makes the run `INCOMPLETE/INVALID`; no D2 PASS, no selective retry, no item deletion. The same rule applies to candidate and baselines. Incorrect answers remain valid zero-score outcomes. |
| R4-F — incomplete ID canonicalization | DONE | One contract covers source and fallback IDs: canonical string conversion, Unicode NFC, trim/internal-whitespace collapse, empty/duplicate failure, `src:`/`q:` namespaces, exact UTF-8 hash bytes, and deterministic `(digest, norm_id)` sorting. Partition/subset/fold namespaces are distinct; counts remain 2,989/1,868/1,121/1,495 and 500/200/300. |
| R4-G — bootstrap underspecified | DONE | Two-sided percentile 95% CI, 10,000 paired item-level resamples, seed S0=20261021, type-7 linear quantile interpolation, identical sampled indices across configurations, lower bound >0. The same rule applies to BEST-FIXED, MAJORITY, and SIMPLE-FEAT. |
| R4-H — stale status pointers/provenance | DONE | Only `phase2_planning` is updated in the separate status commit. Current R4 review/prompt and document list are retained; next gate is Planner R5. Observed HEAD at repair start, substantive deliverable, and status-only commit are distinguished; no final status commit is self-referenced. |

## Final sample, budget, and stop rules

- Planned partitions: BANK/FIT/TUNE/LEVAL = 2,989/1,868/1,121/1,495 =
  7,473. Planned pilot subsets: FIT=500, TUNE=200, LEVAL=300. Planned
  evaluations: 5 × (500+200+300) = **5,000**.
- Worst case: 5,000/100 × 55 s = 2,750 s = 45.8 min; +15% = 52.7 min.
  Expected from per-config observed rates: approximately 24 min.
- Wall-clock fail-safe: abort at 55 min and report INCOMPLETE. Margins:
  2.3 min above worst-case-plus-overhead and 5 min below the 60-min cap.
  GPU-active time is bounded by wall time on one GPU (≤0.92 GPU-hour);
  pynvml GPU-second metering is planned, while wall time is not presented
  as measured GPU-active time.
- **Budget request remains ≤1.0 aggregate GPU-hour and is NOT an
  authorization.**

## Checks actually run

- Custom document-invariant script: PASS. Verified partition and subset
  counts, 5,000-evaluation arithmetic, 52.7 < 55 < 60, lambda algebra,
  required D2/policy/failure terminology, and removal of the old R² and
  complete-pair wording.
- `status.json` parsed as valid JSON at check time: PASS.
- R5 matrix parsed with 18 rows: PASS; it was not modified in this round.
- `git diff --check`: PASS (no whitespace errors).
- Forbidden-phrase scan for pre-registered wording, the withdrawn 45-min
  abort, R² model-selection wording, and complete-pair deletion: no
  matches in the revised protocol.
- No model/unit test suite was rerun: this round changed documents only;
  no such test-run is claimed.

## Explicitly unresolved

- M1 DEFLECT and M2 MEMROUTE remain hypotheses; novelty is **NOT CLEARED**.
  Plain embedding+MLP TACC remains PIVOT. A submission-time literature
  re-audit remains mandatory.
- Actual partition/subset lock artifacts do not exist. Their creation
  requires a separately authorized CPU-only preflight.
- The pilot and its ≤1.0 GPU-hour request remain **NOT AUTHORIZED / NOT
  EXECUTED**. The four-CPU-hour permutation-null timeout is provisional
  and must be calibrated by an authorized two-replicate smoke test.
- Statistical power remains uncertain; NO-GO, INCONCLUSIVE_NULL,
  INCOMPLETE/INVALID, and null outcomes are all reportable and cannot be
  repaired after LEVAL inspection.

**R4 DOCUMENT REPAIRS COMPLETE — STOP AND WAIT FOR PLANNER R5 REVIEW**
