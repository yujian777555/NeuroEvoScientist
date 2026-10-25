# Phase-2 G1 — Learnability & Pilot Protocol v6 (DOCUMENT ONLY, 0 GPU)

Date: 2026-10-24 (v6: repairs after Planner R5; supersedes v5 where they
conflict)
Authority: `plans/phase2_planner_review_r5.md` (R5-A…R5-G),
`plans/phase2_planner_review_r4.md` (R4-A…R4-H, accepted and preserved),
`plans/phase2_g1_pilot_repair_prompt_r4.md`.
Nothing here authorizes computation. All locks are **PLANNED, not created**.
No GPU, inference, training, controller implementation, dataset access, CPU
preflight, or MATH-500 access is authorized in this round.

---

## 1. Partitions, canonical IDs, and deterministic locks (R4-F, R5-B)

### 1.1 Canonical ID contract (exact, R5-B)

Each item has exactly one canonical ID, constructed as follows:

1. **Source-ID branch.** If the source record provides a usable source ID,
   convert it to a string: strings are used directly; integers/floats use
   their JSON scalar representation (`json.dumps(value, ensure_ascii=False)`);
   `null`, booleans, arrays, and objects are **unusable**. Then apply Unicode
   NFC, strip leading/trailing whitespace, and collapse every internal
   whitespace run to one ASCII space. If the result is non-empty, the
   canonical ID is

   ```
   norm_id = "src:" + normalized_source_scalar
   ```

   If the source ID is missing, unusable (wrong scalar type), or normalizes
   to the empty string, the fallback branch is used instead.

2. **Fallback branch.** Normalize the question text with the identical rule
   (Unicode NFC, strip leading/trailing whitespace, collapse every internal
   whitespace run to one ASCII space). The fallback value — i.e., the value
   that is prefixed — is the lowercase hex SHA-256 digest of the UTF-8 bytes
   of `"question\0" + normalized_question_text` (a literal NUL byte after the
   word `question`, no trailing newline). The canonical ID is

   ```
   norm_id = "q:" + sha256_hex
   ```

   The `q:` namespace prefix is applied **exactly once**, to the hex digest
   only; the question text itself never appears inside a canonical ID, and
   no `q:q:` or other double prefix can occur. If the normalized question
   text is empty, this is a preflight FAILURE, not a fallback to anything
   else.

3. Empty normalized values and duplicate canonical IDs (within or across
   the two namespaces) are preflight FAILURES, never silently repaired.

Thus `norm_id` is unique and unambiguous across the two ID namespaces, and
the hashing and prefixing steps are stated exactly once.

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
is introduced in v6.

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
- `TUNE_pilot`: only the predeclared feature-set and threshold selections
  (including the separate SIMPLE-FEAT F0 thresholds, §4.4), plus the
  FIT-selection confirmation report and λ sensitivity.
- `LEVAL_pilot`: one-time confirmatory scoring only. It never participates
  in fitting, tuning, selection, resampling, or redesign.

## 2. Feature contract — fully frozen, no outcomes (R5-C)

Everything in this section is computed **before** LEVAL inference from
question text only. No outcome, answer, token count, or model output of any
kind enters any feature. Features are used for all policy fitting, tuning,
and shift detection; they are never redefined after results are seen.

### 2.1 Text normalization (shared)

Before any feature is computed, the raw question text is normalized:

1. Unicode NFC normalization.
2. Trim leading/trailing whitespace.
3. Collapse every internal whitespace run to one ASCII space.
4. Truncate to the first **2,048 Unicode codepoints** of the normalized
   string.

All downstream features (F0 and F1) use this single normalized, truncated
string.

### 2.2 F0 features (exact definitions)

F0 = {question length, numeric density}, computed from the normalized
string of §2.1:

- **question length** = the number of **Unicode codepoints** in the
  normalized (NFC, trimmed, whitespace-collapsed, 2048-truncated) string.
  This is a codepoint count, not a byte count and not a tokenizer token
  count.
- **whitespace tokens** = the normalized string split on runs of ASCII
  whitespace (post-collapse, equivalently split on the single ASCII space;
  an empty string yields zero tokens).
- **numeric tokens** = whitespace tokens that, **after stripping leading
  and trailing characters in the set `.,;:!?`**, are fully matched by the
  regular expression

  ```
  -?\d[\d,]*(?:\.\d+)?
  ```

  (full match; the empty stripped string never matches).
- **numeric density** = (numeric-token count) / (whitespace-token count),
  and exactly `0.0` when the whitespace-token count is 0.

### 2.3 F1 embedding — stateless HashingVectorizer (exact, R5-C)

**Model selection note.** No pretrained sentence model (e.g., a
MiniLM-class encoder) was downloaded or cached in any prior phase, so no
immutable pretrained weight hash exists to lock. Rather than inventing or
retroactively fabricating a pretrained weight hash, F1 uses a **stateless,
deterministic encoder with no learned weights**: scikit-learn's
`HashingVectorizer`. Because it is stateless, identical inputs on identical
library versions produce bit-identical outputs, which is exactly
reproducible.

- **Algorithm ID**: `hashing-vectorizer-v1`.
- **Library versions (locked)**: `scikit-learn 1.7.2`, `numpy 2.2.6`,
  `scipy 1.15.3`, on CPython 3.11+ / 64-bit little-endian.
- **Constructor parameters (exact)**:
  - `analyzer='word'`
  - `token_pattern=r'(?u)\b\w\w+\b'` (matches tokens of ≥2 word characters)
  - `lowercase=True`
  - `ngram_range=(1, 2)`
  - `n_features=384`
  - `alternate_sign=False`
  - `norm='l2'`
  - `dtype=numpy.float64`
- **Input**: the normalized string of §2.1 (NFC, trimmed,
  whitespace-collapsed, truncated to 2,048 Unicode codepoints). No
  additional stop-word removal, stemming, or preprocessing is applied.
- **Statelessness**: the encoder has no fitted state and no learned
  weights; `fit`/`fit_transform`/`transform` all produce the same output
  for the same input, so there is no training-data dependence and no
  checkpoint to hash.
- **Output validation**: transform each question to a **dense C-order
  `float64` NumPy array of shape (384,)** and record the lowercase hex
  SHA-256 of its raw C-contiguous bytes (`.tobytes(order='C')`) as the
  per-item embedding hash. The sorted list of per-item hashes is itself
  SHA-256 hashed as the feature-lock digest. Any deviation in library
  version, parameter, or normalization that changes any hash is a
  preflight FAILURE.

`F1 = F0 + embedding`: the 2 F0 scalars concatenated (in the fixed order
length, then numeric density) with the 384-dimensional vector above,
giving a 386-dimensional feature vector.

## 3. Outcome records, utility, and endpoint hierarchy (R4-D/E)

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
order directly. MAJORITY frequency ties also use this order (§5.1).

## 4. Unified policy contract and model selection (R4-A/B/C, R5-A)

### 4.1 Common policy output

Every candidate model produces, from pre-inference question features only
(§2), a score vector `s_i(c)` and hence a deterministic action. The B1
score is anchored to zero. The action rule is

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
F1 uses the full 386-dimensional vector of §2.3. Tau candidates are the
90th/95th/99th percentiles of TUNE_pilot shift scores in the corresponding
space. No outcome information enters the features.

Feature sets are `F0 = {question length, numeric density}` (§2.2) and
`F1 = F0 + frozen HashingVectorizer embedding` (§2.3). SIMPLE-FEAT uses F0
throughout, including its shift detector, so it contains no embedding
information.

### 4.2 Candidate classes, targets, outputs, and grids

| Class | Training target | Score vector `s_i(c)` | Independent hyperparameter grid |
|---|---|---|---|
| Ridge regression, one regressor per non-B1 action | `u_i(c)-u_i(B1)` | predicted per-action Δu; B1=0 | `alpha ∈ {0.1, 1, 10}`; intercept=True; deterministic solver |
| Multinomial logistic regression over best action | `a*_i` from observed utility (tie rules in §3) | `p_i(c)-p_i(B1)`; B1=0 | `C ∈ {0.1, 1, 10}`; deterministic lbfgs, max_iter=1000, no class weighting |
| GradientBoostingRegressor, one regressor per non-B1 action | `u_i(c)-u_i(B1)` | predicted per-action Δu; B1=0 | `n_estimators ∈ {50,100}`, `max_depth ∈ {1,3}`; squared-error loss, learning_rate=0.05, subsample=1.0, random_state=S0 |

No alpha is assigned to GBT. The logistic output is an action-probability
advantage, not a Δu estimate; it is therefore evaluated by action utility,
not Δu-R². A logistic fold that lacks any action class, including B1, is a
failed candidate fit and is excluded deterministically.

**Fit-count convention (R5-E).** With four non-B1 actions (B0, B3, REF,
B2), each ridge or GBT **policy-fit invocation** entails 4 underlying
estimator fits, and each multinomial logistic policy-fit invocation entails
1 underlying estimator fit. All workload accounting distinguishes these two
units (§4.5).

### 4.3 Single ordered selection procedure

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
4. **TUNE-only candidate selection.** Apply the F0 and F1 policies to
   TUNE_pilot and select the candidate's feature set, candidate delta
   `delta_cand ∈ {0.0, 0.005, 0.01, 0.02}`, and candidate tau_cand by
   maximum realized utility at lambda=0.1. Ties prefer F0, then smaller
   delta, then smaller tau. If F1 is selected, tau_cand comes from the F1
   shift space; if F0 were selected it would come from the F0 shift space
   (but see step 6: an F0 selection ends the pilot as NO-GO). Lambda
   sensitivity is reported but cannot change the locked primary lambda.
5. **BEST-FIXED.** Select the fixed configuration with the highest mean
   realized utility on FIT_pilot at lambda=0.1. A fixed config requires no
   model fitting; FIT alone selects it. TUNE computes a confirmation
   ranking that cannot change the selection; disagreements are reported
   only. Exact ties use lower total tokens, then the fixed config order.
6. **Degeneracy guard.** If TUNE selects **F0** for the candidate, stop
   with `D2 = NO-GO_IDENTICAL_TO_SIMPLE-FEAT` **before generating or
   inspecting any LEVAL output**. The candidate would be identical to the
   required independent simple-feature comparator, so the strict
   positive-difference gate is uninterpretable. LEVAL is not opened to
   confirm a doomed test, and the baseline is never changed to make the
   comparison possible.
7. **Final candidate refit and freeze (F1 only).** If TUNE selects F1,
   refit the selected class/hyperparameters on FIT_pilot only using F1,
   apply the TUNE-selected delta_cand/tau_cand, and freeze the candidate.
   Any full-fit failure or non-finite/invalid policy output is INVALID and
   prevents a PASS. Only now may the one-time LEVAL evaluation occur.

### 4.4 SIMPLE-FEAT — independent F0-only pipeline (R5-A)

SIMPLE-FEAT is a fully defined, fair F0-only pipeline. It keeps the
selected class/hyperparameters frozen from §4.3 step 2, but it does **not**
reuse the candidate's F1 thresholds: F0 model scores and F0 shift distances
are not on the same scale as the F1 score/embedding space, and no
scale-invariance argument is claimed. Instead:

1. **F0 thresholds.** Using the F0 policy fitted on all FIT_pilot items
   (§4.3 step 3), run a TUNE_pilot selection over the **same predeclared
   delta grid** `{0.0, 0.005, 0.01, 0.02}` and **F0-specific tau
   candidates** (the 90th/95th/99th percentiles of TUNE_pilot shift scores
   in the F0 shift space), selecting `(delta_f0, tau_f0)` by maximum
   realized utility at lambda=0.1. Ties prefer smaller delta, then smaller
   tau.
2. **Final FIT-only refit.** Refit the selected class/hyperparameters on
   FIT_pilot only using F0, apply `(delta_f0, tau_f0)`, and freeze the
   SIMPLE-FEAT policy. Any fit failure or non-finite/invalid policy output
   is INVALID and prevents a PASS.
3. Both the candidate (with its own F1-selected `delta_cand/tau_cand`) and
   SIMPLE-FEAT (with its own F0-selected `delta_f0/tau_f0`) are frozen
   **before LEVAL inference**. SIMPLE-FEAT is a predeclared comparator
   isolating the embedding's contribution; it is never redefined after
   seeing results.

### 4.5 Permutation null that replays the entire pipeline (R4-C, R5-D/E)

Let `Y_i` be the complete per-config outcome vector for item `i` and `X_i`
its features. For each replicate `r=1,...,1000`:

1. Deterministically permute `Y_i` among FIT_pilot items with seed stream
   `sha256("shuffle-fit|" + S0 + "|" + r)`, and independently among
   TUNE_pilot items with `sha256("shuffle-tune|" + S0 + "|" + r)`. Use the
   deterministic Fisher–Yates permutation of §4.6 over canonical-ID order.
2. Move the **whole** outcome vector per item, preserving within-item
   pairing across configurations while breaking feature–outcome
   association. Recompute regression Δu targets and best-action labels
   from the permuted vectors; do not permute only one target column.
3. Rerun the identical adaptive pipeline: FIT cross-validation of
   class/hyperparameters, the two full-FIT feature models, TUNE
   feature-set and threshold selection (including the SIMPLE-FEAT F0
   threshold selection of §4.4), and final FIT-only refit. Fold assignment
   remains fixed by canonical ID. Model-failure and tie rules are
   unchanged.
4. If a replicate selects F0 for the candidate, it is an **F0-NO-GO
   replicate** and is not scored, matching the candidate's guard. Otherwise
   score its frozen F1 policy on the same locked LEVAL outcomes, which are
   never used for fitting/tuning.

**Conditional definition (R5-D).** The SHUFFLE test is explicitly a test
of the null hypothesis **conditional on the replicate's adaptive pipeline
selecting F1**, because the observed candidate reaches LEVAL only after
selecting F1 (§4.3 steps 6–7). Conditioning the null on the same selection
event makes the replicate distribution comparable to the observed
candidate's path: both the candidate and each scored replicate survive the
identical F0-degeneracy guard before any LEVAL scoring. The estimand is
therefore the distribution of LEVAL utility under the null **among
pipelines that select F1**, which is the event the candidate itself
realized.

**Mandatory replicate accounting (R5-D).** Report, exactly:

- `M_total` = 1,000 replicates attempted;
- `M_F0-NO-GO` = replicates whose candidate selection chose F0 (unscored);
- `M_other-invalid` = replicates invalid for any other reason (fit failure,
  invalid policy output, etc.), with reasons counted;
- `M` = valid scored F1 replicates = `M_total − M_F0-NO-GO −
  M_other-invalid`, together with each proportion.

The null distribution contains the LEVAL utilities of the `M` valid F1
replicates. Candidate PASS against SHUFFLE requires a mid-rank percentile
of at least 0.95:
`(#{u_null < u_cand} + 0.5*#{u_null = u_cand}) / M >= 0.95`. If
`M < 950`, the gate is `INCONCLUSIVE_NULL`, never PASS. No replicate is
silently dropped, and no denominator is altered after seeing outcomes.

**Workload accounting (R5-E).** A full replay entails at most **103
policy-fit invocations**: 10 class/hyperparameter candidates × 2 feature
sets × 5 folds = 100, plus two full-FIT feature fits (F0, F1), plus one
final FIT-only refit. In **underlying estimator fits** (§4.2), the worst
case is **322**: all three ridge and all four GBT grid candidates (7
candidates × 4 estimators each) plus all three logistic candidates (3 × 1)
= 31 estimator fits per (feature set × fold), × 2 feature sets × 5 folds =
310, plus the full-FIT F0/F1 fits and final refit (at most 3 × 4 = 12 when
a per-action regressor class is selected) = 322. SIMPLE-FEAT's final F0
policy (§4.4 step 2) is the same deterministic fit as the full-FIT F0
feature fit of §4.3 step 3 — identical data, class, hyperparameters, and
solver — so it adds no new invocation; only its `(delta_f0, tau_f0)` gating
differs, and threshold application is not a fit. Hence at most about
103,000 policy-fit invocations and 322,000 estimator fits for 1,000
replicates. No runtime measurement exists. During a separately authorized
CPU preflight, a two-replicate smoke test must measure throughput before a
provisional four-CPU-hour timeout; checkpoint every 10 replicates and never
present a partial null as complete. **No CPU preflight is performed now.**

### 4.6 Deterministic PRNG and permutation (exact, R5-E)

All permutation and resampling randomness uses **NumPy PCG64** (the
`numpy.random.PCG64` bit generator, NumPy 2.2.6) inside a
`numpy.random.Generator`. For any labeled stream, the 64-bit unsigned
integer seed is

```
seed = int.from_bytes(sha256(UTF8(label + "|" + S0 + "|" + r))[:8], "big")
```

with `S0 = 20261021`, the stream label (e.g., `shuffle-fit`, `shuffle-tune`,
`random-policy`), and replicate index `r`, encoded exactly as written (no
trailing newline, decimal `S0` and `r`). The generator is
`numpy.random.Generator(numpy.random.PCG64(seed))`, a fresh generator per
(stream, replicate) so no cross-replicate state leaks.

**Deterministic Fisher–Yates.** To permute `n` items in canonical-ID order,
iterate `i` from `n−1` down to `1` and draw
`j = generator.integers(0, i+1)` (uniform over the closed interval
`[0, i]`), swapping positions `i` and `j`. The same seed on the same NumPy
version and platform (64-bit little-endian) reproduces the identical
permutation; library/platform versions are recorded in the lock manifest.

## 5. D2 gate — statistics and pass rules (R4-A/G, R5-F)

Everything—candidate, grids, feature choice rule, thresholds, baselines,
seeds, and this gate—is frozen before LEVAL inference.

### 5.1 Paired bootstrap contrasts

For candidate − BEST-FIXED (primary), candidate − MAJORITY, and candidate −
SIMPLE-FEAT:

- Compute per-item paired utility differences on the 300 LEVAL items.
- Draw 10,000 item-level resamples of size 300 with replacement, using the
  PCG64 generator of §4.6 seeded from the stream label
  `bootstrap-leval` with `r = 1,...,10,000`; use the same sampled indices
  for all configurations in each replicate.
- Construct a two-sided **percentile** 95% CI using the 2.5th and 97.5th
  percentiles of the sorted bootstrap means, with linear (type-7) quantile
  interpolation. The pass rule is **CI lower bound > 0** for each contrast.

MAJORITY is the most frequent observed best action on FIT_pilot. If
multiple configurations share the same highest best-action frequency, the
tie is broken by the **fixed configuration order `(B1, B0, B3, REF, B2)`**
(R5-F); this frequency-tie rule is stated here directly, not by
cross-reference to the per-item utility-tie rule. If MAJORITY coincides
with BEST-FIXED, the contrasts are reported as such; the rule does not
change.

Exact McNemar on binary accuracy is secondary to the utility gate and
cannot substitute for it.

### 5.2 SHUFFLE and RANDOM

SHUFFLE follows §4.5: it is conditional on F1 selection, with the mandatory
`M_total` / `M_F0-NO-GO` / `M_other-invalid` / `M` accounting and the
mid-rank >=0.95 rule; `M < 950` means `INCONCLUSIVE_NULL`, not PASS.
RANDOM uses 1,000 independent uniform per-item configuration assignments
with the PCG64 seed stream label `random-policy` (§4.6); score their LEVAL
utilities and apply the same mid-rank >=0.95 rule. Invalid replicates are
reported; `M < 950` means INCONCLUSIVE, not PASS.

### 5.3 Intersection–union gate

**D2 PASS ⟺ all five contrasts pass:** BEST-FIXED CI lower >0, SHUFFLE
percentile >=0.95, RANDOM percentile >=0.95, MAJORITY CI lower >0, and
SIMPLE-FEAT CI lower >0. Each test is at level 0.05; no post-hoc metric,
threshold, seed, or baseline substitution is allowed. Secondary contrasts
are explicitly exploratory.

## 6. Precision and failure interpretation

No unconditional precision claim is made. For paired binary differences at
n=300, illustrative 95% half-widths are approximately `1.96*sqrt(q/300)`:
q=5% → ±2.5pp; 10% → ±3.6pp; 20% → ±5.1pp; 40% → ±7.2pp. Utility CIs may
be wider due to token variance. F2 discordance values (16.7%, 22.7%) are
planning-only and transfer-limited. This is a **learnability screen with
uncertain power**, not a guaranteed effect-size detector. A null,
NO-GO, INCONCLUSIVE_NULL, or INCOMPLETE/INVALID result is reported rather
than repaired post hoc.

## 7. Budget, sequencing, and accounting (proposal only; R5-G)

### 7.1 Two-stage sequencing

The pilot runs in two strictly separated stages:

1. **Stage 1 — GPU FIT+TUNE data collection.** GPU inference is used only
   to collect the frozen per-config outcomes on FIT_pilot and TUNE_pilot
   (5 configs × (500 + 200) = 3,500 evaluations). All model selection,
   threshold selection (including SIMPLE-FEAT's F0 thresholds), and the
   full SHUFFLE permutation null then run on **CPU only**, on frozen
   outcomes. The candidate policy and all gates are frozen before any LEVAL
   GPU call.
2. **Stage 2 — LEVAL GPU.** Only if the Stage-1 pipeline selects F1 for the
   candidate (i.e., the F0 degeneracy guard does not fire) may the one-time
   LEVAL GPU evaluation (5 configs × 300 = 1,500 evaluations) run. If the
   guard fires, no LEVAL GPU inference occurs at all.

### 7.2 GPU budget (FIT+TUNE + possible LEVAL)

Existing F1 logs give a conservative wall-clock basis of 55 s per 100
items/config (prompt + generation + scoring, model loaded once per process,
fresh caches; bank build excluded and small). Total planned GPU evaluations
remain at most 5,000 = 5 configs × (500 FIT + 200 TUNE + 300 LEVAL):

- worst case: 5,000/100 × 55 = 2,750 s = 45.8 min; +15% overhead = 52.7
  min ≈ 0.88 wall-hours;
- expected from per-config observed rates: ≈24 min.

The **55-minute abort / 60-minute cap applies to the GPU
inference/data-collection phase only** (Stage 1 plus, if reached, Stage 2):
abort at 55 min of GPU-phase wall time, report INCOMPLETE, and never
present partial averages as complete. Worst-case-plus-overhead leaves 2.3
min to abort and 5 min to the 60-min cap. Single-GPU GPU-active time cannot
exceed wall time; hence the wall fail-safe bounds GPU-active ≤0.92
GPU-hour. Planned pynvml utilization sampling (10 s) and GPU-second
integration must be recorded in the manifest; if unavailable, the wall
fail-safe enforces the cap. Wall time is never called measured GPU-active
time.

**Budget request (NOT authorization): ≤1.0 aggregate GPU-hour**, covering
only the GPU inference phase above, with the 55-min fail-safe and metering.

### 7.3 CPU null analysis — separate authorization (R5-G)

The SHUFFLE null (§4.5) is **CPU-only** and is **not** part of the GPU-hour
budget or the 55-minute wall-clock cap. It is separately authorized: a
two-replicate smoke test must first measure throughput, then a provisional
**four-CPU-hour timeout** applies, with checkpointing every 10 replicates
and no partial null ever presented as complete. The GPU and CPU phases are
never combined into a single wall-clock promise. **No CPU preflight or
smoke test is performed now.**

## 8. Confirmation-data policy

F2 SVAMP 300 is retired as fresh confirmation and is descriptive only.
MATH-500 remains a candidate only; it is untouched until an immutable
ID/revision/hash lock and overlap policy are committed. No confirmation
outcomes are used for policy selection. V1/F1/F2 results are
hypothesis-generating only; frozen artifacts remain unchanged.

## 9. Scope and novelty boundary

The candidate set remains B1 (cost floor), REF, B2 (dev-selected anchor,
not a universal best), B3, and B0. BEST-FIXED follows §4.3 step 5.
Greedy decoding and cached completions support paired comparisons; any
retrospective oracle is exploratory and non-deployable.

Plain embedding+MLP TACC remains PIVOT. DEFLECT and MEMROUTE remain
hypotheses whose novelty is **NOT CLEARED**. No "first" or "no prior work"
claim is made. All gating language is **pre-specified and commit-locked
before LEVAL inference**, not external preregistration.
