# Gate 2 Executor Report — F2 SVAMP Confirmation (2026-10-09)

Executor: Kimi. Evidence commits: preflight `297d24e`, runner `2644295`.
This is the Executor's report and Gate-2 **recommendation**; the GO/NO-GO
decision itself belongs to the Planner.

## Execution verdict: PROTOCOL CLEAN

All Gate-1 preflight conditions were met before any GPU inference:

1. Dataset revision + file SHAs proven (`5e0bf1e5…`; test sha256 `9b5590fc…`).
2. All 300 test IDs frozen in `confirmation_lock.json` before inference
   (`test_ids_sha256 4e462b13…`); lock committed at `297d24e`, GPU started
   only after runner commit `2644295`.
3. Versioned adapter (`svamp-adapter-v1`) CPU-tested with synthetic fixtures;
   Body+Question only; Equation/Answer never in prompts.
4. Overlap vs full GSM8K corpus: 0/300 (normalized exact match); public-
   benchmark contamination caveat recorded in the lock.
5. Configs frozen as REF/B2/B1; backbone Qwen2.5-1.5B-Instruct revision
   `989aa798…` (verified on-VM); primary REF vs B2, secondary REF vs B1.
6. Consolidated single manifest for all 3 cells: real git SHA, model
   revision, dataset SHAs, adapter SHA, cache identity, phenotype hashes,
   seed, per-cell tokens/errors/GPU-seconds. F1 manifest defect fixed.
7. Full test suite green at preflight (102 passed; one F0 wording test
   repaired by restoring the explicit V1-holdout exclusion sentence in
   `confirmation_dataset.md`, no semantic change).
8. GPU budget: 0.060 GPU·h used of 1.0 h cap. Single shot; no re-runs.

## Results (SVAMP locked test, n=300, 1.5B)

- REF 0.7033 (68,017 prompt tok / 50,049 completion tok)
- B2  0.7167 (197,017 / 44,137)
- B1  0.7033 (19,117 / 48,264)
- PRIMARY REF vs B2: −1.33 pp, 95% CI [−6.00, +3.33], McNemar p=0.6718.
- SECONDARY REF vs B1: 0.00 pp, 95% CI [−5.33, +5.33], McNemar p=1.0.
- 0/900 adapter-scoring mismatches; 0 cell errors.

## Scientific reading (restrained)

1. **No detectable advantage** of the search-selected REF over the strong
   CoT-matched preset B2 on unseen-to-project SVAMP — consistent with F1 dev.
   REF matches B2 accuracy with ~2.9× fewer prompt tokens (68k vs 197k),
   a cost-side observation only; no superiority claim is supported.
2. **The F1 dev-side REF-vs-B1 memory benefit (+10 pp) does NOT transfer
   cross-benchmark (0.00 pp, p=1.0).** The recency-memory benefit is
   benchmark-specific at 1.5B. This directly supports the V2 thesis that
   search-side task specialization does not necessarily generalize — and it
   prohibits any universal "memory helps" or scale-dependent memory claim.
3. Nothing in F2 supports search-superiority, optimizer-centric, or
   equivalence claims (n=300 resolution ±~5 pp; absence of evidence, not
   evidence of exact equivalence).

## Exploratory vs externally confirmed — Executor classification

- **Externally confirmed (cross-benchmark, public benchmark):**
  - Search-selected REF shows no detectable accuracy advantage over a strong
    pre-specified CoT baseline on data never used for search or tuning.
  - Dev-side search preferences (memory benefit) are benchmark-specific and
    can fail to transfer — a confirmation of the V2 "generalization gap"
    thesis on independent data.
- **Remains exploratory:** any nonzero memory/scale effect sizes, all F1
  dev-side differences, and anything about QASPER or 7B (untouched by F2).

## Gate 2 recommendation: **GO (conditional)**

F2 is protocol-clean and delivers the cross-benchmark confirmation the
fast-track plan required. Recommended conditions for F3 (paper revision):

1. Paper claims limited to: configurations matter; no search superiority;
   memory benefit benchmark-specific (dev +10 pp → SVAMP 0 pp); cost-side
   token differences reported descriptively.
2. Explicit limitations: public-benchmark contamination; n=300 power;
   single backbone (1.5B); single confirmation benchmark.
3. V1 artifacts remain frozen; F2 numbers reported as V2 evidence only.

**STOP point reached. Awaiting Planner Gate-2 decision before any F3 work.**
