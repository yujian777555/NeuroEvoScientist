# Phase-2 G1 Preflight Decision v3 — Executor Report (2026-10-21)

Authority: `plans/phase2_planner_review_r2.md`,
`plans/phase2_g1_pilot_repair_prompt_r2.md`.
Scope executed: document/literature only. **0 GPU, 0 training, 0
inference, no controller code, no dataset loads, no partition locks
created, MATH-500 untouched, V1/V2 frozen artifacts untouched.**

## R2 issue-by-issue resolution

| R2 item | Status | Resolution |
|---|---|---|
| R2-A — D2 gate incomplete | DONE | Full battery pre-specified (protocol §5): candidate must beat (1) train-side-selected best fixed, (2) shuffled-label control (1,000 shuffles, seeds locked from SEED+1), (3) random policy (1,000 draws, SEED+2), (4) majority/action-frequency policy, (5) simple length/numeric-density feature baseline. Primary contrast = paired utility diff vs BEST-FIXED (bootstrap 10k, seed SEED+3, CI excludes 0); binary component exact McNemar; hierarchical intersection–union multiplicity rule; candidate/thresholds/seeds frozen before LEVAL; no post-hoc selection |
| R2-B — sample plan ambiguous | DONE | Exact planned counts: FIT_pilot=500 ⊂ FIT, TUNE_pilot=200 ⊂ TUNE (justified: scalar-threshold tuning needs less), LEVAL_pilot=300 ⊂ LEVAL(~1,495), all drawn by sha256(normalized_id‖SEED) ordering, SEED=20261021. Explicitly marked PLANNED: no lock artifacts created this round; CPU-preflight deliverable deferred. Ordered pipeline FIT-only → TUNE-only → best-fixed selection → one-time LEVAL; no LEVAL refit/resampling |
| R2-C — unsupported ±2–3pp claim | DONE | Claim withdrawn. Scenario table (q=5/10/20/40% → ±2.5/3.6/5.1/7.2pp) + token-variance widening note. F2 historical discordance (16.7%/22.7%) cited as planning-only with transfer limits. Pilot relabeled "learnability screen with uncertain power"; no detection guarantee |
| R2-D — throughput/budget reconciliation | DONE | From existing logs only: 55s/100 = wall-clock inside `evaluate()` (prompt+generation+scoring), model loaded once per process, fresh caches (misses included), memory-bank build EXCLUDED (timed outside, CPU-scale) — so the +15% overhead is incremental, not double-counted. Wall-vs-GPU-active metering gap disclosed; pilot must instrument it. v2's 0.97h (margin ~2min) judged inadequate → redesigned to 5,000 gens: worst case 0.88 GPU·h, expected ~0.40, +45-min abort rule. Revised request ≤1.0 GPU·h (NOT authorized) |
| R2-E — algebra + terminology | DONE | Algebra corrected to λ×1,000/10,000 = 0.1×0.1 = 0.01. "Pre-registered" → "pre-specified and commit-locked before LEVAL inference" everywhere; stale VAL references eliminated (partition is LEVAL) |
| R2-F — conformal scan | DONE | Fang & Nalisnick (TMLR 2026; verification PARTIAL — OpenReview bot-walled, abstract+project page+repo README) and TACR (arXiv 2610.02487; FULL) added to matrix + gap §4. Both DISTINCT (human-expert deferral; surrogate-vs-simulator threshold routing). Scope distinctions written explicitly. Verdicts unchanged: PIVOT / novelty NOT CLEARED |

## Status consistency (R2-§3 / Task G)

- `status.json.phase2_planning` rewritten with explicit semantics:
  `last_deliverable_commit` (substantive Executor work) vs
  `observed_remote_head` (latest verified remote state) are separate
  fields; no self-referential hash claim.
- `next_gate` = Planner R3 review; resolved R1/R2 items separated from
  remaining blockers; `g1_protocol` updated to BANK/FIT/TUNE/LEVAL;
  `gpu_authorized: 0`; `pilot_status: NOT AUTHORIZED / NOT EXECUTED`;
  `implementation_authorized: false`.

## Explicitly NOT done

- No partition-lock artifacts (future CPU-preflight deliverable, requires
  separate authorization).
- No GPU/inference/training; no dataset downloads; no MATH-500 access.
- Novelty NOT cleared for M1/M2; no "first" claims.
- Pilot remains NOT AUTHORIZED.

**STOP point reached. Awaiting Planner R3 review.**
