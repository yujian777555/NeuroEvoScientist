# Phase-2 Pilot Result Report

Date: 2026-10-27

## Final status: **INCONCLUSIVE_NULL**

The preregistered Pilot completed all 5,000 generations and the full 1,000-replicate adaptive permutation analysis. The D2 gate is **not passed**: valid F1 permutation replicates were only 251/1000, below the required 950, so the conditional SHUFFLE test is inconclusive. Independently, all three paired fixed-config/simple-feature contrasts failed, and only the RANDOM control passed.

This is not evidence of controller superiority, a validated learnability result, or authorization for full-scale experiments.

## Model selection and actual outcomes

- Selected class: `gbt|n=100|d=1` (GradientBoostingRegressor, 100 trees, depth 1).
- Feature set: F1 (simple features + frozen 384-d HashingVectorizer embedding).
- Candidate thresholds: delta=0.01, tau=27.166463291500232.
- SIMPLE-FEAT: independent F0 thresholds delta=0.005, tau=0.6259149964516657.
- BEST-FIXED: B2. MAJORITY: B1.

| System | Accuracy | Prompt tokens | Completion tokens | Utility (λ=0.1) |
|---|---:|---:|---:|---:|
| B1 | 0.6400 | 24,804 | 62,164 | 0.6371011 |
| B0 | 0.1467 | 20,904 | 2,906 | 0.1458730 |
| B3 | 0.5967 | 87,699 | 63,244 | 0.5916352 |
| REF | 0.6033 | 86,004 | 64,534 | 0.5983154 |
| B2 | 0.6500 | 208,704 | 60,530 | 0.6410255 |
| CANDIDATE | 0.6333 | 100,614 | 60,727 | 0.6279553 |
| SIMPLE-FEAT | 0.6400 | 100,508 | 61,668 | 0.6345941 |

## D2 gate

| Contrast | Mean paired utility diff | 95% CI | Pass |
|---|---:|---:|---|
| CANDIDATE − BEST-FIXED (B2) | -0.0130702 | [-0.0562722, 0.0270257] | NO |
| CANDIDATE − MAJORITY (B1) | -0.0091458 | [-0.0459168, 0.0275942] | NO |
| CANDIDATE − SIMPLE-FEAT | -0.0066388 | [-0.0466694, 0.0331997] | NO |
| RANDOM mid-rank | 1.0 | — | YES |
| SHUFFLE valid replicates | 251/1000 | required ≥950 | **INCONCLUSIVE_NULL** |

SHUFFLE mid-rank was 0.378486, also below 0.95. No invalid replicates and no null errors were recorded. All other gate conditions except RANDOM failed.

## Resource use

- VM: port 30939, one NVIDIA A800 80GB PCIe, `cuda:0`.
- Model: `Qwen/Qwen2.5-1.5B-Instruct`, revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`.
- Generations: 5,000 attempted, 5,000 completed, 0 failed.
- GPU inference wall time: 787.8377 s.
- NVML active-time integral: 329.0410 s = **0.0914003 aggregate GPU-hours** (not conflated with wall time).
- Permutation analysis: 1,000 replicates, 0 invalid, 749 F0-NO-GO, 251 valid F1-scored.
- CPU analysis across workers: 523,065.4217 CPU-seconds (145.30 CPU-hours); wall time 13,692.4471 s (3.80 h).
- Smoke test: 2 replicates, 866.197 s; full sharded analysis used 40 deterministic shards of 25 replicates.

## Verification

- Independent recomputation from all 5,000 raw records matched accuracy, prompt/completion totals, and utility for every fixed config and for CANDIDATE/SIMPLE-FEAT (`planner/pilot_result_verification.log`).
- Lock hash remains `ff6c703e4dce45e88b6847a144433479a1702feae5cf5afc3a466ffd8a5c5035`.
- Historical NO-GO evidence and source data were not modified.
- Focused repair tests: 32 passed; complete CPU suite: 219 passed, 0 failed.
- No MATH-500 access and no other experiments were performed.

## Boundary

Stop at the Pilot boundary. No full-scale experiment or new hypothesis/configuration is authorized by this result. Any follow-up requires a separate Planner decision addressing both the low valid-F1-replicate rate and the lack of a detectable advantage over fixed controls.
