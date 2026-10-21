# Phase-2 R5 — Related-Work Originality Audit (TACC)

Date: 2026-10-21
Status: DOCUMENT-ONLY audit, 0 GPU. Authority: `plans/phase2_planner_review_r0.md`.
Method: full-text reads (ACL Anthology / AAAI OJS / arXiv HTML / publisher
pages) of every paper; fact sheets recorded in
`plans/phase2_r5_overlap_matrix.csv`. Verified flags are per-paper in the
matrix. Nothing below rests on search snippets alone.

---

## 1. Papers audited (all primary sources verified)

| Paper | Venue | One-line mechanism |
|---|---|---|
| Chen et al., *When and How to Augment Your Input* | Findings of NAACL 2025 | BERT router per question over 5 augmentation paths (direct / +CoT / rewrite / RAG / don't-know), single frozen QA LLM, latency-costed labels |
| Gerych et al., *Who Knows the Answer?* | AAAI 2024 | confidence regressor picks (model × static prompt template) per query |
| Pan et al., *Route to Reason* (RTR) | WWW 2026 | supervised MLPs predict correctness + output tokens per (model × strategy); argmax of accuracy − λ·tokens; OOD benchmarks |
| Zhou et al., *Adaptive-Solver* | IPM 2025 | learning-free confidence-triggered escalation over (model, samples, prompt method, decomposition granularity); $ cost |
| Lu et al., *Choosing How to Remember* (FluxMem) | arXiv 2026-02 | supervised per-turn selection of memory structure (Linear/Graph/Hierarchical), single frozen backbone, no cost term |
| Ong et al., *RouteLLM* | ICLR 2025 | supervised strong-vs-weak **model** routing with cost threshold, OOD eval |
| Chen et al., *FrugalGPT* | TMLR 2024 | LLM-API cascade under a hard $ budget |
| **Forge**, *Form-Optimal Routing of Grounded Evidence for Frozen LLM Agents* | arXiv 2026-09-28 | **per-question joint (evidence form × thinking depth) above a single frozen host, trained from measured F1 − λ·token utility** (Boltzmann distillation + GRPO) |
| **ARC**, *Learning to Configure Agentic AI Systems* | arXiv 2026-02 (v5 2026-10) | **per-query joint (workflow × tools × token-budget × prompt) over a frozen agent system via RL+SFT** |
| Jeong et al., *Adaptive-RAG* | NAACL 2024 | per-question retrieval-depth classifier (none/single/multi-step RAG) |

## 2. Novelty verdict for the original TACC formulation

**Decision: PIVOT.** The original "embedding + MLP router over
reasoning/memory/context configs, trained on accuracy − λ·token labels"
does **not** survive as a standalone algorithmic contribution:

- The *economic formulation* (per-question, supervised, accuracy −
  λ·token-cost, OOD evaluation) is established by **RTR** (published,
  WWW 2026) and anticipated by FrugalGPT/RouteLLM.
- The *single-frozen-backbone per-question scaffold selection* core is
  directly claimed by **Forge** (evidence form × reasoning depth, frozen
  host, token-utility training) and **ARC** (workflow × budget × prompt,
  frozen system).
- The *memory-axis* selection exists in **FluxMem** (structure choice) and
  retrieval-depth selection in **Adaptive-RAG**.
- "Fixed-backbone vs model routing" alone is **not** a sufficient
  separator — Forge and ARC are explicitly frozen-backbone.

## 3. Residual gaps that remain credible (verified against the matrix)

After the full audit, three distinctions are not claimed by any audited
paper *in combination*:

- **G1 — the episodic-memory policy axis**: recall width / exemplar count /
  memory on-off selected per question, *jointly* with reasoning strategy.
  Forge routes corpus evidence form, FluxMem routes memory structure,
  ARC routes tools — none routes episodic exemplar memory jointly with the
  reasoning strategy.
- **G2 — difference-prediction training**: all audited routers predict
  absolute correctness/cost per arm. Predicting **pairwise utility
  differences** (cancelling the item-difficulty main effect) from
  pre-inference features is unclaimed.
- **G3 — shift-aware deferral to a cost floor**: abstaining from routing
  (falling back to the cheapest adequate fixed configuration) when the
  predicted utility gain is uncertain or the input is off-distribution.
  Chen et al.'s "don't know" path is *answer* abstention, not
  *cost-floor deferral*; nobody couples scaffold routing with a
  distribution-shift-triggered fallback to a token-cost floor.

A fourth, methodological distinction (pre-locked cross-benchmark
confirmation with forensic provenance) is real but is a *protocol*
contribution, inherited from this project's Phase-1, not an algorithmic
one.

## 4. Two falsifiable candidate mechanisms (post-PIVOT)

### M1 — DEFLECT: Difference-prediction router with shift-aware cost-floor deferral

Per item, the controller predicts, from pre-inference features only, the
pairwise utility differences Δu(cfg, B1) between each candidate config and
the cost-floor config B1 (no-memory CoT). Selection rule:

```
choose argmax_cfg Δû(cfg, B1)  iff  max Δû > δ  AND  shift_score(x) < τ
otherwise fall back to B1
```

- δ, τ pre-locked on train-validation; shift_score from feature-space
  density (fit on train only).
- Novelty claim (narrow, checkable): pairwise-difference supervision +
  shift-triggered deferral to a cost floor in scaffold space (G2+G3).
- Falsifiable tests: (i) on locked confirmation data, net utility over
  B1 > 0 with paired CI; (ii) deferral rate ↑ and utility loss ↓ under
  induced distribution shift vs a non-deferring router; (iii) ablation:
  absolute-utility prediction instead of difference prediction must
  degrade out-of-sample selection (train-side).

### M2 — MEMROUTE: Episodic-memory-aware joint configuration routing

Per-question joint selection where the differentiating axis is episodic
memory: {none} ∪ {recency(k), retrieval(k), exemplar_count} crossed with a
small reasoning-strategy set, trained with utility labels. The central
claim is *when episodic exemplar memory pays its token cost* — directly
extending Phase-1's locked finding (memory benefit task- and
scale-dependent, non-transferring on SVAMP) into a per-question learnable
question.

- Novelty claim (narrow, checkable): first per-question joint
  reasoning × episodic-memory policy router with token-costed utility
  (G1), with the Phase-1 non-transfer result as the motivating measurement.
- Falsifiable tests: (i) TACC-mem vs no-memory fixed B1 and vs
  always-memory fixed REF/B2 on utility; (ii) memory-axis ablation must
  account for the transfer gap (dev→locked-test); (iii) memory ON rate
  correlates with a pre-specified feature (e.g. multi-step density) on
  train-validation.

**Both candidates keep**: discrete audited config set, single frozen
backbone (Qwen2.5-1.5B), supervised utility labels, token-metered cost,
pre-locked confirmation protocol.

## 5. Closest-method comparators (mandatory in any future paper)

Forge and ARC must be cited and compared directly (mechanism table), plus
Chen et al. 2025 (path routing), RTR (utility form), FluxMem (memory
axis), Adaptive-RAG (retrieval depth), RouteLLM/FrugalGPT (cost-aware
model routing). No "first" claims anywhere; the strongest permitted phrasing
is "to our knowledge, no prior work jointly routes episodic-memory policy
and reasoning strategy per question under a token-costed utility with a
pre-locked cross-benchmark protocol" — and only if a second audit pass at
submission time still supports it.

## 6. What would make us STOP instead of PIVOT

- If Forge/ARC are extended (or other 2026 work is found) covering the
  episodic-memory axis with token-costed utility: STOP the algorithmic
  claim; TACC survives only as an audit-protocol study.
- If the G1 learnability diagnostics (see `phase2_g1_revised_protocol.md`)
  show no feature-predictable utility differences above the best fixed
  config: STOP TACC entirely; report the null as a Phase-1-consistent
  finding.
