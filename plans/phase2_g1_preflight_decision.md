# Phase-2 G1 Preflight Decision — Executor Report (2026-10-21)

Authority: `plans/phase2_planner_review_r0.md`, `plans/phase2_r5_g1_kimi_prompt.md`.
Scope executed: document-only. **0 GPU, 0 training, 0 inference, no
controller code, no modification of V1/V2 frozen artifacts.**

## 1. Papers audited and direct novelty collisions

10 primary sources fully read (fact sheets + comparison matrix in
`plans/phase2_r5_overlap_matrix.csv`; gap analysis in
`plans/phase2_r5_related_work_gap.md`):

- **Direct collisions:**
  - **Forge** (arXiv 2609.34358, 2026-09-28): per-question joint
    (evidence form × thinking depth) selection above a *single frozen
    host*, trained from measured accuracy − λ·token utility. Two of TACC's
    three axes + the utility form.
  - **ARC** (arXiv 2602.11574, v5 2026-10-06): per-query joint
    (workflow × tools × token budget × prompt) over a frozen agent system
    (RL+SFT).
  - **RTR / Route to Reason** (WWW 2026): supervised accuracy − λ·token
    per-question selection with OOD benchmarks (utility-form collision).
  - **Chen et al. NAACL-Findings 2025**: supervised per-question
    augmentation-path routing above one frozen LLM (archetype collision).
- **Partial:** Gerych et al. AAAI 2024 ((model,prompt) confidence
  routing), Adaptive-Solver IPM 2025 (heuristic escalation), FluxMem 2026
  (memory-structure selection), Adaptive-RAG NAACL 2024 (retrieval depth),
  RouteLLM ICLR 2025 + FrugalGPT TMLR 2024 (cost-aware model
  routing/cascades).

## 2. Novelty decision

**Original embedding+MLP TACC: PIVOT** (not defensible as a standalone
algorithmic contribution; "frozen backbone vs model routing" is
insufficient — Forge/ARC are frozen-backbone).

**Strongest defensible differentiator (narrow, falsifiable):** joint
per-question routing that includes the **episodic-memory policy axis**
(recall width / exemplar count / memory on-off) with a token-costed
utility, via one of two candidate mechanisms:

- **M1 DEFLECT** — pairwise utility-*difference* prediction +
  shift-aware deferral to the B1 cost floor;
- **M2 MEMROUTE** — joint reasoning × episodic-memory routing, directly
  extending Phase-1's locked non-transfer finding.

Both are specified with falsifiable tests and ablations in
`phase2_r5_related_work_gap.md` §4. Neither is claimed novel-by-flat: the
claim is the combination, verified unclaimed across the audited matrix.
STOP conditions are pre-declared (§6 of the gap doc).

## 3. Leak guards and confirmation-data status

- **GSM8K train partition**: disjoint hash-locked BANK / LABEL / VAL
  (40/40/20) with exact+near-duplicate guards against each other and
  against all evaluation splits; a labeled item's own answer can never be
  in its retrieval bank (`phase2_g1_revised_protocol.md` §1).
- **F2 SVAMP 300: RETIRED as fresh confirmation** (was inspected in F2);
  future use = descriptive only.
- **New confirmation candidate: MATH-500** — candidate only; full
  pre-inference lock (revision, 500 IDs, SHA-256, overlap checks, adapter
  tests) required before any use; public-benchmark contamination caveat
  stands.

## 4. Utility protocol and learnability threshold

- `utility = accuracy − λ·(total_tokens/10,000)`; pilot default λ = 0.10
  (1pp ≙ 1,000 tokens), derived from deployment framing before outcomes;
  sensitivity on train-validation only. Controller overhead metered in its
  own units; raw accuracy + tokens + Pareto always reported.
- Learnability gate = **D2**: out-of-sample prediction of utility
  *differences* must beat best-fixed-config utility on VAL with CI
  excluding 0 and beat shuffled-label controls. D1 hindsight oracle is
  optimistic-only, never evidence of attainability.

## 5. Pilot design (NOT executed; budget request only)

TRAIN-side-only diagnostic: 5 configs × 2,400 LABEL items ≈ 12,000
generations on Qwen2.5-1.5B; est. 35–55 min; **budget request ≤ 0.5
aggregate GPU-hours**; preflight = partition locks + overlap guards +
config lock + λ lock; stop rules for guard failure, budget breach, or D2
null. Awaiting Planner authorization — not started.

## 6. GO / PIVOT / NO-GO recommendation

**PIVOT-then-GATE:**
1. PIVOT the algorithmic claim to M1/M2 as scoped above.
2. GO to the 0.5 GPU·h train-only learnability pilot *only after* Planner
   reviews these four documents; pilot outcome decides controller training
   (D2 pass) or a Phase-1-consistent null report (D2 fail).

**Scientific blockers if ignored:** R1 (no within-task variance) remains
the project-defining unknown — the pilot exists to measure it. R5 residual
novelty is narrow; a re-audit is mandatory at submission time.

## 7. Files changed / commits / cleanliness

- Added: `plans/phase2_r5_related_work_gap.md`,
  `plans/phase2_r5_overlap_matrix.csv`,
  `plans/phase2_g1_revised_protocol.md`,
  `plans/phase2_g1_preflight_decision.md` (this file).
- Modified: `status.json` (`phase2_planning` only; V1/V2 frozen fields
  untouched).
- Commit: see `status.json.phase2_planning.last_commit`.
- Working tree clean; pushed to origin/main.

**STOP point reached. Awaiting Planner review.**
