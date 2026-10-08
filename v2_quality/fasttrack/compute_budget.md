# F1 Compute Budget (locked at F0)

Basis: measured throughput on A800 (Phase-17..20): ~1.1 min per
100-problem evaluation at 1.5B (batch 32, exemplar prompts); QASPER
long-context prompts ~2.5–3 min per 50-item eval at 1.5B; 7B ≈ 3x slower.
Estimates per run are in run_matrix.csv; totals below.

## F1 totals

| Stage | runs | est. GPU-minutes | est. GPU-hours |
|---|---|---|---|
| GSM8K dev 1.5B (B0..B5,REF) | 7 | ~9.5 | 0.16 |
| QASPER dev 1.5B (B1,B2,B3,REF) | 4 | ~10.6 | 0.18 |
| Transfer shortlist 7B (B1,REF × 2 tasks) | 4 | ~24 | 0.40 |
| Contingency + reruns (×2) | — | ~44 | 0.73 |
| **Hard cap F1** | | | **1.5 GPU-hours** |

(The 12 GPU-hour figure in protocol §5 is the outer ceiling including F2;
F1 must stay within 1.5 GPU-hours.)

## F2 (conditional, locked only if F1 GO)

Independent confirmation on SVAMP or MATH-algebra subset (≤200 items,
shortlist ≤3 configs, 1.5B only): ≤ 1.0 GPU-hour.
Optional 2×2 interaction on DEV (GSM8K + QASPER): ≤ 0.5 GPU-hour.

## Total V2 GPU ceiling

F0 0.0 + F1 ≤1.5 + F2 ≤1.5 (with contingency) = **≤ 3.0 GPU-hours total**.
Hard stop at 4.0 GPU-hours; any overrun requires Planner re-authorization.

## Cost accounting rule

GPU-hours recorded per run from wall time × device; scheduling contention
is logged, never silently dropped. Cached evaluations count 0 GPU but are
flagged as cache-hits in the manifest.
