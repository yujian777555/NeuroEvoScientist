# Gate 0 Decision — FAST-TRACK V2

Date: 2026-10-08. Executor: Kimi. Reviewer: Planner (GPT) — pending.

## Gate conditions (from v2_fasttrack_kimi_prompt.md / quality plan §4)

| Condition | Status | Evidence |
|---|---|---|
| Strong baselines defined and implementable | ✅ | `protocol_f0.md` §2 (B0–B5 + REF, CoT-matched, token-matched variants) |
| Auditable independent confirmation plan | ✅ | `confirmation_dataset.md`: SVAMP primary (HF sha 5e0bf1e5, verified reachable), MATH-algebra fallback (sha e839825f); contamination caveats documented |
| New/old result version isolation | ✅ | all V2 under `v2_quality/`; V1 PDF sha unchanged (test-enforced); Phase-17–21 artifacts untouched |
| Budget, statistics, stop rules explicit | ✅ | `compute_budget.md` (F1 ≤1.5 GPU-h, total ≤3.0, hard stop 4.0); `protocol_f0.md` §4–6 |
| Necessary tests pass | ✅ | `pytest tests/test_v2_f0.py`: 5 passed |

## Key audit findings (carried into F1 design)

1. V1 GSM8K fixed baselines were all Direct-reasoning; A_gsm uses CoT —
   the +29.0/+16.7pp margin conflates prompt strategy with search value.
2. At 1.5B, CoT alone (A_gsm minus memory) already matches A_gsm
   (0.5193 vs 0.5185) at ~3x fewer prompt tokens; memory adds nothing there.
   At 7B, memory adds +12.6pp. Any F1 claim must separate these.
3. Fixed baselines used 2.6–3.2x more tokens than A_gsm while losing —
   cost is not the advantage driver.
4. `paper/phase21_tables.md`: verified CONSISTENT with locked CSVs
   (Planner's suspicion not confirmed); marked SUPERSEDED, not present in
   the anonymous supplementary (clean).

## Decision proposal: **GO** for F1 (dev-only, budget-capped)

F1 may launch once Planner approves: 15 runs, ~44 GPU-minutes estimated,
1.5B discovery + 7B transfer shortlist, dev partitions only.

## Blockers / risks

- QASPER parser freeze: any parser change must be a versioned sensitivity
  study over ALL configs (locked in protocol §2).
- Confirmation read happens once, after `confirmation_lock.json` is written
  at F1 end. If SVAMP proves unsuitable at F1, V2 confirmation is
  exploratory-only.
- Multi-tenant GPU availability is the only schedule risk (no technical
  blocker).

## NO-GO triggers that would have applied

- No independent confirmation candidate → would have forced
  exploratory-only scope. (Not triggered: SVAMP verified.)
- Inability to isolate V1 results → would have blocked. (Not triggered.)
