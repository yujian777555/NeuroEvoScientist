# Kimi Code: Phase-2 R5 literature audit + G1 design correction (NO GPU)
Planner review authority: plans/phase2_planner_review_r0.md.
Repository: https://github.com/yujian777555/NeuroEvoScientist
Branch: main. GPT=Planner, Kimi=Executor.

## Required first step
Sync the current origin/main (do not overwrite concurrent changes). Read completely:
1. plans/phase2_planner_review_r0.md — **highest current Phase-2 authority**
2. plans/phase2_controller_design.md
3. plans/phase2_experiment_design.md
4. plans/phase2_risk_analysis.md
5. status.json
6. Existing F1/F2 experimental *summaries* and frozen configuration identities, for motivation only; no new evaluation against previously inspected test outcomes.

## Work authorization
You may conduct PUBLIC paper/web research and make DOCUMENT-ONLY protocol revisions. NO new training, NO new inference, NO GPU, NO controller implementation, NO modifications to any V1/V2 submission PDF/source or historical experiment data, and NO claimed uncontaminated evaluation on F2 SVAMP. Do not run code except ordinary file inspection and document checks.

## Workstream R5 — literature originality challenge
Examine full papers and verified primary publication metadata for:
- Chen et al. 2025 Findings NAACL, When and How to Augment Your Input — https://aclanthology.org/2025.findings-naacl.200/
- Gerych et al. AAAI 2024, Who Knows the Answer? — https://doi.org/10.1609/aaai.v38i16.29763
- Pan et al. 2025, Route to Reason — https://arxiv.org/abs/2505.19435
- Zhou et al. 2025 Adaptive-Solver — https://doi.org/10.1016/j.ipm.2024.104052
- Lu et al. 2026, Choosing How to Remember — https://arxiv.org/abs/2602.14038
- RouteLLM, FrugalGPT, budgeted prompt routing, adaptive inference, memory selection, and any more-direct 2025–26 scaffold controller you discover.
Research whether those already select prompting/reasoning/retrieval/memory policy on a per-question basis. Do NOT assume that only model routing exists. Use URLs, exact publication dates, paper-specific comparison and code availability.
Deliver plans/phase2_r5_related_work_gap.md and plans/phase2_r5_overlap_matrix.csv.
Make a reviewer-style novelty decision: GO / PIVOT / STOP for original embedding+MLP TACC. If GO, name a precise previously unaddressed mechanism, give TWO falsifiable candidate algorithms, ablations and direct closest-method comparators. Do not assert that the mechanisms are novel until verified.

## Workstream G1 — corrected LEARNABILITY protocol (documentation, 0 GPU)
Deliver plans/phase2_g1_revised_protocol.md:
1. Lock separate GSM8K-TRAIN memory bank and controller-label subsets and internal validation, ban identical / near-duplicate training questions being retrieved with gold answers during their own evaluation.
2. Retire reused F2 SVAMP TEST as 'fresh independent confirmation'. It was previously inspected and used in selecting the research hypothesis. Define a genuinely unused confirmation candidate and require dataset/ID/revision/overlap lock before ANY future outcomes; MATH-500 is a possibility not guaranteed independent of model pretraining.
3. Specify a small preselected configuration set, including B1 (no-memory CoT) as primary COST floor and REF/B2 as accuracy anchors. Avoid casually calling dev-selected B2 global best.
4. Gate1 training-side *opportunity* metric: best oracle-derived (retrospective only, optimistic due selection) per-item utility minus best constant config utility, uncertainty and tie rates, under equal total cost accounting. Separately train a cheap out-of-sample diagnostic to test whether input-only features predict DIFFERENCES in utility. Include shuffled-label and feature-only baselines. Do NOT use 'percentage of per-item argmax varies' as sufficient evidence of learning.
5. Define utility units in advance, lambda selection based on acceptable price of a correct answer / deployment budget, prompt+completion costs and encoder/controller runtime. Distinguish FLOPs/latency from tokens. No tune lambda on fresh test.
6. Correct domain tag: GSM8K-only training cannot learn cross-domain routing from a constant domain ID. Define what is and is not available at deployment and a valid domain-tag baseline or remove it.
7. Document simple deterministic/equal-input greedy decoding noise limitations; distinguish per-item hindsight oracle from predictive policy, and no inference-time outcome leakage.
8. Design a tiny TRAIN-only GPU pilot with an upper-bound request (suggest 0.25–0.5 aggregate GPU-hours), explicit preflight and stop rules, but DO NOT execute it. Give expected time, cost and number of config×example evaluations for Planner review.
9. Classify any reuse of historic F1/F2 pairs as descriptive/hypothesis-generating, NOT new confirmation, and make the primary method-vs-best-fixed utility/accuracy+token endpoints clear.

## Completion and stop
Produce plans/phase2_g1_preflight_decision.md documenting:
- papers audited and direct novelty collisions;
- strongest defensible differentiator or STOP recommendation;
- training/memory leak guard and new confirmation dataset status;
- lambda/utility protocol and measurable learning-opportunity threshold;
- Pilot cell count and budget request, not actual GPU use;
- GO / PIVOT / NO-GO to later pilot, scientific blockers;
- files changed, git commits, clean status.
Update ONLY status.json.phase2_planning with latest planner review state; retain all v1/v2 frozen submission status and original artifacts.
Commit and push to origin/main. STOP for Planner review. No implementation or pilot until new authorization.
