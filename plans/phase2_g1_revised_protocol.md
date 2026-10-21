# Phase-2 G1 — Revised Learnability & Pilot Protocol v2 (DOCUMENT ONLY, 0 GPU)

Date: 2026-10-21 (v2: repairs after Planner R1)
Authority: `plans/phase2_planner_review_r1.md` (blocking issues B1–B3 +
additional checks), `plans/phase2_g1_pilot_repair_prompt.md`.
This document REPLACES `phase2_g1_revised_protocol.md` v1 where they
conflict. No experiment here is authorized; §8 is a design + budget
request only.

---

## 1. Leakage-free GSM8K train partitions (B, B1-repaired)

GSM8K train (7,473 items) is split into four **disjoint, hash-locked**
partitions by fixed-seed shuffle over normalized-question hashes,
committed before any controller work:

| Partition | Share | ~Items | Role |
|---|---|---|---|
| `BANK` | 40% | ~2,989 | episodic exemplar bank content ONLY; never labeled, never evaluated as targets |
| `FIT` | 25% | ~1,868 | label matrix for fitting predictors; candidate fixed-config selection (cross-fit) |
| `TUNE` | 15% | ~1,121 | threshold/hyperparameter selection (δ, τ, feature set, predictor class); λ sensitivity |
| `LEVAL` | 20% | ~1,495 | **locked pilot evaluation** — used exactly once for the confirmatory D1/D2 comparison |

Rules:
- During label collection for any item, the memory bank contains **BANK
  items only** — a labeled item's own answer can never be retrieved.
- **Cross-fitting discipline (B1 fix):** best-fixed-config selection and
  predictor fitting happen on FIT (with k-fold cross-fitting inside
  FIT∪TUNE for model/feature choices); δ/τ/λ choices are made on TUNE;
  the confirmatory comparison (feature-policy vs best-fixed) is computed
  **once** on LEVAL, which neither side was selected on. Nothing tuned on
  VAL/LEVAL is refit using it.
- Overlap guards (CPU, pre-pilot): exact + normalized near-duplicate
  checks across all four partitions and against every evaluation split
  ever used (GSM8K test[0:100] dev, V1 holdout, F2-locked SVAMP 300);
  partition hashes committed; any hit → exclusion + documented.
- Exploratory vs confirmatory is explicit: FIT/TUNE analyses are
  exploratory; only the pre-registered LEVAL contrast is confirmatory
  (pilot-scale).

## 2. Confirmation-data policy (unchanged, A)

- F2 SVAMP 300: **retired as fresh confirmation**; descriptive only.
- MATH-500: **candidate only** — no fetch, no adapter probing on its
  content, no result access until an immutable ID/revision/hash lock and
  overlap policy are committed. Public-pretraining contamination caveat
  stands.

## 3. Locked candidate configuration set

| Config | Role |
|---|---|
| B1 (none, CoT d3) | **cost floor** — deferral target and primary reference |
| REF (recency k=3, 1 exemplar, CoT d3) | Phase-1 search-selected anchor |
| B2 (recency k=3, 3 exemplars, CoT d3) | strong manual anchor (**dev-selected on inspected data; never called global best**) |
| B3 (retrieval tf-cosine, CoT d3) | retrieval-memory axis |
| B0 (none, direct) | cheap degenerate anchor |

"Best fixed config" for the confirmatory comparison = the config with the
highest FIT∪TUNE cross-fitted utility, selected **without access to LEVAL**.

## 4. Utility definition (B2 fix — explicit per-item units)

Per item i under config c:

```
u_i(c) = correct_i(c) − λ · (prompt_tokens_i(c) + completion_tokens_i(c)) / 10,000
```

Dataset utility = mean over items (so the accuracy term and the token
term are on commensurate per-item scales; aggregate token totals are
always reported separately alongside).

**λ algebra and status.** λ = 0.1 makes 1 percentage point of accuracy
(0.01) exactly offset 1,000 total tokens (0.1·λ·1,000/1,000 = λ·0.1 =
0.01). This policy value was chosen **with awareness of Phase-1 cost
spreads** (e.g. F2 B1↔REF ≈ 170 tokens/item gap at equal accuracy), so it
is labeled **exploratory-informed**, not an independently specified
deployment price. Consequence: raw accuracy, raw prompt/completion tokens,
and the accuracy–token Pareto are the **primary** metrics; utility at
λ = 0.1 is a secondary decision metric, and λ sensitivity is reported on
TUNE only — never re-fit on LEVAL or confirmation data.

## 5. Learnability diagnostics (C, G + R1-§4 repair)

**D1 — Retrospective opportunity (optimistic by construction).**
Per-item hindsight best-config utility minus best-constant-config utility,
on FIT only; mean gap, bootstrap CI, tie rates, share of items whose top-2
configs are within noise. Labeled an optimistic, non-deployable upper
bound; never evidence of attainability.

**D2 — Out-of-sample predictability of utility differences (confirmatory
gate).** Predictor maps pre-inference features (frozen embedding +
length/numeric-density; ablations: feature-only, length/number-only) to
pairwise utility differences Δû(cfg, best-fixed) fit on FIT, thresholds on
TUNE. Confirmatory test on LEVAL, exactly once:

- feature-policy utility must exceed **best-fixed-config** utility
  (selected cross-fitted without LEVAL access) with a paired bootstrap CI
  excluding 0 — beating B1 alone is **not sufficient** if REF/B2/B3 is the
  stronger fixed comparator on FIT/TUNE;
- must beat the **shuffled-label negative control** (chance);
- majority-action and random-policy baselines reported;
- D1 oracle gap reported alongside for optimism calibration.

Pre-registered D2 pass = both conditions. Anything else = pilot null,
reported as such.

## 6. Embedding/controller overhead accounting

The frozen query encoder (e.g. BGE/MiniLM-class) is precomputed once per
partition; its wall-clock seconds and peak memory are logged and reported
as **encoder seconds** — never converted into or equated with LLM tokens.
Controller inference latency per routing decision is likewise reported in
ms/decision. Deployment-cost tables show: LLM prompt tokens, LLM
completion tokens, encoder seconds, controller ms — as separate columns.

## 7. Decoding noise and oracle discipline (unchanged)

Greedy deterministic decoding; cached completions reused to keep
comparisons paired; residual nondeterminism documented. Hindsight oracle
appears only in D1, always labeled optimistic/non-deployable.

## 8. Tiny TRAIN-only pilot v2 — design + budget request (NOT executed)

**Throughput basis (from existing logs, no new benchmark):** F1 GSM8K dev
cells at 1.5B ran ≈ 55 s per 100 items per config (worst case, B1); F2
SVAMP ran ≈ 24 s per 100 items. Budgeting uses the **conservative 55
s/100/config**.

**v1 error (corrected):** v1 estimated "35–55 min" for 12,000 generations,
misreading 55 s as per-config total rather than per 100 items. Correct
arithmetic: 12,000 / 100 × 55 s = 6,600 s ≈ 110 min ≈ **1.83 GPU·h** —
the v1 ≤ 0.5 GPU·h cap was not defensible and is withdrawn.

**v2 design (precision-motivated downsize):** 5 configs × **800 FIT+TUNE
items** for label fitting + 5 × **300 LEVAL items** for the confirmatory
contrast (LEVAL evaluated once). Generations: 5 × 1,100 = 5,500.

- Compute: 5,500 / 100 × 55 s = 3,025 s ≈ 50.4 min ≈ **0.84 GPU·h**;
  +15% overhead (bank build, cache misses) ≈ 0.97 → **budget request:
  ≤ 1.0 aggregate GPU-hour (hard cap)**.
- Precision rationale: paired per-item utility differences at n = 300
  (LEVAL) give bootstrap CI half-width ≈ ±2–3pp (binary-dominant term);
  the Phase-1 dev-side effects motivating TACC were ~10pp, so the pilot
  can detect effects of the motivating magnitude, and a null at ±3pp is
  still decision-relevant (proceed only to larger designs if the point
  estimate exceeds the detectable band).
- Preflight: partition hashes committed; overlap guards green; config set
  locked; λ locked; no confirmation-data access.
- Stop rules: guard failure → STOP; budget breach → STOP (no partial
  averages reported as complete); D2 null → STOP, report the null.

## 9. Historical-data classification (unchanged standing rule)

V1/F1/F2 numbers are descriptive/hypothesis-generating only. Frozen V1/V2
paper artifacts untouched.
