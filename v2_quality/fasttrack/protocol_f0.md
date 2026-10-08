# F1 Locked Protocol — Planner Corrected from F0 (2026-10-08)

Status: **F1 AUTHORIZED ON CONDITION PRE-FLIGHT PASS**. This document supersedes F0's conflicting baseline definitions and GPU cap; all V1 artifacts remain read-only.

## 1. Research question and anti-overclaim

What incremental accuracy/token value, if any, does the frozen V1 searched architecture A_gsm provide relative to fair and conventional *CoT-matched* fixed presets? The prior +29.0pp/+16.7pp V1 margin was over Direct-only baselines, so do not treat it as a search-specific effect. Phase-18 evolution ≈ random must remain a negative result.

- Primary descriptive contrast on **DEV**, `B1 (CoT no-memory) vs REF (searched V1 A_gsm)`, paired by item, on GSM8K 1.5B; log difference with CI, two-sided exact McNemar. Because these 100 dev items already influenced V1 search, this is **EXPLORATORY**, not preregistered independent confirmation or a formal equivalence/noninferiority test.
- Other F1 contrasts / QASPER / 7B are exploratory; all are allowed to favor baselines.
- No winner picked from this inspected DEV may be presented as an untouched discovery when later reported on that same DEV.
- Minimum practical threshold ±2 percentage points is a *decision heuristic* only: on n=100, a difference within ±2pp DOES NOT establish equivalence. Carry uncertainty and candidate shortlist forward to separately locked confirmation; avoid early scientific conclusions.

## 2. Exact machine-readable baseline identities

Authoritative baseline definitions: `v2_quality/fasttrack/baselines_f1.json`. The `baseline` column in run_matrix.csv must resolve to EXACTLY one effective genome, with the same task-specific input context budget, tokenizer, decoding and parser as the paired reference.

| ID | reasoning | memory/exemplars | context | unique scientific control |
|---|---|---|---|---|
| B0 | Direct | none, 0 exemplars | full | zero-shot Direct vs B1 |
| B1 | CoT depth 3 | none, 0 exemplars | full | strong CoT preset (REF minus memory) |
| B2 | CoT depth 3 | recency k3, 3 exemplars | full | exemplar count 3 vs REF 1 |
| B3 | CoT depth 3 | term-frequency cosine retrieval k3, 1 exemplar | full | retrieval type vs REF recency |
| B4 | CoT depth 3 | recency k3, **1** exemplar | **answer_only**, exemplar_word_budget=128 | context verbosity vs REF full |
| B5 | **Direct** | recency k3, **1** exemplar | full | reasoning alone vs REF CoT |
| REF | CoT depth 3 | recency k3, **1** exemplar | full | frozen `A_gsm` reference |

Important: Original F0 B0=B5 were duplicates. Original B4 had no exemplars and thus `context_mode=answer_only` was behaviorally inert and duplicated B1. Corrected B4/B5 are genuinely different prompts, and this change must be captured as a versioned pre-run protocol correction. Do NOT implement TF-IDF when only sparse term-frequency cosine exists. `B1` is not the strongest provable CoT baseline a priori; refer to it as the *predefined CoT no-memory preset*; the best CoT-matched baseline is determined transparently among all listed baselines, with exploratory selection caveat.

All baselines using QASPER must share an explicitly defined fixed document word budget (2048) and same data rendering; no comparator is granted more context without being identified as a distinct treatment. Prepare a deterministic prompt-equivalence unit test for B1/B4 and B0/B5 to verify *not identical*, and B5 vs REF should differ in reasoning instruction, not memory count.

## 3. Data, splits and cache integrity

- DEV ONLY: GSM8K test[0:100] and QASPER items[0:50], per old development splits. No Phase-20 inspected holdout in F1 inference, even via cache.
- Phase-20 holdout references may be described historically, not passed into the active F1 runner.
- Independent confirmation SVAMP is a **candidate**, not an already fully locked/validated test set. F1 must not load or inspect its gold answers/outputs. At F1 end prepare an exact immutable confirmation item-ID lock and checks of provenance, duplicates and prompt/procedure compatibility before Planner Gate F2 decision; don't change chosen dataset based on model performance.
- Public pretraining contamination is unknowable; acknowledge.
- Use new versioned caches and run results under `v2_quality/`. Never alter `results/`, `experiments/`, `configs/`, V1 paper, or historic selection lock.
- Fail closed on prompt hash, genome hash, model revision, dataset revision, item slice, parser version, inference backend, and cache identity mismatches. Retain all original completions and per-item scores with traces.

## 4. Control & stats

- Same frozen model revision and decoder per paired comparisons, greedy, max_new_tokens 256, FP16, batch 32. Verify hardware/model IDs. Count actual prompt and generated tokens, separately.
- Use paired bootstrap 95% CI (10k), McNemar for binary GSM8K outcomes and paired exact sign test on nonzero per-item QASPER F1 differences. Do not report significance from an unadjusted multi-comparison search as primary confirmatory.
- Cost evaluation must compare accuracy-vs-token Pareto tradeoffs, avoid claiming lower token cost from apples/oranges model tokenizers.
- n=100 DEV results are noisy. A non-significant difference is NOT equivalence; do not use automatic stop on ±2pp alone.
- Exact prescribed 15-cell F1 matrix: `v2_quality/fasttrack/run_matrix.csv`; no new unlogged cells or seed reruns. If reruns are necessary for infra failures, log and account.
- Every cell requires run_id, git SHA, model/dataset revision, seed, prompt/genome hashes, actual usage, cache hit/miss, errors, item-level scores and output paths.

## 5. Hard resource cap (consistent across documents)

**F1 ≤ 1.5 GPU-hours measured as sum of device-time across assigned GPUs.** F0 approved baseline estimated ~43.2 device-minutes without contingencies; up to ~86.4 with a 2x contingency. F2 budget to be decided separately after F1; planned V2 total ≤3.0 GPU-hours, global safety ceiling 4.0 with renewed authorization. The original F0 protocol's '12 GPU-hours for F1' was an error and is revoked. Do not multiply number of simultaneous GPUs into 'wall time savings' without reporting aggregate GPU-hours.

## 6. F1 termination, audit & F2 handoff

At end of F1, STOP and submit:
- F1 report with all 15 attempted cells, successes/failures, actual aggregate GPU-time and all raw paths.
- B1 vs REF paired contrasts with CI and effect sizes; compare other fair CoT, memory and context presets with cost.
- A controlled failure classification if another config wins, including whether any positive search-specific claim remains defensible.
- Candidate confirmation shortlist (≤3) locked *before* SVAMP labels/results are consulted; proposal for F2 data integrity and transfer budget.
- No independent-confirmation result and no V2 paper-ready declaration until Planner approves F2.

If F1 misses required integrity checks, mark BLOCKED and do not advance.
