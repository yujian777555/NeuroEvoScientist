# F2 Results — SVAMP Cross-Benchmark Confirmation (single shot)

Date: 2026-10-09
Runner commit: `2644295fa81860737594327bcd5dfa7328545f4d`
Status: **COMPLETE — 3/3 cells, 300/300 items each, 0 errors**

## Protocol compliance

- Locked data: SVAMP test 300 items, IDs sha256
  `4e462b134a5cf3dd…`, validated at run time by
  `svamp_adapter.load_locked_test_rows()` (any divergence = hard error).
- Locked configs: REF / B2 / B1 from `baselines_f1.json` — no re-selection,
  no tuning, no re-run after seeing results.
- Backbone: Qwen2.5-1.5B-Instruct, revision
  `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` (verified identical on the VM
  offline cache).
- Calibration bank: GSM8K TRAIN only (unchanged from V1/F1); SVAMP train
  never read.
- Prompts: Body + Question only; Equation/Answer never in prompts.
- Adapter cross-check: 0/900 scoring mismatches between the evaluator path
  and the locked adapter scorer.
- GPU: single idle card (VM 30939:0), aggregate **215.8 s = 0.060 GPU·h**
  (cap 1.0 h).

## Headline results (SVAMP test, n=300)

| Config | Accuracy | Prompt tokens | Completion tokens | Wall (s) |
|--------|----------|---------------|-------------------|----------|
| REF (search-selected, recency k=3, 1 exemplar, CoT d3) | **0.7033** | 68,017 | 50,049 | 74.5 |
| B2 (strong CoT preset, recency k=3, 3 exemplars, CoT d3) | **0.7167** | 197,017 | 44,137 | 70.1 |
| B1 (no memory, CoT d3) | **0.7033** | 19,117 | 48,264 | 71.2 |

## Paired statistics (bootstrap n=10000, seed=20260923; two-sided exact McNemar)

| Contrast | Diff (pp) | 95% CI (pp) | Discordant (a/b wins) | p_exact |
|----------|-----------|-------------|-----------------------|---------|
| **PRIMARY: REF vs B2** | −1.33 | [−6.00, +3.33] | 50 (23/27) | 0.6718 |
| **SECONDARY: REF vs B1** | 0.00 | [−5.33, +5.33] | 68 (34/34) | 1.0 |
| descriptive: B2 vs B1 (not pre-registered) | +1.33 | [−3.67, +6.33] | 62 (33/29) | 0.7035 |

Full machine-readable stats: `f2_results/f2_statistics.json`.
Per-item raw completions (all 900, untruncated): `f2_results/predictions_f2_*.jsonl`.
Consolidated manifest (all 3 cells, one file): `f2_results/run_manifest.json`.

## Difference from F1 (dev-side GSM8K, n=100, same backbone)

| Contrast | F1 GSM8K dev | F2 SVAMP test |
|----------|--------------|----------------|
| REF vs B2 | +1.0 pp (p=1.0) | −1.33 pp (p=0.67) |
| REF vs B1 | +10.0 pp (p=0.087) | 0.00 pp (p=1.0) |

The dev-side REF-vs-B1 memory benefit (+10 pp on GSM8K dev) **does not
transfer** to SVAMP: the exact same paired design yields 0.00 pp. This is
direct cross-benchmark evidence that the search-side benefit of the
recency-memory configuration is **benchmark-specific**, consistent with the
V2 paper thesis that search-side task specialization does not necessarily
generalize.

## Failure / anomaly trace

- None. 3/3 cells completed on first attempt; 0 errors; budget usage 6% of cap.
- Provenance defects from F1 (partial manifest, unknown git_sha) are fixed:
  single manifest covers all 3 cells with real commit SHA, model revision,
  dataset SHAs, adapter SHA, per-cell tokens and GPU seconds.

## Provenance limitations (carried into the paper)

- SVAMP is a **public benchmark**; pretraining contamination cannot be ruled
  out. F2 is cross-benchmark confirmation, **not** a same-distribution
  independent holdout.
- n=300 gives ±~5 pp CI resolution; equivalence is not formally established,
  only absence of a detectable advantage at this resolution.
