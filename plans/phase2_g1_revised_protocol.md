# Phase-2 G1 — Learnability & Pilot Protocol v4 (DOCUMENT ONLY, 0 GPU)

Date: 2026-10-21 (v4: repairs after Planner R3; supersedes v3 where they
conflict)
Authority: `plans/phase2_planner_review_r3.md` (R3-A…R3-D),
`plans/phase2_g1_pilot_repair_prompt_r3.md`.
Nothing here is authorized compute. All locks described are **PLANNED, not
yet created**; the immutable artifacts are a future, separately-authorized
CPU-preflight deliverable.

---

## 1. Partitions, deterministic algorithms, and pilot subsets (R3-B/D)

### 1.1 Planned partition-generation algorithm (fully defined; NOT executed)

- **ID normalization:** use the dataset's stable source ID field when it
  exists; otherwise `id = sha256_hex(NFC(question_text))` where the text is
  NFC-normalized, leading/trailing whitespace stripped, and internal
  whitespace runs collapsed to a single space. Empty/duplicate IDs cause
  preflight FAILURE, never silent repair.
- **Partition assignment (namespace `phase2-partition-v1`):** sort all
  7,473 GSM8K-train items by
  `sha256(norm_id || "|partition|" || "phase2-partition-v1")` ascending;
  assign in order: first 2,989 → `BANK`, next 1,868 → `FIT`, next 1,121 →
  `TUNE`, remaining 1,495 → `LEVAL`. Counts: 2,989+1,868+1,121+1,495 =
  **7,473** exactly.
- **Pilot subsets (namespace `phase2-subset-v1`):** within each partition,
  sort by `sha256(norm_id || "|subset|" || "phase2-subset-v1")`, take the
  first n: `FIT_pilot` = **500**, `TUNE_pilot` = **200**, `LEVAL_pilot` =
  **300**. (TUNE gets 200 not 300 because it selects only scalar thresholds
  and a feature-set bit — low-dimensional decisions; FIT keeps the larger
  share because predictor fitting is variance-limited.)
- **Future lock artifacts (CPU preflight, separately authorized):** source
  file path + revision + SHA-256; per-partition ordered ID lists + SHA-256;
  per-subset ordered ID lists + SHA-256; pairwise-intersection proofs (must
  be empty); exact + normalized near-duplicate checks against all
  historical evaluation splits (GSM8K test, V1 holdout, F2-locked SVAMP
  300). All committed before any GPU. **None exist as of this round.**

### 1.2 Roles (single, non-overlapping)

| Partition | Role — and ONLY this role |
|---|---|
| BANK | exemplar bank content; never labeled, never a target |
| FIT_pilot | predictor fitting; 5-fold cross-fitting INSIDE FIT_pilot for the predeclared (predictor class, regularization) grid |
| TUNE_pilot | feature-set choice, scalar thresholds (δ, τ), λ sensitivity — with predictor class/regularization already frozen by FIT |
| LEVAL_pilot | one-time confirmatory evaluation only |

Bank rule: labels for any item are collected with the memory bank
restricted to BANK items only. LEVAL_pilot never participates in fitting,
tuning, threshold or candidate selection, or resampling.

## 2. Single ordered selection procedure (R3-C — all frozen before LEVAL)

**Predeclared candidate grids:**
- Predictor class: {ridge regression on Δu, logistic regression over
  best-config label, gradient-boosted trees (max_depth=3, n_est=100)};
  regularization α ∈ {0.1, 1, 10}.
- Feature sets: `F0` = {question length, numeric-density};
  `F1` = F0 + frozen query embedding.
- Thresholds: δ ∈ {0.0, 0.005, 0.01, 0.02};
  τ ∈ {TUNE_pilot shift-score percentiles 90/95/99}.
- λ: primary 0.1; sensitivity {0.05, 0.2} reported on TUNE_pilot only.

**Ordered procedure:**
1. **FIT_pilot (5-fold cross-fitting):** select (predictor class, α) by
   mean held-out Δu-prediction R². Feature set is NOT chosen here.
2. **TUNE_pilot:** with (class, α) frozen, select feature set ∈ {F0, F1}
   and (δ, τ) by TUNE_pilot utility; produce the λ-sensitivity report.
3. **BEST-FIXED selection:** the fixed configuration with the highest
   cross-fitted utility on FIT_pilot — this rule alone selects.
   TUNE_pilot computes a confirmation ranking that cannot change the
   selection; any disagreement is reported, not acted on.
4. **LEVAL_pilot:** evaluated once, per the frozen gate (§3).

**Deterministic tie-breaks everywhere:** prefer lower complexity
(ridge < logistic < GBT; larger α; F0 < F1; smaller δ; smaller τ), then
lexicographic order of the grid key. No decision uses LEVAL_pilot.

## 3. D2 gate — complete pre-specified battery (R3-A)

**Frozen before LEVAL_pilot inference:** candidate policy, (class, α),
feature set, (δ, τ), λ, all seeds, this gate text. No metric, threshold,
or test may be changed after seeing LEVAL outputs.

**Resampling conventions (global):** bootstrap resample unit = the
LEVAL_pilot item (n=300, resampled with replacement); 10,000 resamples;
seed `S0 = 20261021` for the primary stream (control streams derive from
S0 as below). Ties in utility are exact float ties and flow through the
bootstrap naturally. Missing values: not expected (every config evaluated
on every LEVAL item); if any item is missing for any config, that item is
dropped from ALL contrasts (complete-pair rule), predeclared here.

| # | Contrast | Pre-specified pass rule |
|---|---|---|
| 1 | candidate − BEST-FIXED (primary) | paired per-item utility difference; 95% paired-bootstrap CI (10,000 resamples, seed S0) **lower bound > 0** |
| 2 | candidate vs SHUFFLE | 1,000 shuffles of FIT_pilot labels (seeds S0+1+k), each refit and scored on LEVAL_pilot; pass ⟺ candidate utility ≥ 95th percentile of the shuffled distribution, percentile computed with mid-rank tie handling: `(#{u_shuf < u_cand} + 0.5·#{u_shuf = u_cand}) / 1000 ≥ 0.95` |
| 3 | candidate vs RANDOM | 1,000 uniform-random per-item config assignments (seeds S0+1001+k) scored on LEVAL_pilot; same 95th-percentile mid-rank rule |
| 4 | candidate − MAJORITY | MAJORITY = always the most frequent per-item best action on FIT_pilot; paired per-item utility difference on LEVAL_pilot; 95% paired-bootstrap CI (seed S0) **lower bound > 0** |
| 5 | candidate − SIMPLE-FEAT | SIMPLE-FEAT = identical pipeline restricted to F0 (length + numeric density); paired per-item utility difference on LEVAL_pilot; 95% paired-bootstrap CI (seed S0) **lower bound > 0** |

**Accuracy component:** exact McNemar (candidate vs BEST-FIXED) reported
secondary to the primary utility gate; never substitutes for it.

**Multiplicity:** intersection–union gate — **D2 PASS ⟺ contrasts 1–5 ALL
pass.** No per-contrast α adjustment is needed under IUT (each test at
level 0.05). Secondary/exploratory contrasts are reported unadjusted and
labeled as such.

## 4. Utility definition (unchanged from v3)

`u_i(c) = correct_i(c) − λ × (prompt_tokens_i(c) + completion_tokens_i(c)) / 10,000`;
dataset utility = mean over items. λ × 1,000 / 10,000 = 0.1 × 0.1 = 0.01
= 1pp accuracy. λ = 0.1 is exploratory-informed (Phase-1-spread aware);
raw accuracy, raw prompt/completion tokens, and the Pareto are primary;
utility is the secondary decision metric.

## 5. Precision: scenarios, not promises (unchanged from v3)

Unconditional precision claims remain withdrawn. Discordance scenarios
(q=5/10/20/40% → ±2.5/3.6/5.1/7.2pp accuracy-scale half-width at n=300);
utility CIs are wider due to token variance. F2 discordance references
(16.7%/22.7%) are planning-only and transfer-limited. **The pilot is a
learnability screen with uncertain power**; no detection guarantee.

## 6. Budget, abort rule, and accounting (R3-B — coherent plan)

**Basis (existing logs only; no new benchmark):** 55 s/100 items/config =
worst observed F1 wall-clock inside `evaluate()` (prompt + batched
generation + scoring), model loaded once per process, fresh caches (misses
included), memory-bank build excluded (timed outside; CPU-scale).
Per-config observed rates (s/100): B0 6.2, B2 27.3, REF 27.7, B3 26.9,
B1 54.5.

**Planned evaluations: 5,000** = 5 configs × (500 FIT + 200 TUNE + 300
LEVAL).

- Worst case: 5,000/100 × 55 = 2,750 s = 45.8 min; +15% overhead
  (bank build + cache effects; incremental, not double-counted) =
  **52.7 min ≈ 0.88 wall-hours**.
- Expected (per-config observed rates): ≈ 24 min.

**Coherent guard set (the v3 45-min abort is withdrawn):**
- **Wall-clock fail-safe: abort at 55 min cumulative**, report INCOMPLETE
  (no partial averages presented as complete). Margins: worst-case-plus-
  overhead (52.7) → abort (55): 2.3 min; abort (55) → hard cap (60): 5
  min. The 2.3-min margin is thin by construction but the 52.7-min figure
  is itself an all-configs-at-slowest-observed bound; expected usage is
  ~24 min.
- **GPU-hour accounting (honest):** F1/F2 never metered GPU-active time;
  wall-clock is the only reliable legacy proxy. Single-GPU process ⇒
  GPU-active ≤ wall-clock, so the 55-min wall fail-safe bounds GPU-active
  ≤ 0.92 GPU·h < 1.0 cap. **Planned instrumentation (not yet run):**
  pynvml utilization sampling at 10 s intervals with a GPU-second
  integral in the run manifest; if GPU-active telemetry fails, the
  wall-clock fail-safe alone enforces the cap. Wall-clock is never
  reported as GPU-active time.

**Budget request (proposal, NOT authorization): ≤ 1.0 aggregate
GPU-hour**, hard cap, with the 55-min wall fail-safe and planned GPU-active
metering.

## 7. Confirmation-data policy (unchanged)

F2 SVAMP 300: retired as fresh confirmation (descriptive only).
MATH-500: candidate only; untouched until an immutable lock exists.

## 8. Locked candidate configuration set (unchanged)

B1 (cost floor; deferral target), REF, B2 (dev-selected anchor — never
"global best"), B3, B0. BEST-FIXED selected per §2 step 3.

## 9. Standing rules (unchanged)

Greedy deterministic decoding; cached completions reused for pairing;
hindsight oracle (D1) optimistic/non-deployable, FIT-only. V1/F1/F2
numbers are descriptive/hypothesis-generating only; frozen V1/V2 artifacts
untouched. All gating is **"pre-specified and commit-locked before LEVAL
inference"**; no external preregistration exists or is claimed.
