# Kimi Code: FAST-TRACK V2 execution handoff (2026-10-08)

Repo: https://github.com/yujian777555/NeuroEvoScientist | main
GPT=Planner; Kimi=Executor. The owner clarified: **not racing the October deadline at all costs, but still wants submission as early as reasonably defensible**.

Immediately `git fetch origin`, sync main and READ IN FULL:
1. `plans/v2_fasttrack_submission_plan.md` — **new active scheduling/scope authority**.
2. `plans/v2_quality_upgrade_plan.md` — scientific controls and extended optional backlog.
3. `status.json` — latest handoff.
4. `plans/v2_kimi_executor_prompt.md` — older detailed V2-0 audit list; interpret it in light of the new fast-track scope.

CURRENT AUTHORIZATION: **F0 only**, no GPU. Audit baseline fairness, identify strong CoT-matched fixed comparator definitions, freeze metrics/splits/parser and finite compute budget, confirm whether any genuinely independent holdout exists (old inspected holdout is NOT untouched), check whether obsolete `paper/phase21_tables.md` contaminates supplementary. Reuse any audit you have already started.
Write a compact `v2_quality/fasttrack/f0_gate.md` and link exact versioned protocol/run matrix with two-model estimate. Update status and push F0. Stop and request Planner approval before F1/GPU.

Priority order:
- F1 fair CoT baselines and token-budget comparisons;
- F2 independent confirmation, if viable; otherwise be transparent exploratory and consider narrow separate task;
- F3 revise and submit V2;
- defer broad interactions, full structured evolution-vs-random reruns, extra model families, or 7–10 week work unless a concrete gated problem needs them.
Preserve V1 `paper/arr2026/`, `deliverables/final_submission/`, historical `results/`/`experiments/`, lock files unmodified. Negative results are valid; don't reframe as search victory.

Important calendar: 2026-10-12 ARR is the final NAACL 2027 / COLING 2027 applicable cycle. Do not claim next cycle eligible for those conferences; verify next intended venue from official page, without inventing submission dates. Existing V1 could be submitted in October only if owner chooses and completes portal/admin, not Kimi's decision.

Output:
F0 AUDIT — COMPLETE/BLOCKED
HEAD/origin-main and clean status
Evidence of Direct-vs-CoT baseline confounding
Proposed limited F1 run matrix; time/GPU-hour budget
Independent confirmation dataset readiness / contamination guard
Versioned artifacts and tests
Experiment reruns: NO, GPU hours: 0
Gate GO/NO-GO and scientific blockers
Push commit and precise files/URLs
STOP. Ask Planner to open F1.
