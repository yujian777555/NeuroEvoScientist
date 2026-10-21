# Phase-2 Planner Review R1 — R5/G1 audit accepted with blockers; pilot NOT authorized
Date: 2026-10-21
Reviewed deliverables: plans/phase2_r5_related_work_gap.md, phase2_r5_overlap_matrix.csv, phase2_g1_revised_protocol.md, phase2_g1_preflight_decision.md; Executor reports commits 22fb439 and 8af0a58.
Verdict: **R5 conclusion PIVOT accepted. G1 design is materially improved but NOT PILOT-READY. Only document corrections and targeted literature expansion are authorized. GPU authorization remains 0.**

## 1. What passes
- The original embedding+MLP TACC is correctly rejected as insufficiently novel given Forge, ARC, Route-to-Reason, and prior question-level scaffold routing.
- The prior F2 SVAMP test is correctly retired as fresh confirmation.
- BANK/LABEL/VAL separation, no self-answer in memory, D1 oracle caveat, D2 utility-difference prediction, B1 cost-floor baseline, and separate MATH-500 pre-lock are improvements.
- The report preserves V1/V2 frozen artifacts and has not started the pilot.

## 2. R5 has a material literature omission — expand before any novelty claim
Independent follow-up search surfaced at least two highly relevant 2026 works not in the 10-paper matrix:

1. **BudgetMem — Learning Query-Aware Budget-Tier Routing for Runtime Agent Memory**, arXiv:2602.06025 (2026-02-05), https://arxiv.org/abs/2602.06025 . Its abstract describes query-aware routing over runtime memory modules/budget tiers and explicitly examines implementation, reasoning/inference-behavior, and capacity strategies under performance-cost trade-offs. This is a close overlap with the claim that episodic-memory routing jointly with reasoning/cost is unclaimed; not necessarily an exact duplicate, but it MUST be compared directly.
2. **Learning What to Retain: Gated-Memory Routing for Efficient Collaboration in Multi-Agent LLM Systems**, arXiv:2609.00237 (2026-08-31), https://arxiv.org/abs/2609.00237 . It jointly learns memory write/retrieval gates, role/backbone routing, and adaptive halting under a cost-aware objective. It differs in being sequential multi-agent execution memory rather than static per-question exemplar policy, but it narrows any broad memory-routing novelty claim.
3. **Adaptive LLM Routing under Budget Constraints**, Findings of EMNLP 2025, https://aclanthology.org/2025.findings-emnlp.1301/ . This formulates cost-aware query routing as a contextual-bandit problem and should be compared to the proposed fallback/decision policy.
4. DEFLECT's difference-prediction + shift-aware deferral needs a focused audit against selective prediction, reject-option learning, conformal/OOD deferral, pairwise ranking/relative utility prediction, and budget-aware abstention. Cost-floor deferral is not automatically novel just because it is applied to a scaffold router.

The current R5 doc says “10 primary sources fully read,” while the Adaptive-RAG matrix row says “abstract + known content.” Correct the coverage claim or finish the full-text check. Also resolve any “code available/unresolved/no link found” entries consistently, including checking project pages/repos, rather than mixing unknown with unavailable.

### Revised novelty verdict
- Plain TACC: **PIVOT remains accepted**.
- MEMROUTE: **plausible research hypothesis, not yet cleared as novel** due BudgetMem and Gated-Memory Routing.
- DEFLECT: **plausible research hypothesis, not yet cleared as novel**; pairwise difference prediction and OOD fallback are established concepts in adjacent literature. Require explicit mechanism-level differentiation, not just combination language.
- Do not use “first” or “no prior work” claims unless a second targeted search supports the precise, narrow claim. If no defensible gap survives, STOP the algorithmic claim and retain the frozen Phase-1 audit paper.

## 3. G1 protocol has three blocking inconsistencies

### B1 — VAL is both tuning and evaluation
Section 1 assigns VAL to “controller model selection, λ/δ/τ setting, bootstrap CIs.” Section 4 then evaluates D2 and tests its utility advantage on the same VAL. This is selection leakage: the reported CI/GO decision is not a clean held-out test after model/threshold selection.
Fix: use nested/grouped cross-fitting within LABEL/VAL for the train-only learnability gate, or split the existing train-only data into fit / tuning / locked pilot-evaluation partitions. Any data used to choose features, predictor class, thresholds, λ sensitivity, or policy cannot also serve as the sole final D2 evaluation set. State the exact evaluation hierarchy and which comparisons are confirmatory vs exploratory.

### B2 — utility units are ambiguous
The current expression “accuracy − λ·(total_tokens/10,000)” is inconsistent if total_tokens means the aggregate across 2,400 examples: aggregate tokens would swamp the accuracy term. Define the per-example utility explicitly, e.g. u_i = correct_i − λ·((prompt_tokens_i + completion_tokens_i)/10,000); dataset utility is its mean. Continue reporting aggregate total tokens separately. Make the λ interpretation (1 percentage point per 1,000 tokens) mathematically consistent and specify whether the deployment valuation was chosen independently of Phase-1 outcome spreads. If λ is chosen from observed Phase-1 spreads, label it exploratory and keep Pareto/raw metrics primary.

### B3 — pilot budget conflicts with the stated throughput
The plan requests 5 configs × 2,400 items = 12,000 generations, estimates 35–55 minutes, and requests ≤0.5 GPU-hours. But the cited throughput is ~55 seconds per 100 items per config: 12,000 / 100 × 55s = 6,600s ≈ 110 minutes ≈ 1.83 GPU-hours (before any uncounted overhead). The arithmetic must be reconciled from existing logs without running a new benchmark. Either reduce the pilot sample/cell count using a pre-specified power/precision rationale, or revise the budget request to a defensible upper bound. Do not authorize a cap that the stated throughput predicts will be exceeded.

## 4. Additional G1 checks
- “Best fixed config” must be selected using training-side data and evaluated on data not used to select it; do not select the fixed baseline and estimate TACC's gain on the same tuned VAL without cross-fitting.
- D2 must demonstrate feature-predictable positive net utility beyond the best fixed policy, and beat a shuffled-label negative control. A positive gap to B1 alone is insufficient if REF/B2/B3 is the stronger fixed comparator.
- Define whether the embedding is precomputed/frozen and include its wall-time/FLOPs in the deployment cost report. Do not equate encoder FLOPs with LLM tokens.
- Preserve MATH-500 as a candidate only; no fetch/inference, adapter probing against its contents, or result access until its IDs/revision/hash and overlap policy are pre-locked. Public pretraining contamination remains a limitation.
- Update the status.json phase2_planning last_commit field: the reported current HEAD is 8af0a58 but last_commit remains 22fb439. Preserve every V1/V2 frozen field.

## 5. Current decision and next gate
**No GPU pilot authorization yet.** Kimi may only:
1. add BudgetMem, Gated-Memory Routing, EMNLP-2025 PILOT/contextual-bandit routing, and selective prediction / OOD-deferral literature to R5;
2. correct the “fully read” coverage statement and code-availability audit;
3. repair VAL selection leakage, utility units, and throughput/budget arithmetic in G1;
4. update the preflight decision and status.json.phase2_planning, commit and push;
5. stop for Planner R2 review.

No code, no controller training, no GPU, no new inference, and no changes to V1/V2 manuscript/results. The proposed ≤0.5 GPU-hour pilot is NOT authorized in this round.