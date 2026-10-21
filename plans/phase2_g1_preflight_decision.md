# Phase-2 G1 Preflight Decision v2 — Executor Report (2026-10-21)

Authority: `plans/phase2_planner_review_r1.md`,
`plans/phase2_g1_pilot_repair_prompt.md`.
Scope executed: document/literature only. **0 GPU, 0 training, 0
inference, no controller code, V1/V2 frozen artifacts untouched, MATH-500
untouched.**

## R1 issue-by-issue resolution

### R5 expansion (Task A)

| R1 requirement | Status | Evidence |
|---|---|---|
| Add BudgetMem (2602.06025) | DONE | FULL read; matrix row + gap §2. Contests broad "memory routing under token-costed utility"; runtime pipeline tiers, PPO, multi-capacity; static-exemplar axis survives narrowly |
| Add Gated-Memory Routing (2609.00237) | DONE | FULL read; matrix row + gap §2. RL trajectory-memory gates (nearest recall-width analog); multi-agent, multi-model; narrows M2 broadly, static pre-inference exemplar routing survives |
| Add EMNLP-2025 budget routing (PILOT) | DONE | FULL read (App. D.1 extraction truncated — recorded); contextual-bandit LLM routing under token budget; "cost-aware per-query routing" framing owned by PILOT — TACC may not claim it |
| Audit DEFLECT vs selective-prediction / reject-option / conformal / pairwise-ranking literature | DONE | Scan row-set added (RouteLLM, FrugalGPT, Mozannar & Sontag ICML 2020, Liang et al. TMLR 2024, Chow 1970). M1's two halves are each anticipated (RouteLLM: pairwise-diff + defer-to-cheap between models; Liang: shift-aware abstention for frozen models). Surviving claim narrowed to the exact combination; conformal-deferral sub-scan UNRESOLVED and recorded as a mandatory pre-submission re-audit |
| Fix "10 primary sources fully read" contradiction | DONE | v2 gap doc carries a per-row coverage statement (12 FULL / 2 ABSTRACT-ONLY / 1 SNIPPET / 1 FULL-minus-appendix); Adaptive-RAG row corrected to ABSTRACT-ONLY |
| Consistent code-availability audit | DONE | Per-row: RouteLLM YES(URL), FrugalGPT YES(URL), Adaptive-Solver YES(URL), RTR YES(URL), BudgetMem YES(URL + project page), Liang YES(URL), L2D YES(URL); Chen-2025/Gerych/FluxMem/Forge/PILOT NO; ARC LINKED-UNRESOLVED; Gated-Memory-Routing placeholder-repo NO; Chow NO |

**Revised verdicts:** plain TACC PIVOT (unchanged); M1/M2 = plausible
research hypotheses, **not cleared novel**; narrowed claims written into
`phase2_r5_related_work_gap.md` §3; STOP conditions pre-declared (§4).

### G1 repair (Task B)

| R1 issue | Status | Fix |
|---|---|---|
| B1 — VAL both tunes and evaluates | DONE | Four partitions BANK/FIT/TUNE/LEVAL (40/25/15/20), hash-locked; fitting on FIT, thresholds on TUNE, **LEVAL used exactly once** for the confirmatory contrast; cross-fitting inside FIT∪TUNE; exploratory-vs-confirmatory hierarchy stated (`phase2_g1_revised_protocol.md` §1) |
| B2 — utility units ambiguous | DONE | Per-item `u_i(c) = correct_i − λ·(prompt_i+completion_i)/10,000`; dataset utility = mean; aggregates reported separately; λ = 0.1 ⟹ 1pp ≙ 1,000 tokens shown algebraically; λ labeled **exploratory-informed** (chosen with awareness of Phase-1 spreads); raw accuracy/tokens/Pareto primary (§4) |
| B3 — budget arithmetic wrong | DONE | v1 error documented: 55 s is per-100-items-per-config, so 12,000 gens ⇒ 6,600 s ≈ 1.83 GPU·h, not ≤0.5. v2 downsized with precision rationale: 5 configs × (800 FIT+TUNE + 300 LEVAL) = 5,500 gens ⇒ 3,025 s ≈ 0.84 GPU·h + 15% overhead ⇒ **revised request ≤ 1.0 GPU·h** (hard cap); LEVAL n=300 gives ±2–3pp CI, sufficient vs the ~10pp motivating effects (§8) |
| Best-fixed selection must not see its eval fold | DONE | best fixed = highest cross-fitted FIT∪TUNE utility, selected without LEVAL access; final comparison on LEVAL once (§3, §5) |
| D2 must beat best fixed + shuffled control | DONE | pass requires BOTH, paired CI excluding 0; beating B1 alone insufficient (§5) |
| Embedding/controller overhead accounting | DONE | encoder seconds + controller ms reported as separate units, never equated with tokens (§6) |
| MATH-500 candidate-only | DONE | no fetch/probe/result access before immutable lock (§2) |
| status.json last_commit stale | DONE | updated to actual HEAD (see below) |

## Files changed this round

- `plans/phase2_r5_overlap_matrix.csv` — 16 rows (was 10), coverage/code
  fields consistent
- `plans/phase2_r5_related_work_gap.md` — v2 rewritten (narrowed claims,
  honest coverage statement)
- `plans/phase2_g1_revised_protocol.md` — v2 rewritten (B1/B2/B3 repairs)
- `plans/phase2_g1_preflight_decision.md` — this file
- `status.json` — `phase2_planning` only

## What is NOT done (explicit)

- Pilot NOT executed and NOT authorized (request: ≤1.0 GPU·h, pending
  Planner R2).
- No controller code, no training, no GPU, no confirmation-data access.
- Conformal-deferral literature scan: UNRESOLVED (mandatory pre-
  submission re-audit).
- No claim in this round is final-novelty-cleared; M1/M2 remain
  hypotheses pending Planner R2.

**STOP point reached. Awaiting Planner R2 review.**
