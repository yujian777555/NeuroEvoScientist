# Phase-2 Experiment Design — TACC Evaluation

Date: 2026-10-14
Status: DESIGN ONLY. No GPU/GPU-hours authorized by this document; execution
requires Planner gate approval per step.
Companion: `plans/phase2_controller_design.md`, `plans/phase2_risk_analysis.md`.

---

## 0. Hypotheses (pre-specified, falsifiable)

- **H1 (within-task adaptivity).** Within one benchmark, the per-item best
  configuration varies enough that a learned controller can beat the best
  fixed configuration on utility (accuracy − λ·tokens).
- **H2 (cross-benchmark transfer).** A controller trained on GSM8K assigns
  configurations on SVAMP/MATH whose utility exceeds (a) the fixed
  Phase-1 REF and (b) a random controller.
- **H3 (cost-awareness).** At matched accuracy, TACC uses fewer total
  tokens than the fixed strong CoT baseline.

Any hypothesis may fail; failure is a reportable answer consistent with
Phase-1's theme (adaptation claims require cross-benchmark verification).

---

## 1. Baselines (fixed set, locked before any experiment)

| # | Name | Definition | Role |
|---|---|---|---|
| B-fix | **Fixed REF** | Phase-1 GSM8K-selected config (recency k=3, 1 exemplar, CoT d3, full) | static-search reference |
| B-man | **Best manual config** | B2 (recency k=3, 3 exemplars, CoT d3) — strongest CoT-matched preset from F1 | strong hand baseline |
| B-min | **Cheapest adequate** | B1 (no memory, CoT d3) — F2 cost reference | cost floor |
| B-rand | **Random controller** | uniform random config per item from the same config set, fixed seed | conditioning-free lower bound |
| B-oracle | **Oracle controller** | per-item argmax over configs on the *test* set | upper bound; analysis only, never a claimable method |
| B-tag | **Domain-tag controller** | rule: domain tag → per-domain best config (from train only) | trivial conditioning baseline to beat |
| TACC | **Proposed** | learned task-features → config policy (Approach A, supervised utility) | proposed method |

All baselines use the identical frozen backbone (Qwen2.5-1.5B-Instruct,
revision locked), identical decoding, identical candidate config set, and
identical calibration bank rules (GSM8K train only for math tasks).

---

## 2. Datasets and splits

| Split | Dataset | Items | Use | Status |
|---|---|---|---|---|
| Train/calibration | GSM8K train | ≤ 7473 (label-matrix subset TBD) | controller labels + memory bank | existing local copy |
| Dev | GSM8K test[0:100] | 100 | controller model selection ONLY | reused from F1 (contaminated by selection — reported as such) |
| Test-1 | SVAMP test (locked) | 300 | primary cross-benchmark test | **reuse the committed F2 lock** (`v2_quality/fasttrack/confirmation_lock.json`); IDs/hashes unchanged |
| Test-2 | MATH subset (e.g. MATH-500) | 500 | second math transfer test | **new — requires a fresh pre-inference lock** (revision, IDs, hashes, adapter) before any use |
| Test-3 (optional) | PubMedQA holdout slice | 400 | non-math domain transfer | existing V1 locked split |

Rules: SVAMP lock is reused verbatim (same 300 IDs, same adapter, same
scorer). MATH is locked with the same protocol *before* any inference, and
if its preprocessing cannot be made deterministic and cheap, MATH is
dropped rather than improvised. SVAMP train and MATH train never enter any
bank or label matrix.

---

## 3. Metrics (accuracy alone is insufficient — Phase-1 lesson)

| Category | Metric | Definition |
|---|---|---|
| Performance | Accuracy | item-level binary; paired stats |
| Cost | Prompt + completion tokens | real tokenizer counts, per item and total (controller overhead reported separately) |
| Joint | Utility | `accuracy − λ · normalized_tokens`, λ pre-specified and locked |
| Transfer | Transfer gap | dev utility − test utility per method; negative-gap comparison across methods |
| Adaptivity | Regret-to-oracle | oracle utility − method utility (per dataset) |
| Robustness | Paired statistics | bootstrap 95% CI + exact McNemar (binary), fixed seed, contrasts pre-specified |
| Controller health | Selection distribution | per-config selection frequency; degenerate single-config output is reported, not hidden |

**Pre-specified primary contrasts (locked before experiments):**
1. TACC vs Fixed REF (utility, SVAMP) — primary.
2. TACC vs B-man (utility, SVAMP) — fairness anchor.
3. TACC vs B-rand (utility, SVAMP) — is conditioning needed at all?
MATH (if locked) and PubMedQA contrasts are secondary and unadjusted.

---

## 4. Execution plan and gates

### Gate 0 — Design review (this document set)
Planner approves method, baselines, metrics, locks. **No code beyond
prototypes on GSM8K train.**

### Gate 1 — Variance gate (CPU/small GPU, GSM8K train only)
Measure per-item config variance: how often does the per-item utility
argmax differ from the global argmax? If within-benchmark config variance
is negligible, **TACC is expected to fail H1**; report that measurement and
stop or rescope per Planner decision. This is the cheapest kill-switch.

### Gate 2 — Label matrix + controller training
Evaluate the candidate config set on the GSM8K train subset (budget-capped,
cached, hashed); train TACC (Approach A). Freeze controller weights +
config set + λ. Commit lock.

### Gate 3 — Locked evaluation (single shot per test set)
Run all 7 systems × SVAMP (300) and, if locked, MATH (500). One shot, no
tuning after seeing test outputs. Manifest, per-item predictions, forensic
verifier — same machinery as F2.

### Gate 4 — Analysis and report
Utility/transfer/regret tables, paired stats, selection distributions,
negative results, Gate report. Stop for Planner review.

---

## 5. Budget envelope (design-time estimate, not authorization)

| Step | Estimate |
|---|---|
| Gate 1 variance probe (train subset, 7 configs × ~500 items, 1.5B) | ~0.5–1.0 GPU·h |
| Gate 2 label matrix (config set × train subset) | ~1–3 GPU·h (cache-reuse dependent) |
| Gate 3 locked eval (7 systems × 300–800 items) | ~0.5–1.5 GPU·h |
| **Total Phase-2 envelope** | **≤ 5 GPU·h**, hard cap, tracked in status.json |

The candidate config set for the controller should be small (≤ 8
Phase-1-validated configs), which keeps both the label matrix and the
locked eval tractable.

---

## 6. Threats to validity (pre-registered)

- Dev reuse: GSM8K test[0:100] was exposed to Phase-1 selection — used only
  for controller model selection, never reported as evidence.
- Public-benchmark contamination (SVAMP/MATH): stated, not solvable.
- Oracle is computed on test and serves only as an upper bound, never as a
  deployable method.
- Controller overhead is metered and included in cost comparisons.
- If TACC ≈ B-rand, conditioning provides nothing — reported as such.
