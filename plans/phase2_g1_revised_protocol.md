# Phase-2 G1 — Revised Learnability & Pilot Protocol v3 (DOCUMENT ONLY, 0 GPU)

Date: 2026-10-21 (v3: repairs after Planner R2; supersedes v2 where they
conflict)
Authority: `plans/phase2_planner_review_r2.md` (R2-A…R2-F),
`plans/phase2_g1_pilot_repair_prompt_r2.md`.
Nothing here is authorized compute. All partition/sample locks described
below are **PLANNED, not yet created**: the immutable lock artifacts are a
future, separately-authorized CPU-preflight deliverable.

---

## 1. Planned partitions and exact pilot subsets (R2-B)

GSM8K train (7,473 items) → four disjoint partitions (planned shares):

| Partition | Planned share | Planned count | Role |
|---|---|---|---|
| `BANK` | 40% | ~2,989 | exemplar bank content ONLY; never labeled, never a target |
| `FIT` | 25% | ~1,868 | predictor fitting (with k-fold cross-fitting **inside FIT only**) |
| `TUNE` | 15% | ~1,121 | scalar thresholds (δ, τ), feature-set choice, λ sensitivity |
| `LEVAL` | 20% | ~1,495 | locked pilot evaluation reserve; touched once, at the end |

**Pilot subsets (planned, deterministic):**

- `FIT_pilot`: **500** items, drawn from FIT.
- `TUNE_pilot`: **200** items, drawn from TUNE. (Justification for
  500+200 instead of proportional 500+300: TUNE selects only scalar
  thresholds (δ, τ) and a feature-set bit — low-dimensional decisions for
  which 200 items give adequate resolution; FIT keeps the larger share
  because predictor fitting is variance-limited. Budget margin analysis in
  §8.)
- `LEVAL_pilot`: **300** items, drawn from the ~1,495-item LEVAL reserve,
  selected and hash-locked **before any model outputs are generated**.

**Planned deterministic selection algorithm (for the future CPU
preflight):** normalize IDs (exact source ID string, NFC, stripped) →
sort each partition by `sha256(normalized_id || "|" || SEED)` with
`SEED = 20261021` → take the first n. The CPU preflight commits, per
subset: exact ID list, SHA-256 of the ordered ID list, the partition
hashes, and the overlap-guard results. None of these artifacts exist yet;
this round creates none of them.

**Ordered pipeline (ambiguity fix):**
1. FIT_pilot only: fit predictors; model-class/feature choices by k-fold
   cross-fitting **inside FIT_pilot**.
2. TUNE_pilot only: choose δ, τ, λ-sensitivity, feature set.
3. Best-fixed-config selection: highest cross-fitted utility on
   FIT_pilot, confirmed on TUNE_pilot; **no LEVAL access at any point**.
4. One-time evaluation on LEVAL_pilot. No LEVAL-based refitting,
   threshold adjustment, candidate selection, or result-driven
   resampling — ever.

Bank rule unchanged: labels for any item are collected with the memory
bank restricted to BANK items only (self-answer can never be retrieved).
Overlap guards (exact + normalized near-duplicate) across partitions and
against all historical evaluation splits are a preflight hard gate.

## 2. Confirmation-data policy (unchanged)

F2 SVAMP 300: retired as fresh confirmation (descriptive only).
MATH-500: candidate only; untouched until an immutable
ID/revision/hash lock exists. Not accessed in this round.

## 3. Locked candidate configuration set (unchanged)

B1 (cost floor; deferral target), REF, B2 (dev-selected anchor — never
"global best"), B3, B0. Best-fixed for the confirmatory contrast is
selected per §1 step 3.

## 4. Utility definition (R2-E algebra fix)

Per item i under config c:

```
u_i(c) = correct_i(c) − λ × (prompt_tokens_i(c) + completion_tokens_i(c)) / 10,000
```

Dataset utility = mean over items; aggregate token totals are always
reported separately.

**λ algebra:** 1,000 extra tokens cost `λ × 1,000 / 10,000 = 0.1 × 0.1 =
0.01` utility = exactly one percentage point of accuracy. So λ = 0.1
implements "1pp ≙ 1,000 tokens". λ = 0.1 is **exploratory-informed**
(chosen with awareness of Phase-1 cost spreads, not an independently
specified deployment price); raw accuracy, raw prompt/completion tokens,
and the accuracy–token Pareto remain the **primary** metrics; utility is
a secondary decision metric; λ sensitivity on TUNE_pilot only.

## 5. D2 gate — full pre-specified comparison battery (R2-A)

**Frozen before LEVAL_pilot:** the candidate policy (M1 or M2), all
thresholds (δ, τ), λ, feature set, all random seeds, and this gate text.
Nothing is chosen after inspecting LEVAL_pilot.

**Baselines the candidate must beat (all on LEVAL_pilot):**
1. `BEST-FIXED`: best fixed configuration, selected train-side only
   (§1 step 3);
2. `SHUFFLE`: shuffled-label negative control — 1,000 shuffles of the
   FIT_pilot labels, shuffle seeds derived deterministically from
   `SEED+1`; candidate must exceed the 95th percentile of the shuffle
   utility distribution;
3. `RANDOM`: uniform random config per item, 1,000 policy draws, seeds
   from `SEED+2`; candidate must exceed the 95th percentile;
4. `MAJORITY`: action-frequency policy (always the most frequent
   best-config action on FIT_pilot) — applicable to this discrete action
   space;
5. `SIMPLE-FEAT`: predictor using only length + numeric-density features
   (same training pipeline) — the candidate's full-feature model must beat
   it.

**Statistics:** primary contrast = candidate vs BEST-FIXED paired
per-item utility difference on LEVAL_pilot; paired bootstrap 95% CI,
10,000 resamples, seed `SEED+3`; binary accuracy component additionally
gets exact McNemar. **Multiplicity:** hierarchical intersection–union
gate — the primary contrast must have CI excluding 0 **and** each of the
four control contrasts (2–5) must pass its pre-specified rule; all must
pass for D2 = PASS. Secondary contrasts are reported unadjusted and
labeled exploratory.

**D2 PASS ⟺ all five conditions met.** Anything else = pilot null,
reported as such.

## 6. Precision: scenarios, not promises (R2-C)

The unconditional "n=300 gives ±2–3pp" claim is **withdrawn**. For a
near-zero paired binary difference, the approximate 95% CI half-width is
`1.96 × sqrt(q / 300)` where q is the paired discordance rate:

| discordance q | approx. half-width |
|---|---|
| 5% | ±2.5pp |
| 10% | ±3.6pp |
| 20% | ±5.1pp |
| 40% | ±7.2pp |

Utility CIs are **wider** than these accuracy-only illustrations because
token-cost variance enters the difference.

Planning-only reference (transfer-limited, different benchmark, label:
**hypothesis-generating, not evidence**): the locked F2 SVAMP pairs showed
discordance 50/300 ≈ 16.7% (REF vs B2) and 68/300 ≈ 22.7% (REF vs B1),
which under the approximation above correspond to roughly ±4.6pp and
±5.3pp accuracy-scale half-widths. There is no guarantee GSM8K-train
discordance is similar.

**Honest characterization:** this pilot is a **learnability screen with
uncertain power**. If the true LEVAL_pilot discordance is ≈20%, effects
smaller than ~5pp in accuracy scale cannot be resolved; the screen can
detect effects of the ~10pp magnitude seen dev-side in Phase-1, and a null
at that resolution redirects the project (see risk R1). No detection of a
specific effect size is guaranteed.

## 7. Decoding noise and oracle discipline (unchanged)

Greedy deterministic decoding; cached completions reused for pairing;
hindsight oracle (D1) labeled optimistic/non-deployable, FIT-only.

## 8. Budget reconciliation (R2-D — from existing logs only, no new runs)

**What the 55 s/100 figure includes (verified against
`f1_results/f1_summary.csv` and runner code `src/scripts/f1_run.py`):**

- It is **per 100 items, per config, wall-clock**, measured inside
  `evaluate()` (prompt build + batched generation + scoring).
- It comes from the slowest observed F1 GSM8K 1.5B cell (B1, 54.5 s).
  Observed per-config rates (s/100 items): B0 6.2, B2 27.3, REF 27.7,
  B3 26.9, B1 54.5.
- **Excluded:** memory-bank construction (executed and timed *outside*
  `evaluate()`; CPU-only retrieval over ≤48 calibration items,
  subsecond-to-seconds scale).
- **Included:** first-run cache misses (F1/F2 used fresh caches).
- **Accounting gap (stated, not hidden):** wall-clock vs GPU-active time
  was not separately metered in F1/F2. The pilot must add GPU-active
  metering; until then, wall-clock is the conservative upper proxy.

**Arithmetic (planned 5,000 generations = 5 configs × (500 FIT + 200 TUNE
+ 300 LEVAL)):**

- Worst case (every config at the slowest observed 55 s/100):
  5,000/100 × 55 = 2,750 s ≈ 45.8 min ≈ **0.76 GPU·h**; +15% for
  bank-build/cache effects (incremental, **not** double-counted, since
  bank build is outside the 55 s figure) ≈ **0.88 GPU·h**.
- Expected (per-config observed rates): ≈ 1,420 s ≈ 24 min ≈
  **0.40 GPU·h**.

**Margin judgment:** worst-case 0.88 h leaves ~7 min under a 1.0 h cap —
thin but workable **only with** an instrumented early-abort rule: abort at
45 min cumulative wall-clock, report INCOMPLETE (no partial averages).
The v2 design (5,500 gens, 0.97 h worst case, ~2 min margin) is judged
**not to leave adequate margin** and is superseded by the 5,000-gen
design above.

**Budget request (NOT authorized): ≤ 1.0 aggregate GPU-hour, hard cap,
with GPU-active metering and the 45-min abort rule.** All figures are
estimates from existing logs; nothing here is an execution permission.

## 9. Historical-data classification (unchanged)

V1/F1/F2 numbers are descriptive/hypothesis-generating only. Frozen V1/V2
artifacts untouched. Terminology: all gating language is **"pre-specified
and commit-locked before LEVAL inference"**; no external preregistration
exists or is claimed.
