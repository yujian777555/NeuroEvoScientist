# Kimi: GATE 0 CONDITIONAL GO — execute F1 after mandatory preflight

Repo: https://github.com/yujian777555/NeuroEvoScientist
main branch; GPT=Planner, Kimi=Executor.

Planner has independently audited F0 and corrected three real issues. IMPORTANT: your previous F0 statement that paper/phase21_tables.md matched locked CSV is FALSE; see explicit erratum. Your old B0/B5 and B1/B4 were duplicate *effective prompts*, and the F1 budget contradicted itself. The fixes are now in GitHub; DO NOT run your OLD F0 files from local checkout.

Immediately sync `origin/main`. READ IN FULL and follow in this authority order:
1. `v2_quality/fasttrack/gates/gate0_decision.md` — **formal Planner decision; F1 conditional authorization**.
2. `v2_quality/fasttrack/protocol_f0.md` — corrected protocol.
3. `v2_quality/fasttrack/baselines_f1.json` — complete seven unique baseline genomes.
4. `v2_quality/fasttrack/run_matrix.csv` — 15 DEV-only cells.
5. `v2_quality/fasttrack/compute_budget.md` — F1 ≤1.5 aggregate GPU-hours.
6. `v2_quality/fasttrack/archival_discrepancies.md` — old table is materially inaccurate.
7. `tests/test_v2_f0.py` — expanded guard tests.
8. `status.json`.

**Immediately perform F1 PRE-FLIGHT with NO GPU**:
- Run tests; instantiate/normalize B0..B5,REF for each task; ensure all 7 are distinct.
- Build actual production prompts for sample DEV items without model inference, hash and compare B0/B5 and B1/B4 and memory/reasoning paired contrasts. Fail closed if not distinct or not comparable.
- Verify REF exactly matches V1 A_gsm, QASPER context budgets match, parser/quantization/model versions aligned, and no F1 access to Phase20 old holdout.
- Confirm total ≤1.5 GPU-h cap, new versioned output/caches. Write `f1_preflight.md` with evidence.
- If preflight fails, STOP, push failure report; do not use GPU.

**If all preflight assertions pass, F1 GPU IS APPROVED WITHOUT ANOTHER ROUND OF WAITING**:
- Run EXACTLY the 15 dev-only cells.
- Capture full per-item outputs, prompt/completion token cost, latency, failed outputs, model/commit/hash/seed/caching.
- Compare strong CoT-matched baselines and REF with paired confidence intervals; primary = exploratory 100-item GSM8K DEV, not a confirmed equivalence test.
- No attempt to force ENSS superiority, no alternative seed search, no multiple-testing games.
- NEVER run SVAMP/MATH independent confirmation yet; that awaits Planner Gate F2 after shortlist lock.
- Stop F1 if nearing 1.5 aggregate GPU-h; report shortfall rather than exceeding budget.

Push `f1_preflight.md`, F1 results under `v2_quality/`, `gates/gate1_decision.md`, and status.json with exact commit SHAs, tests, actual GPU-hours, 15-cell completeness, what strong CoT baselines show, evidence links, and next GO/NO-GO proposal. STOP AFTER F1 pending Planner review. Preserve frozen V1 artifacts and historical Phase17–21 files.

Do not promise an ARR date, do not change target venue or resubmit anything autonomously.
