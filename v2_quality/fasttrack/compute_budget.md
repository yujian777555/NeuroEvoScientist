# F1 Compute Budget — Planner corrected (2026-10-08)

Current execution plan: `v2_quality/fasttrack/protocol_f0.md` and `baselines_f1.json`.
Estimated minutes are planning assumptions, not confirmed GPU measurements. A800 device occupancy and input length can vary.

| F1 component | runs | sum of run_matrix estimates |
|---|---:|---:|
| GSM8K dev 1.5B B0–B5 + REF | 7 | ~8.6 device-min |
| QASPER dev 1.5B B1/B2/B3/REF | 4 | ~10.6 device-min |
| Transfer dev 7B B1/REF × 2 tasks | 4 | ~24.0 device-min |
| **Base total** | **15** | **~43.2 device-min = 0.72 GPU-h** |
| **Contingency / rerun allowance** | — | **~43.2 extra device-min** |
| **F1 MAXIMUM** | | **1.5 aggregate GPU-hours** |

F1 hard cap means sum of concurrent devices × actual device runtime, not wall clock. Cache hits count 0 new GPU-h but must be explicitly marked. If at risk of exceeding 1.5, stop and ask Planner; do not invoke a 12-GPU-hour allowance (revoked F0 wording).

Future F2 if separately authorized: ≤1.5 additional aggregate GPU-hours. Project target ≤3.0 total GPU-hours; any extension toward or beyond 4.0 requires explicit Planner and owner authorization. Do not begin F2 automatically.

Interpretation: nominal 43.2 minutes of **aggregate single-GPU device time**, not a guarantee of 43.2 wall-clock minutes; CPU preprocessing, shared-GPU queuing, failures, download/setup and data integrity checks may dominate elapsed time.
