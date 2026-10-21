# Kimi Code — Phase-2 R5/G1 repair after Planner Review R1
Repository: https://github.com/yujian777555/NeuroEvoScientist, branch main.
Authority: plans/phase2_planner_review_r1.md (read fully before work).
Role: Executor. GPT remains Planner.

## Current decision
R5 verdict PIVOT for plain embedding+MLP TACC is accepted. **The G1 pilot is NOT authorized. GPU budget authorized = 0.** This round is documents/literature only.

## Read first
- plans/phase2_planner_review_r1.md
- plans/phase2_r5_related_work_gap.md
- plans/phase2_r5_overlap_matrix.csv
- plans/phase2_g1_revised_protocol.md
- plans/phase2_g1_preflight_decision.md
- status.json

## Task A — targeted R5 expansion
Read and compare the primary sources:
1. BudgetMem, Learning Query-Aware Budget-Tier Routing for Runtime Agent Memory: https://arxiv.org/abs/2602.06025
2. Learning What to Retain: Gated-Memory Routing for Efficient Collaboration in Multi-Agent LLM Systems: https://arxiv.org/abs/2609.00237
3. Adaptive LLM Routing under Budget Constraints, Findings EMNLP 2025: https://aclanthology.org/2025.findings-emnlp.1301/
4. Selective prediction / reject-option / conformal or OOD deferral, pairwise ranking/relative utility prediction, budget-aware abstention.
Compare mechanism-level overlap, not title keywords: decision timing; query vs execution-state features; static episodic exemplars vs runtime/trajectory memory; reasoning-depth/strategy choice; cost model; uncertainty/shift signal; fallback policy; evaluation/transfer. Do not claim any method is an exact duplicate if its setting differs; state overlap and distinction accurately.
Fix the contradiction where the R5 doc says all 10 full papers were read while the Adaptive-RAG row says only abstract/known content. Audit all code-availability fields consistently.
Update the overlap CSV and R5 gap report. Keep PIVOT as default unless the evidence supports a precise, defensible mechanism. If no novelty gap survives, explicitly recommend STOP rather than inventing a distinction.

## Task B — G1 protocol repair
1. **Remove VAL leakage.** VAL currently tunes model/features/λ/δ/τ and is also used for D2 evaluation/CI. Redesign with explicit fit/tune/locked-evaluation roles, e.g. nested/grouped cross-fitting entirely on train-side partitions. State which data select the best fixed baseline and ensure its final comparison uses separate evaluation folds. No test outcomes or F2 values may be used to select policies.
2. **Fix utility units.** Define per-item utility explicitly, e.g. u_i = correct_i - λ * (prompt_tokens_i + completion_tokens_i)/10000, dataset utility as the mean of u_i; aggregate token total is reported separately. Clarify λ so “1 percentage point ≙ 1000 tokens” follows algebraically. State whether the λ policy value is independently specified or only exploratory because chosen from Phase-1 cost spreads. Pareto/raw metrics remain primary.
3. **Fix budget arithmetic using existing logs only; do not run a benchmark.** Current 12,000 generations at ~55 seconds/100 items/config implies ~6,600 sec = 110 min = 1.83 GPU-hours, not 35–55 min / ≤0.5 GPU-hours. Either reduce the sample/cell count with a pre-specified precision/power rationale or submit a realistic new budget request. No pilot runs this round.
4. Require the feature-based policy to beat the best fixed policy (selected without access to its evaluation fold) with a paired CI excluding zero and beat shuffled-label controls. A gain over B1 alone is insufficient.
5. Define embedding precompute/runtime accounting. Keep encoder FLOPs/latency separate from tokens.
6. Keep MATH-500 as candidate only. No data fetch, inference, adapter probe on its content, or results access before an immutable ID/revision/hash lock is committed.

## Required outputs
Update:
- plans/phase2_r5_related_work_gap.md
- plans/phase2_r5_overlap_matrix.csv
- plans/phase2_g1_revised_protocol.md
- plans/phase2_g1_preflight_decision.md
- status.json (phase2_planning fields only; correct last_commit to actual current HEAD at end)
Add a short change log or update the preflight report with exact issues resolved.

## Forbidden
- No GPU, training, inference, code, new holdout inspection, or controller implementation.
- Do not modify V1/V2 PDF, LaTeX, Markdown, supplementary archives, or historical F1/F2/V1 results.
- Do not mark pilot authorized.

Commit and push the document-only changes, verify clean worktree/remote sync, report exact SHA and the revised pilot time/budget arithmetic, then STOP for Planner R2 review.