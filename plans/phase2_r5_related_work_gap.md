# Phase-2 R5 — Related-Work Originality Audit v2 (TACC)

Date: 2026-10-21 (v2: expanded after Planner R1)
Authority: `plans/phase2_planner_review_r1.md` §2.
Coverage honesty statement (replaces v1's overbroad "10 primary sources
fully read"): **verification depth is per-row in
`phase2_r5_overlap_matrix.csv`** — 12 sources FULL (full text read), 2
ABSTRACT-ONLY (Adaptive-RAG; Mozannar & Sontag), 1 SNIPPET (Chow 1970,
paywalled), 1 FULL with a partially-truncated appendix (PILOT App. D.1).
Code availability was re-audited per row (YES with URL / NO / LINKED-
UNRESOLVED / placeholder-repo-NO).

---

## 1. Papers audited

Core routing/scaffold set (from v1): Chen et al. 2025 (NAACL-Findings,
question-augmentation routing); Gerych et al. 2024 (AAAI,
model×prompt confidence routing); Pan et al. RTR (WWW 2026,
model×strategy, accuracy−λ·token utility, OOD); Zhou et al.
Adaptive-Solver (IPM 2025, heuristic escalation); Lu et al. FluxMem
(2026, memory-structure selection); RouteLLM (ICLR 2025);
FrugalGPT (TMLR 2024); Forge (arXiv 2609.34358); ARC (arXiv 2602.11574);
Adaptive-RAG (NAACL 2024).

Added in v2 (Planner R1): **BudgetMem** (arXiv 2602.06025, runtime
memory-pipeline budget-tier routing, PPO); **Gated-Memory Routing**
(arXiv 2609.00237, multi-agent trajectory memory gates + halting, RL);
**PILOT** (Findings of EMNLP 2025, contextual-bandit LLM routing under a
token budget); **Liang et al.** (TMLR 2024, selective classification under
distribution shift); **Mozannar & Sontag** (ICML 2020, learning to
defer); **Chow 1970** (reject option).

## 2. Novelty verdicts

- **Plain embedding+MLP TACC: PIVOT (accepted by Planner, unchanged).**
  Forge/ARC (frozen-backbone joint config selection with token-costed
  utility) and RTR (supervised accuracy−λ·token per-question selection
  with OOD eval) cover the core.
- **M1 (DEFLECT): plausible research hypothesis, NOT cleared novel.**
  Each half is anticipated: RouteLLM already does per-query
  pairwise-difference prediction (Bradley–Terry win probability) with
  default-to-the-cheap-arm thresholding — between two *models*, with
  preference labels; Liang et al. (and the Chow → SelectiveNet → L2D
  line) own shift/uncertainty-triggered abstention — to a human/void,
  with no config space. The surviving claim is **only the narrow
  combination**: (i) arms = scaffold configurations of ONE frozen
  backbone; (ii) labels = supervised token-costed utility; (iii) deferral
  = dual-trigger (predicted-gain threshold AND shift score) to an explicit
  token-cost floor (B1). Each ingredient is prior art and must be cited
  as such; no "first" or "no prior work" phrasing anywhere.
- **M2 (MEMROUTE): plausible research hypothesis, NOT cleared novel.**
  BudgetMem (query-aware cost-tiered routing of *runtime* memory
  processing) and Gated-Memory Routing (learned retrieval/write gates
  over *trajectory* memory, variable per-step subset — the nearest
  existing analog of recall width) contest any broad "memory routing
  under a cost objective" claim. FluxMem routes memory *structure*. The
  surviving claim is **only**: pre-inference, supervised, per-question
  selection of a *static episodic-exemplar* memory policy (on/off, recall
  width k, exemplar count) *jointly* with reasoning strategy, above one
  frozen backbone, under token-costed utility — with BudgetMem /
  Gated-Memory-Routing / FluxMem cited as the closest runtime/structure
  memory routers and the static-exemplar vs runtime-trajectory
  distinction made explicit.
- **Framing claims owned by others (never claim):** "cost-aware per-query
  routing under a user budget" (PILOT; Chen et al. 2022 lineage);
  "online adaptation to query-distribution shift" (PILOT App. D.1).

**Unresolved audit item (carried, not hidden):** a dedicated scan for
conformal-prediction-based deferral to cheaper models was not completed
(one 2026 preprint, arXiv:2610.02487, self-describes decision-aware
deferral as open; not fully verified). Any future submission requires a
second targeted pass on this and on exemplar-selection literature.

## 3. Candidate mechanisms (restated with narrowed claims)

### M1 — DEFLECT (narrowed)

Pairwise utility-difference prediction Δû(cfg, B1) from pre-inference
features; select argmax only if max Δû > δ **and** shift_score(x) < τ;
else fall back to B1 (token-cost floor). Claim = the combination over a
single frozen backbone's config space with token-costed supervised labels
and dual-trigger cost-floor deferral — no broader.
Falsifiable tests: net utility vs best-fixed > 0 with paired CI
(excluding 0) on locked data; deferral rate ↑ and utility loss ↓ under
induced shift vs a non-deferring router; ablation replacing difference
prediction with absolute-utility prediction must degrade out-of-sample.

### M2 — MEMROUTE (narrowed)

Joint per-question routing of reasoning strategy × static
episodic-exemplar memory policy (on/off, k, exemplar count) under
token-costed utility, single frozen backbone. Motivated by Phase-1's
locked finding that memory benefit is task-/scale-dependent and failed to
transfer to SVAMP. Claim = the static-exemplar memory axis in joint
scaffold routing — no broader.
Falsifiable tests: utility vs both fixed anchors (B1, REF/B2) with paired
CIs; memory-axis ablation accounts for the dev→locked-test gap; memory-ON
rate correlates with a pre-specified feature on train-side data.

## 4. STOP conditions (pre-declared)

- Any located work (incl. the unresolved conformal-deferral scan or a
  v2+ of Forge/ARC/BudgetMem) covering the narrowed combination → STOP
  the algorithmic claim; retain Phase-1 audit paper only.
- D2 learnability null (G1 protocol §5) → STOP TACC; report the null.

## 5. Mandatory citation set for any future Phase-2 paper

Forge; ARC; Route-to-Reason; Chen et al. 2025; BudgetMem; Gated-Memory
Routing; FluxMem; Adaptive-RAG; PILOT; RouteLLM; FrugalGPT;
Adaptive-Solver; Gerych et al.; plus deferral lineage (Chow 1970;
Mozannar & Sontag 2020; Liang et al. 2024). Comparison framing must be
mechanism-level (decision timing; query vs execution-state features;
static exemplar vs runtime/trajectory memory; cost model; deferral
trigger), as tabulated in `phase2_r5_overlap_matrix.csv`.
