# Phase-2 G1 — Learnability & Pilot Protocol v5 (DOCUMENT ONLY, 0 GPU)

Date: 2026-10-24 (v5: repairs after Planner R4; supersedes v4 where they
conflict)
Authority: `plans/phase2_planner_review_r4.md` (R4-A…R4-H),
`plans/phase2_g1_pilot_repair_prompt_r4.md`.
Nothing here authorizes computation. All locks are **PLANNED, not created**.
No GPU, inference, training, controller implementation, dataset access, CPU
preflight, or MATH-500 access is authorized in this round.

---

## 1. Partitions, canonical IDs, and deterministic locks (R4-F)

### 1.1 Canonical ID contract

The following applies identically to source-provided IDs and fallback IDs:

1. Convert the source ID to a string as follows: strings are used directly;
   integers/floats use their JSON scalar representation
   (`json.dumps(value, ensure_ascii=False)`); `null`, booleans, arrays, and
   objects are invalid. If no usable source ID exists, use the normalized
   question text to construct a fallback.
2. Apply Unicode NFC, strip leading/trailing whitespace, and collapse every
   internal whitespace run to one ASCII space.
3. Prefix the normalized value with its namespace: `src:` for a source ID,
   `q:` for a fallback. The fallback value is
   `q:` + lowercase hex SHA-256 of the UTF-8 bytes of
   `"question\0" + normalized_question_text`.
4. Empty normalized values and duplicate canonical IDs are preflight
   FAILURES, never silently repaired.

Thus `norm_id` is unique and unambiguous across the two ID namespaces.

### 1.2 Hash ordering and planned partitions

For each ordering operation, compute
`digest = SHA256(UTF8(norm_id + "|" + namespace_tag))`, where there is no
trailing newline and the exact bytes are as written. Sort ascending by
`(digest, norm_id)`; the second key makes even an equal-digest tie
deterministic. Namespace tags are distinct:

- `phase2-partition-v1`: sort all 7,473 GSM8K-train items; first 2,989 →
  `BANK`, next 1,868 → `FIT`, next 1,121 → `TUNE`, remaining 1,495 →
  `LEVAL`. The counts sum to 7,473 exactly.
- `phase2-subset-v1`: independently sort within each partition and take the
  first `FIT_pilot=500`, `TUNE_pilot=200`, and `LEVAL_pilot=300` items.
- `phase2-fold-v1`: for FIT cross-validation, assign each FIT_pilot item to
  fold `int.from_bytes(digest[:4], "big") % 5`. The fold assignment is
  fixed before model fitting and does not depend on outcomes.

`LEVAL_pilot` is selected and hash-locked before any LEVAL model outputs
are generated. The subset counts are unchanged; no alternative allocation
is introduced in v5.

### 1.3 Future CPU-preflight artifacts (NOT created now)

Source file path/revision/SHA-256; canonical-ID and fallback-ID audit;
per-partition and per-subset ordered ID lists + SHA-256; pairwise
intersection proofs (must be empty); exact and normalized near-duplicate
checks across partitions and against all historical evaluation splits
(GSM8K test, V1 holdout, F2-locked SVAMP 300). Any failure blocks the
pilot. These artifacts require separate explicit authorization.

### 1.4 Roles

- `BANK`: exemplar-bank content only; never labeled or evaluated as a
  target. During every label/outcome collection, the retrieval bank is
  restricted to BANK, so an item's own answer cannot be retrieved.
- `FIT_pilot`: model-class/hyperparameter selection by 5-fold
  cross-validation, and final FIT-only refitting.
- `TUNE_pilot`: only the predeclared feature-set and threshold selections,
  plus the FIT-selection confirmation report and λ sensitivity.
- `LEVAL_pilot`: one-time confirmatory scoring only. It never participates
  in fitting, tuning, selection, resampling, or redesign.

## 2. Outcome records, utility, and endpoint hierarchy (R4-D/E)

For each item `i` and configuration `c`, the frozen outcome record is
`O(i,c) = (correct_i(c), prompt_tokens_i(c), completion_tokens_i(c),
raw_completion_i(c), validity_i(c))`. Per-item utility is

```
u_i(c) = correct_i(c)
         - lambda * (prompt_tokens_i(c) + completion_tokens_i(c)) / 10,000
```

Dataset utility is the mean of per-item utilities; aggregate prompt and
completion totals are reported separately. At `lambda=0.1`, 1,000 extra
tokens cost `0.1 * 1,000 / 10,000 = 0.01` utility, exactly one accuracy
percentage point. Lambda is **exploratory-informed**, chosen with awareness
of Phase-1 spreads; it is not claimed to be a deployment-optimal price.
Sensitivity at lambda in {0.05, 0.2} is reported on TUNE only.

**Endpoint hierarchy:** for this utility-driven learnability pilot, the
primary D2 pass/fail endpoint is utility at the locked lambda=0.1. Raw
accuracy, prompt tokens, completion tokens, and the accuracy–token Pareto
are mandatory **secondary outcomes**, reported separately and never
collapsed into utility. A result cannot be reclassified as a D2 PASS by
switching to a raw-metric or different-lambda view.

A wrong answer is a valid outcome with `correct=0`, not a missing output.
If any required configuration has a missing/invalid raw completion, score,
or token count on any LEVAL_pilot item, the confirmatory run is
`INCOMPLETE/INVALID`: report the missing count, do not declare D2 PASS, and
do not selectively retry or delete items. The same rule applies to the
candidate and every baseline. Any missing/invalid FIT or TUNE outcome stops
model selection before LEVAL.

The fixed configuration order for action ties is
`(B1, B0, B3, REF, B2)`. When computing an observed best action
`a*_i = argmax_c u_i(c)`, exact utility ties are broken first by lower
measured total tokens and then by this order. Policy-score ties use this
order directly.

## 3. Unified policy contract and model selection (R4-A/B/C)

### 3.1 Common policy output

Every candidate model produces, from pre-inference question features only,
a score vector `s_i(c)` and hence a deterministic action. The B1 score is
anchored to zero. The action rule is

```
c_star = argmax_c s_i(c)   (ties broken by the fixed config order)
action_i = c_star if max_c s_i(c) > delta and shift_score(x_i) <= tau
           B1 otherwise
```

`delta` is in the model's score units; classes are compared by **realized
utility of the resulting action**, never by an R² that is meaningless for a
classifier. The shift score uses the **same feature representation as the
policy**: standardize each feature dimension using FIT_pilot mean/std, then
take the mean Euclidean distance to the 10 nearest FIT_pilot items in that
space (computed once, frozen). Thus F0 uses only its two simple features;
F1 additionally uses the frozen embedding. Tau candidates are the
90th/95th/99th percentiles of TUNE_pilot shift scores in the corresponding
space. No outcome information enters the features.

Feature sets are `F0 = {question length, numeric density}` and
`F1 = F0 + frozen query embedding`. SIMPLE-FEAT uses F0 throughout,
including its shift detector, so it contains no embedding information.

### 3.2 Candidate classes, targets, outputs, and grids

| Class | Training target | Score vector `s_i(c)` | Independent hyperparameter grid |
|---|---|---|---|
| Ridge regression, one regressor per non-B1 action | `u_i(c)-u_i(B1)` | predicted per-action Δu; B1=0 | `alpha ∈ {0.1, 1, 10}`; intercept=True; deterministic solver |
| Multinomial logistic regression over best action | `a*_i` from observed utility (tie rules in §2) | `p_i(c)-p_i(B1)`; B1=0 | `C ∈ {0.1, 1, 10}`; deterministic lbfgs, max_iter=1000, no class weighting |
| GradientBoostingRegressor, one regressor per non-B1 action | `u_i(c)-u_i(B1)` | predicted per-action Δu; B1=0 | `n_estimators ∈ {50,100}`, `max_depth ∈ {1,3}`; squared-error loss, learning_rate=0.05, subsample=1.0, random_state=S0 |

No alpha is assigned to GBT. The logistic output is an action-probability
advantage, not a Δu estimate; it is therefore evaluated by action utility,
not Δu-R². A logistic fold that lacks any action class, including B1, is a
failed candidate fit and is excluded deterministically.

### 3.3 Single ordered selection procedure

All rules and grids are frozen before LEVAL.

1. **FIT cross-validation only.** For each class, hyperparameters, and
   feature set, fit on four folds and evaluate on the held-out fold using
   neutral gating (`delta=0`, `tau=+infinity`). The score is mean realized
   utility of the selected actions at lambda=0.1 from the frozen per-config
   outcomes. Compute `S(F0)` and `S(F1)`; the class/hyperparameter score is
   `(S(F0)+S(F1))/2`, giving equal weight to each feature set without
   selecting a feature set in FIT.
2. **FIT model choice.** Select class/hyperparameters by that score.
   Deterministic ties prefer: ridge < logistic < GBT; larger alpha/C;
   shallower then fewer GBT trees; then lexicographic grid key. A candidate
   whose fit fails on any fold is excluded. If all candidates fail on a
   fold, model selection is INVALID and stops before LEVAL.
3. **FIT-only feature candidates.** Refit the selected class/hyperparameters
   on all FIT_pilot items separately for F0 and F1. Do not add TUNE items
   to these fits.
4. **TUNE-only selection.** Apply the two policies to TUNE_pilot and select
   the feature set, `delta ∈ {0.0, 0.005, 0.01, 0.02}`, and tau by maximum
   realized utility at lambda=0.1. Ties prefer F0, then smaller delta, then
   smaller tau. Lambda sensitivity is reported but cannot change the locked
   primary lambda.
5. **BEST-FIXED.** Select the fixed configuration with the highest mean
   realized utility on FIT_pilot at lambda=0.1. A fixed config requires no
   model fitting; FIT alone selects it. TUNE computes a confirmation
   ranking that cannot change the selection; disagreements are reported
   only. Exact ties use lower total tokens, then the fixed config order.
6. **Degeneracy guard.** If TUNE selects **F0**, stop with
   `D2 = NO-GO_IDENTICAL_TO_SIMPLE-FEAT` **before generating or inspecting
   any LEVAL output**. The candidate would be identical to the required
   independent simple-feature comparator, so the strict positive-difference
   gate is uninterpretable. LEVAL is not opened to confirm a doomed test,
   and the baseline is never changed to make the comparison possible.
7. **Final refit and freeze (F1 only).** If TUNE selects F1, refit the
   selected class/hyperparameters on FIT_pilot only using F1, apply the
   TUNE-selected delta/tau, and freeze the candidate. Any full-fit failure
   or non-finite/invalid policy output is INVALID and prevents a PASS.
   Only now may the one-time LEVAL evaluation occur.

**SIMPLE-FEAT** uses the same selected class/hyperparameters and the same
frozen delta/tau, but is fitted on FIT_pilot with F0. It is therefore a
fair, predeclared comparator isolating the embedding's contribution; it is
never redefined after seeing results.

### 3.4 Permutation null that replays the entire pipeline (R4-C)

Let `Y_i` be the complete per-config outcome vector for item `i` and `X_i`
its features. For each replicate `r=1,...,1000`:

1. Deterministically permute `Y_i` among FIT_pilot items with seed stream
   `sha256("shuffle-fit|" + S0 + "|" + r)`, and independently among
   TUNE_pilot items with `sha256("shuffle-tune|" + S0 + "|" + r)`. Use a
   deterministic Fisher–Yates permutation over canonical-ID order; the
   integer seed is `int.from_bytes(digest[:8], "big")`.
2. Move the **whole** outcome vector per item, preserving within-item
   pairing across configurations while breaking feature–outcome
   association. Recompute regression Δu targets and best-action labels
   from the permuted vectors; do not permute only one target column.
3. Rerun the identical adaptive pipeline: FIT cross-validation of
   class/hyperparameters, the two full-FIT feature models, TUNE
   feature-set and threshold selection, and final FIT-only refit. Fold
   assignment remains fixed by canonical ID. Model-failure and tie rules
   are unchanged.
4. If a replicate selects F0, it is `NO-GO` and is not scored, matching the
   candidate's guard. Otherwise score its frozen policy on the same locked
   LEVAL outcomes, which are never used for fitting/tuning.

The null distribution contains the LEVAL utilities of valid replicates.
Candidate PASS against SHUFFLE requires a mid-rank percentile of at least
0.95: `(#{u_null < u_cand} + 0.5*#{u_null = u_cand}) / M >= 0.95`, where
`M` is the number of valid replicates. If `M < 950`, the gate is
`INCONCLUSIVE_NULL`, never PASS. This preserves the same adaptive selection
opportunities under the null rather than retaining original TUNE
information.

No new LLM calls are needed for permutations once per-config outcomes are
frozen. Each full replay entails at most 103 small model fits (10
class/hyperparameter candidates × 2 feature sets × 5 folds = 100, plus two
feature fits and one final refit), hence about 103,000 fits for 1,000
replicates. No runtime measurement exists. During a separately authorized
CPU preflight, a two-replicate smoke test must measure throughput before a
provisional four-CPU-hour timeout; checkpoint every 10 replicates and never
present a partial null as complete. **No CPU preflight is performed now.**

## 4. D2 gate — statistics and pass rules (R4-A/G)

Everything—candidate, grids, feature choice rule, thresholds, baselines,
seeds, and this gate—is frozen before LEVAL inference.

### 4.1 Paired bootstrap contrasts

For candidate − BEST-FIXED (primary), candidate − MAJORITY, and candidate −
SIMPLE-FEAT:

- Compute per-item paired utility differences on the 300 LEVAL items.
- Draw 10,000 item-level resamples of size 300 with replacement, seed
  `S0=20261021`; use the same sampled indices for all configurations in
  each replicate.
- Construct a two-sided **percentile** 95% CI using the 2.5th and 97.5th
  percentiles of the sorted bootstrap means, with linear (type-7) quantile
  interpolation. The pass rule is **CI lower bound > 0** for each contrast.

MAJORITY is the most frequent observed best action on FIT_pilot (ties per
§2). If it coincides with BEST-FIXED, the contrasts are reported as such;
the rule does not change.

Exact McNemar on binary accuracy is secondary to the utility gate and
cannot substitute for it.

### 4.2 SHUFFLE and RANDOM

SHUFFLE follows §3.4 with its 1,000-replay null and mid-rank rule. RANDOM
uses 1,000 independent uniform per-item configuration assignments with seed
stream `sha256("random-policy|" + S0 + "|" + r)`; score their LEVAL
utilities and apply the same mid-rank >=0.95 rule. Invalid replicates are
reported; `M < 950` means INCONCLUSIVE, not PASS.

### 4.3 Intersection–union gate

**D2 PASS ⟺ all five contrasts pass:** BEST-FIXED CI lower >0, SHUFFLE
percentile >=0.95, RANDOM percentile >=0.95, MAJORITY CI lower >0, and
SIMPLE-FEAT CI lower >0. Each test is at level 0.05; no post-hoc metric,
threshold, seed, or baseline substitution is allowed. Secondary contrasts
are explicitly exploratory.

## 5. Precision and failure interpretation

No unconditional precision claim is made. For paired binary differences at
n=300, illustrative 95% half-widths are approximately `1.96*sqrt(q/300)`:
q=5% → ±2.5pp; 10% → ±3.6pp; 20% → ±5.1pp; 40% → ±7.2pp. Utility CIs may
be wider due to token variance. F2 discordance values (16.7%, 22.7%) are
planning-only and transfer-limited. This is a **learnability screen with
uncertain power**, not a guaranteed effect-size detector. A null,
NO-GO, INCONCLUSIVE_NULL, or INCOMPLETE/INVALID result is reported rather
than repaired post hoc.

## 6. Budget and accounting (proposal only)

Existing F1 logs give a conservative wall-clock basis of 55 s per 100
items/config (prompt + generation + scoring, model loaded once per process,
fresh caches; bank build excluded and small). Planned evaluations remain
5,000 = 5 configs × (500 FIT + 200 TUNE + 300 LEVAL):

- worst case: 5,000/100 × 55 = 2,750 s = 45.8 min; +15% overhead = 52.7
  min ≈ 0.88 wall-hours;
- expected from per-config observed rates: ≈24 min.

Wall-clock fail-safe: abort at 55 min, report INCOMPLETE, and never present
partial averages as complete. Worst-case-plus-overhead leaves 2.3 min to
abort and 5 min to the 60-min cap. Single-GPU GPU-active time cannot exceed
wall time; hence the wall fail-safe bounds GPU-active ≤0.92 GPU-hour.
Planned pynvml utilization sampling (10 s) and GPU-second integration must
be recorded in the manifest; if unavailable, the wall fail-safe enforces
the cap. Wall time is never called measured GPU-active time.

**Budget request (NOT authorization): ≤1.0 aggregate GPU-hour**, with the
55-min fail-safe and metering.

## 7. Confirmation-data policy

F2 SVAMP 300 is retired as fresh confirmation and is descriptive only.
MATH-500 remains a candidate only; it is untouched until an immutable
ID/revision/hash lock and overlap policy are committed. No confirmation
outcomes are used for policy selection. V1/F1/F2 results are
hypothesis-generating only; frozen artifacts remain unchanged.

## 8. Scope and novelty boundary

The candidate set remains B1 (cost floor), REF, B2 (dev-selected anchor,
not a universal best), B3, and B0. BEST-FIXED follows §3.3 step 5.
Greedy decoding and cached completions support paired comparisons; any
retrospective oracle is exploratory and non-deployable.

Plain embedding+MLP TACC remains PIVOT. DEFLECT and MEMROUTE remain
hypotheses whose novelty is **NOT CLEARED**. No "first" or "no prior work"
claim is made. All gating language is **pre-specified and commit-locked
before LEVAL inference**, not external preregistration.
