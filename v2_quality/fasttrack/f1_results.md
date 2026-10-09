# F1 Results — Strong CoT-Matched Baselines (dev-only)

Date: 2026-10-09. Source commit: `7a35430` (runner) — VM checkout has no .git
(manifest git_sha "unknown"; code version recorded here).
GPU: A800 × 3 cards used; **aggregate GPU time ≈ 563 s ≈ 0.16 GPU-hours**
(cap 1.5). 15/15 cells completed, zero failures.
Data: `v2_quality/fasttrack/f1_results/` (f1_summary.csv + 15 per-item
prediction files + run_manifest.json). All DEV slices; no holdout touched.

## Per-cell results

### GSM8K dev (test[0:100], accuracy)

| Cell | Baseline | Memory | Reasoning | Acc | Prompt tokens |
|---|---|---|---|---|---|
| F1-06 | B0 | none | direct | 0.110 | 6,791 |
| F1-05 | B5 | recency×1 | direct | 0.130 | 23,091 |
| F1-01 | B1 | none | cot d3 | 0.500 | 8,091 |
| F1-04 | B4 | recency×1 + answer_only 128w | cot d3 | 0.490 | 14,491 |
| F1-03 | B3 | retrieval tf-cosine k=3 | cot d3 | 0.570 | 27,683 |
| F1-02 | B2 | recency k=3 | cot d3 | 0.590 | 67,391 |
| F1-07 | REF (A_gsm) | recency×1 | cot d3 | **0.600** | 24,391 |

### QASPER dev (items[0:50], normalized F1 on extracted answer)

| Cell | Baseline | F1 | Prompt tokens |
|---|---|---|---|
| F1-11 | REF (A_gsm) | 0.167 | 144,623 |
| F1-08 | B1 | 0.184 | 143,323 |
| F1-10 | B3 | 0.188 | 144,851 |
| F1-09 | B2 | 0.192 | 146,323 |

### 7B transfer (pre-chosen shortlist)

| Cell | Baseline | Task | Score |
|---|---|---|---|
| F1-12 | B1 | gsm8k | 0.750 |
| F1-13 | REF | gsm8k | **0.850** |
| F1-14 | B1 | qasper | 0.161 |
| F1-15 | REF | qasper | 0.178 |

## Paired statistics (item-level, bootstrap 10k + exact McNemar)

| Comparison | Δpp | 95% CI | p |
|---|---|---|---|
| REF vs B1 (primary, gsm8k dev) | +10.0 | [0.0, 20.0] | 0.087 |
| REF vs B2 | +1.0 | [−8.0, 10.0] | 1.000 |
| REF vs B3 | +3.0 | [−5.0, 11.0] | 0.629 |
| REF vs B4 | +11.0 | [+2.0, 20.0] | 0.043 |
| B2 vs B1 (memory on/off under CoT) | +9.0 | [−2.0, 20.0] | 0.163 |
| REF vs B1 at 7B (gsm8k dev) | +10.0 | [+2.0, 19.0] | 0.041 |
| REF vs B2 (qasper dev) | −2.6 | [−7.6, +1.8] | 0.749 |
| REF vs B1 (qasper dev) | −1.7 | [−5.8, +2.5] | 0.154 |

## Reading

1. **No search advantage over CoT-matched presets.** REF ties B2/B3 on
   GSM8K dev (+1pp/+3pp, n.s.) and is slightly below them on QASPER dev.
2. The +10pp REF-vs-B1 gap (CoT with no memory) is the memory+exemplar
   component, not search; it is directionally consistent but n.s. at
   1.5B (p=0.087) and significant at 7B (p=0.041) — matching the V1
   holdout finding that memory matters more at larger scale.
3. B4 (reduced-context CoT) is the only preset clearly below REF
   (+11pp, p=0.043) — context budget matters more than which strong
   preset you pick.
4. Cost: B1 is cheapest among CoT presets (8k tokens); REF sits mid
   (24k); B2 highest (67k) with no accuracy gain over REF.
