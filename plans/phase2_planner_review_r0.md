# Phase-2 Planner Review R0 — TACC: CONDITIONAL GO for literature and design only
Date: 2026-10-14
Reviewed commit: c8c7206aa428dc2ab24b7701e7e32ac52e3b90e8
Scope: NO new GPU, NO controller code or training.
Verdict: **DESIGN CONDITIONAL GO / IMPLEMENTATION NO-GO** pending novelty and validity corrections.

## Phase-1 evidence boundaries
- Frozen V1 task-family optima differed, but this does not prove item-level predictable heterogeneity.
- F1 REF-B1 +10pp was exploratory on reused GSM8K dev; F2 REF-B1 0pp on inspected public SVAMP. Point estimate not replicated; NO formal significant interaction shown.
- F2 B1 achieved equal observed accuracy to REF with 1.75x fewer total tokens. Hence cost-only constant B1 is a strong baseline and the controller may simply degenerate to it.
- Phase18 evolutionary search vs random produced no detectable advantage in its compact audited search space, not a universal result about all optimizers.

## R5 novelty: close existing methods
Proposed embedding/features -> MLP -> reasoning/memory/context policy is not, by itself, a new algorithm; fixed-backbone versus model routing is INSUFFICIENT separation.

Required direct comparison with ORIGINAL papers:
1. Chen et al. NAACL Findings 2025, When and How to Augment Your Input: Question Routing Helps Balance the Accuracy and Efficiency of Large Language Models. https://aclanthology.org/2025.findings-naacl.200/ . Adapts question augmentation paths including CoT/retrieval.
2. Gerych et al. AAAI 2024, Who Knows the Answer? Finding the Best Model and Prompt for Each Query Using Confidence-Based Search. https://doi.org/10.1609/aaai.v38i16.29763 . Aux predictor routes by input to model+prompt pair.
3. Pan et al. 2025, Route to Reason: Adaptive Routing for LLM and Reasoning Strategy Selection. https://arxiv.org/abs/2505.19435 . Dynamically allocates reasoning strategies / models under budget.
4. Zhou et al., Adaptive-solver framework for dynamic strategy selection in large language model reasoning. https://doi.org/10.1016/j.ipm.2024.104052 .
5. Lu et al. 2026 preprint, Choosing How to Remember: Adaptive Memory Structures for LLM Agents. https://arxiv.org/abs/2602.14038 .
Also check RouteLLM, FrugalGPT, adaptive retrieval and compute routing. Research above is preliminary, NOT comprehensive novelty clearance.
Deliver comparison matrix covering target object, question features, learning signal, single vs multi backbone, cost constraints, prompt/memory/scaffold selection, OOD testing, closest overlapping claim, code. Offer two concrete falsifiable method ideas with a credible novelty distinction, or NO-GO/PIVOT if none.

## Mandatory corrections before implementing anything

**A. Test reuse:** SVAMP 300-item test was already inspected in F2 and motivated Phase-2. It cannot be the NEW untouched confirmatory test for new TACC development. Historical SVAMP may be reported as already-seen exploratory evidence. Pre-lock a new truly unused confirmation partition with dataset IDs, revision, exact+near overlap, and data-governance checks BEFORE choosing method/evaluating outcomes. MATH-500 is only a candidate; no guarantee of pretraining independence.

**B. Memory-bank label leakage:** GSM8K train is proposed for BOTH example bank and training reward labels. A question being labeled must never occur in memory retrieval bank with its answer. Design an immutable, disjoint TRAIN-memory-bank / TRAIN-controller-label / validation partition and assert no exact/near duplicates, including selection/test exclusion.

**C. Learnability not just argmax frequency:** Different winners on per-item binary 0/1 scores may arise from answer noise, ties and random fluctuations. The 95%-same-choice early cutoff has no evidential calibration. Two required diagnostics on strictly training-side data: (1) value-of-routing opportunity above *best fixed action* at the same token budget (with uncertainty); (2) out-of-sample predictability of *utility differences* from pre-inference available question features. Include fixed B1, majority action, simple length/number features, shuffled-label negative control, random policy, and a clairvoyant oracle explicitly labeled an optimistic non-deployable upper bound. Bootstrap on held-out TRAIN-validation; no controller fit/eval on V1/F2 previously exposed test data.

**D. New mechanism:** A simple embedding+MLP router is too close to prior research. Consider confidence-aware abstain-to-cheap-B1, shift-aware calibration, or pairwise utility ranking with a budget constraint only as hypotheses; verify none already exists in R5. Controller novelty must be specific and experimentally falsifiable, not a renamed router.

**E. Utility and overhead:** Define token normalization and lambda from a real deployment cost tradeoff BEFORE outcomes. Include actual prompt+completion tokens and full controller compute/latency, with explicit distinct units; no pretending CPU FLOPs equal LLM tokens. Sensitivity only on fit/validation, not final confirm. Report raw accuracy, tokens and Pareto, not just a manipulable scalar.

**F. Domain tag:** GSM8K-only train has one constant domain ID, so domain-tag-only is not a meaningful learnable OOD baseline. Define zero-shot semantics and train/domains correctly or designate it a descriptive oracle-like task-aware reference. Ensure adaptation vs per-domain static lookup distinguished. B2 labeled 'best manual' was selected on inspected dev; do not present as a ground-truth universal best.

**G. Oracle:** Per-item hindsight winner over evaluated outputs is an optimistic upper bound prone to selection noise, not evidence that an inference-time router could attain that utility. Do not use to declare learnable opportunity.

## Gate sequencing (authorized vs blocked)
- **R5-LIT — AUTHORIZED NOW, 0 GPU**: targeted primary-paper novelty review, overlap matrix, 2 candidate mechanisms or stop decision.
- **G1-DESIGN — AUTHORIZED NOW, 0 GPU**: rewrite experimental protocol fixing leaked train/bank split, definition of λ, new confirmation data eligibility, fairness, label-noise controls, pilot metrics.
- **G1 TRAIN-ONLY GPU PILOT — NOT AUTHORIZED** until Planner reviews R5+G1 revised documents. Future preliminary cap proposed 0.25–0.5 total GPU-hours, must be formally approved.
- **G2 controller training / G3 fresh confirmation — NOT AUTHORIZED** until both scientific value and novelty demonstrated.
- Old V1/V2 manuscript/PDF, frozen F1/F2 artifacts stay unchanged and READY FOR OWNER UPLOAD; Phase2 is a separate optional research track.

## Kimi required deliverables
- plans/phase2_r5_related_work_gap.md
- plans/phase2_r5_overlap_matrix.csv
- plans/phase2_g1_revised_protocol.md
- plans/phase2_g1_preflight_decision.md
- status.json phase2_planning update: R5+G1 DESIGN AUTHORIZED / ZERO GPU / NO controller code
All exact citations with URLs and verified metadata; no unverifiable 'first' claims. Commit and push these docs, stop and request Planner review. No experiments or reinterpreting SVAMP test as untouched.

Outcome criterion: no implementation approval without a concrete originality distinction AND a measurement design for FEATURE-PREDICTABLE positive net utility above the best fixed baseline without leakage.