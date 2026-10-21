# Phase-2 G1 — Revised Learnability & Pilot Protocol (DOCUMENT ONLY, 0 GPU)

Date: 2026-10-21
Authority: `plans/phase2_planner_review_r0.md` (corrections A–G),
`plans/phase2_r5_g1_kimi_prompt.md` (items 1–9).
This document REPLACES the G1-relevant parts of
`plans/phase2_experiment_design.md` where they conflict. No experiment in
this document is authorized; the pilot (§8) is a design + budget request.

---

## 1. Leakage-free GSM8K train partition (correction B)

GSM8K train (7,473 items) is split into three **disjoint, hash-locked**
partitions, derived by a fixed-seed shuffle over normalized-question
hashes, committed before any controller work:

| Partition | Share | Purpose | Hard rule |
|---|---|---|---|
| `BANK` | ~40% | episodic-memory exemplar bank content | items here NEVER receive controller labels and are never evaluated as targets |
| `LABEL` | ~40% | controller label matrix (config × item outcomes) | during label collection for item i, the memory bank is restricted to `BANK` only — i's own answer can never be retrieved |
| `VAL` | ~20% | controller model selection, λ/δ/τ setting, bootstrap CIs | never used for controller weight fitting |

Guards (CPU tests, pre-pilot): exact-text and normalized near-duplicate
checks across all three partitions AND against every evaluation split ever
used (GSM8K test[0:100] dev, V1 holdout test[100:1319], SVAMP locked 300);
partition hashes committed; any hit → exclusion + documented.

## 2. Confirmation-data policy (correction A)

- **F2 SVAMP 300 is RETIRED as "fresh confirmation".** It was inspected in
  F2 and motivated Phase-2 hypotheses; any future use is
  **descriptive / hypothesis-generating only**, explicitly labeled as such.
- **New confirmation candidate: MATH-500** (public MATH test subset) —
  candidate only. Before ANY inference on it: pin dataset revision, freeze
  all 500 IDs + file SHA-256, run exact/normalized overlap checks against
  GSM8K (train+test) and SVAMP, unit-test a Body+Question-style adapter on
  synthetic fixtures, and commit the lock. Pretraining contamination cannot
  be ruled out for MATH-500; this is stated as a limitation, and MATH-500
  is dropped if its adapter cannot be made deterministic.
- Primary endpoints on the locked confirmation set: **utility (TACC vs best
  fixed at matched accounting), raw accuracy, total prompt+completion
  tokens** — reported separately, never collapsed into only a scalar.

## 3. Locked candidate configuration set (correction: no "global best" language)

Small, pre-registered, all Phase-1-validated:

| Config | Role |
|---|---|
| B1 (none, CoT d3) | **cost floor** — primary reference for net-utility claims |
| REF (recency k=3, 1 exemplar, CoT d3) | Phase-1 search-selected anchor |
| B2 (recency k=3, 3 exemplars, CoT d3) | strong manual anchor — described as *dev-selected on inspected data*, never "global best" |
| B3 (retrieval tf-cosine, CoT d3) | retrieval-memory axis |
| B0 (none, direct) | cheap degenerate anchor |

(≤5 configs; final list locked in the pilot preflight.)

## 4. Learnability diagnostics (corrections C, G — replaces "argmax frequency")

Both diagnostics on **training-side data only** (LABEL fit, VAL eval),
with paired bootstrap CIs (fixed seed):

**D1 — Retrospective opportunity (optimistic by construction).**
Per-item hindsight best-config utility minus best-constant-config utility
under identical total-cost accounting; report mean gap, CI, tie rate, and
the share of items whose top-2 configs are within noise. Explicitly labeled
an *optimistic, non-deployable upper bound subject to selection noise* —
never evidence that a router can attain it.

**D2 — Out-of-sample predictability of utility DIFFERENCES (the real gate).**
Fit a cheap predictor from pre-inference features (embedding +
length/numeric-density; feature-only variants) to pairwise utility
differences Δu(cfg, B1) on LABEL; evaluate on held-out VAL:

- vs **shuffled-label negative control** (must be at chance);
- vs **majority-action** and **random-policy** baselines;
- vs **length/number-feature-only** predictors;
- vs the D1 oracle gap (optimism calibration).

**Learnability threshold (pre-specified):** D2 passes only if the
feature-based selector's VAL utility exceeds best-fixed-config utility with
a paired bootstrap CI excluding 0, AND beats shuffled-label controls. F1/F2
historical pairs are hypothesis-generating input to this design, not
evidence.

## 5. Utility, λ, units, and overhead (correction E)

- Unit of cost: **tokens** (prompt + completion separately metered). The
  controller's own compute is reported in its own units (encoder latency,
  FLOPs) and never conflated with LLM tokens.
- `utility = accuracy − λ · tokens_norm`, where `tokens_norm =
  total_tokens / 10,000` (scale fixed, not fit).
- **λ is derived before any outcome is seen**, from a deployment framing:
  λ = (acceptable price of one additional correct answer) / (token scale).
  Pilot default λ = 0.10 per 10k tokens (i.e., 1pp accuracy ≙ 1,000
  tokens), chosen on Phase-1 cost spreads; a λ-sensitivity check is allowed
  on VAL only, never on confirmation data.
- Report raw accuracy, raw tokens, and the Pareto set alongside utility.

## 6. Domain-tag correction (correction F)

GSM8K-only training has a constant domain tag → a learned domain router is
vacuous. Resolution: the domain-tag baseline is **removed as a learnable
baseline**. If deployment-time domain tags are assumed available, a
rule-based tag→config lookup computed from train-side per-domain
statistics is kept only as a **descriptive, oracle-like reference**,
explicitly separated from learned adaptation claims.

## 7. Decoding noise and oracle discipline (correction G)

- Greedy deterministic decoding is the default; residual nondeterminism
  (batching/kernel) is documented as a limitation, and cached completions
  are reused rather than regenerated to keep comparisons paired.
- The per-item hindsight oracle appears only in D1, always labeled
  optimistic/non-deployable; no inference-time outcome information may
  enter any deployable controller input.

## 8. Tiny TRAIN-only GPU pilot — design + budget request (NOT executed)

Scope: D1 + D2 diagnostics only, on GSM8K train partitions; no
confirmation data, no controller training beyond the cheap diagnostic
predictors.

| Quantity | Estimate |
|---|---|
| Config × item evaluations | 5 configs × 2,400 LABEL items ≈ 12,000 generations (batched, 1.5B) |
| Wall time @ 1.5B, batch 32 | ~35–55 min total (F1 timing: ~55s/100 items/config incl. memory build) |
| **GPU budget request** | **≤ 0.5 aggregate GPU-hours** (hard cap; stop-and-report on breach) |
| Preflight | partition lock hashes committed; overlap guards green; cache/test exclusions green; configs locked; λ locked |
| Stop rules | any partition/overlap failure → STOP; budget breach → STOP with partial-results-not-reported rule; D2 null → STOP, report null |

Deliverable of the pilot (if later authorized): D1/D2 numbers with CIs,
tie rates, shuffled-label controls — a binary learnability decision
(GO/NO-GO for controller training), nothing more.

## 9. Historical-data classification (standing rule)

All V1/F1/F2 numbers used in Phase-2 documents are marked
**descriptive/hypothesis-generating**. They may motivate designs but never
appear as confirmation evidence for TACC. The frozen V1/V2 paper artifacts
are untouched by this track.
