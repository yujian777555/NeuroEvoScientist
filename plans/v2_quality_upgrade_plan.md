# NeuroEvoScientist — V2 Paper Quality Upgrade Plan
Date: 2026-10-08
Status: PLANNED / NOT EXECUTED
Roles: GPT = Planner/reviewer; Kimi = Executor.
Authority: GitHub origin/main, locked evidence, source code and versioned protocols.

## 0. Decision and protected baseline

The owner explicitly states that submission is not time-critical. Stop the 2026-10-12 ARR submission countdown. Do not claim that the previous V1 submission PDF has been submitted.
Protect and preserve V1 at commit 8fa8945 and review PDF SHA-256 e42191b0502f4b1ca7f7ed2bdd6b8b735ab0755294e185d2cd83156d22ae931d (the later metadata-only commits do not alter the PDF).
Historical Phase-17–21 result artifacts, selection locks, old LaTeX/PDF and all other previously frozen evidence are READ-ONLY. No silent reruns, changing a cached result, rewriting original selection locks, or relabeling an already inspected holdout as untouched. New work belongs in v2_quality/ and in new versioned experiment/result paths only.
V1 claims that must not be inherited as unqualified V2 claims: ENSS > random; Mamba benefit; across-task own-task superiority; memory always helps; full backbone NAS; strong absence of a QASPER capability issue.

## 1. Scientific review finding: baseline confounding

The reported V1 GSM8K advantages (+29.0pp at 1.5B, +16.7pp at 7B) are against the best of four fixed baselines that all use Direct reasoning. The selected A_gsm uses CoT. Its memory-disabled paired reference already obtains approximately the same accuracy at 1.5B (51.93% vs 51.85%) with fewer prompt tokens, whereas GSM8K-7B gains 12.6pp with memory.
Therefore do NOT attribute the V1 strongest-fixed margin to evolutionary search, joint configuration optimization, or memory without additional controlled evidence.
Current Phase-18 compact-space search efficiency shows no evolutionary advantage versus budget-matched random. Preserve this result.

## 2. Success criteria and priority

P0 (MANDATORY): Determine fairly whether task-conditioned configuration search improves on strong hand-designed and CoT-matched baselines in capability, actual prompt tokens, and Pareto tradeoffs.
P1 (CONDITIONAL): Analyze interactions among reasoning, memory and context under matched factors. Test whether joint co-design is more than the sum of independent tuning.
P2 (CONDITIONAL): Evaluate structured-space evolutionary search versus correctly budget-matched random in a new clean analysis, without seeking an advantage by cherry-picking seeds or budgets.
P3 (CONDITIONAL): Test cross-model-family and optionally cross-task generalization using an independently locked confirmation evaluation.
P4: Package a reviewer-defensible manuscript with honest positive or negative results.

Research objective is falsification and clearer attribution, not 'make ENSS beat random'.

## 3. Global experimental integrity protocol

Before any V2 GPU execution:
- Write v2_quality/protocol_v2.md: claims, hypotheses, independent variables, train/calibration/dev/test boundaries, config definitions, baseline set, statistics, multiplicity treatment, inference controls, stopping rules and planned outputs.
- Write v2_quality/dataset_registry.json with source, immutable revision/hash, item count, split, exact-overlap and near-duplicate checks, contamination limitations, and licenses. Do not select new confirmation items after viewing performance.
- New confirmation material must be independent of the already repeatedly inspected Phase-20 holdout. The prior GSM8K test[100:1319], PubMedQA samples[100:500], and QASPER items[50:150] CANNOT be called untouched for new V2 hypotheses. An independent set may be a truly separate suitable benchmark or a separately reserved source, with task/distribution caveats explicitly documented. No guarantee public sets are absent from LLM pretraining.
- Partition discovery/dev and final confirm; lock candidate shortlist, metric, parser, item IDs and hypotheses before revealing final confirm. If a clean confirmation set cannot be found, report V2 as exploratory and do not fabricate a confirmatory label.
- Evaluate same model revision, decoding, quantization, hardware/precision where feasible, prompt template, item set and answer parser per paired comparison. Count actual prompt and generated tokens; include cost/failure rate; do not confuse wall-time changes due to hardware scheduling with model improvements.
- Paired item-level bootstrap CI; exact McNemar for binary outcomes and exact paired sign test for non-tied QASPER item F1; report effect sizes and uncertainty rather than p-only conclusions. Account for multiplicity for confirmatory comparisons; define primary endpoints in advance. Blind failure-case categorization where possible.
- Keep all seeds and attempts in a manifest. Record run_id, git_sha, model+dataset sha, seed, runtime, config, outputs, cache fingerprints, token accounting, GPU-hours, failure traces.
- Implement fail-closed guards against cached-parameter mismatch, data leakage, hidden use of holdout for selection, missing predictions, and duplicate item IDs.
- Do not improve scores by changing the parser after seeing confirm outputs. QASPER parser changes, if needed, must be separately versioned as an evaluation sensitivity study applied to ALL compared configurations.
- Preserve V1 folder and V1-ready package. Never overwrite V1 PDFs or historical result CSV/JSON.

## 4. Phase V2-0 — audit and protocol freeze (estimated 2–4 workdays)

Read actual source and provenance before changing code: configs/phase20_protocol.yaml, configs/phase20_structured_search_space.yaml, results/phase20_selection_lock.json, results/phase20_statistics.json, results/phase20_holdout_results.csv, src/evaluator, src/evolution, Phase-18 search-audit artifacts, tests, old paper/phase21_tables.md.
Deliver:
1. v2_quality/audit_baseline_fairness.md: table mapping each old baseline's reasoning/memory/context; identify confounded comparisons; recompute no new scores.
2. v2_quality/protocol_v2.md + dataset registry + compute_budget.md + run_matrix.csv + tests for isolation.
3. v2_quality/archival_discrepancies.md listing obsolete tables such as paper/phase21_tables.md and verifying whether old copies reside in supplementary. Mark old documents SUPERSEDED (do not silently rewrite historical measurements).
4. Record confirmation-set viability and license before any experimental green light.
GATE 0: No GPU launch until protocol, candidate set, cost budget, and confirmation plan are reviewed by Planner. If data isolation is impossible, declare exploratory-only scope.

## 5. Phase V2-1 — strongest fair baselines (estimated 4–8 workdays)

Primary evaluation on DEV/DISCOVERY partitions with no confirm peeking:
- Fixed Direct+Full/recency and existing historical comparisons (descriptive only).
- CoT+Full+NO memory and carefully matched prompt/template.
- CoT+Full+recency at exemplar counts and recall widths fixed before evaluation.
- CoT+Full+lexical retrieval (term-frequency cosine or hashed bag-of-words cosine; no false TF-IDF claim).
- CoT with shorter/exemplar/context budget, plus a reasonable low-token strong fixed preset.
- Selected V1 A_gsm frozen as reference (not retrained/retuned).
For each, compare capability, tokens/input, generated tokens, efficiency definition, latency distribution, and cost-matched Pareto frontier. Report both equal-compute and token-budget-qualified results, not only raw accuracy. If prompts differ by memory/exemplars, explain their causal role explicitly; no false 'single-gene ablation' claim for mixed changes.
GATE 1: A short 1–2 page signed review memo (v2_quality/gates/gate1_decision.md) must answer whether search adds value over the best pre-fixed CoT preset. If no clear advantage, do not continue with 'search wins' framing; pivot to a controlled configuration-selection/negative-results paper. No requirement to force a positive result.

## 6. Phase V2-2 — mechanism and interaction (estimated 5–10 workdays, conditional)

Run a compact, pre-specified factorial within manageable budgets: Memory {off, recency-on}, Reasoning {Direct, CoT}, Context {full, shorter budget}, yielding 8 cells, on GSM8K and at least one structurally different task. Additional retrieval contrasts optional if preregistered on DEV before confirm. Keep backbone and per-cell prompts/decoding fixed and report main and interaction effects with CIs, prompt tokens, and possible treatment-by-task differences. Do not conflate seed variance with item-paired variance.
GATE 2: Demonstrate credible interaction benefit or document none, and decide whether 'co-design synergy' is supportable. If none, position co-design as a configuration framework, not a mechanism superiority result.

## 7. Phase V2-3 — structured search audit (estimated 5–10 workdays, conditional)

Separate V1 48-point compact oracle from V2 structured-space search. On same DEV budget compare ENSS/NSGA-II-style selector and unbiased uniform random or valid budget-matched alternative, with matching unique phenotype evaluations (avoid duplicate/cached evaluations artificially improving one side), same seed schedule, time budget, candidate budget and stopping rules.
Preselect budgets, e.g. {12,24,48,96} unique evaluations, and at least 10 search seeds as feasible. Use 20 seeds if budget supports; report actual total. Evaluate best-of-budget, quality-vs-cost Pareto front/hypervolume, AUC, regret if reference available, and variation with CIs. No full oracle claim for combinatorial space without exhaustive enumeration.
GATE 3: Negative result remains acceptable. Do not iterate the algorithm to find a lucky win after viewing confirm results.

## 8. Phase V2-4 — external validity and confirmation (estimated 5–12 workdays, conditional)

On a separate INSTRUCT model family from Qwen (choose from actually accessible and appropriately licensed candidates after a one-day feasibility gate), transfer the fixed small shortlist WITHOUT re-search; no model-family advantage claim without a fair independent validation.
Use the prelocked independent confirmation set exactly once for the pre-specified primary comparisons. Evaluate generalization and cost at matching decoding, answer parsing, and budget policy as much as model tokenizers permit; report tokenizer-normalized caveats. No new task/model needed if gate1 or gate2 has already invalidated the expected scientific value.
GATE 4: Every primary result traceable to frozen protocol, named configuration, exact model/dataset revisions and prediction files. Be clear that distinct domains may shift benchmark difficulty.

## 9. Phase V2-5 — manuscript and final audit (estimated 5–8 workdays)

Prepare new v2_quality/paper/ manuscript and independently compiled PDF, while preserving paper/arr2026 and deliverables/final_submission as V1. Include:
- A primary fair CoT-matched baseline table and paired effect estimates;
- An explicit 'search method vs architecture choice' decomposition;
- At least one interaction plot or careful null analysis;
- Direct ENSS vs Random performance-vs-budget figure if V2-3 is run (do NOT cite the V1 landscape figure as if it were an optimizer comparison);
- Correct QASPER F1 statistics and extraction diagnosis;
- Transparent selection/confirmation flow and contamination limits;
- Limitations acknowledging 1–2 model families, test scope, exploratory vs confirmatory status, and baseline coverage.
Audit BibTeX, anonymity, PDF pagination, public release license and final claims. Author determines venue and timing later. Do not promise CCF-B acceptance.

## 10. Execution order and strict reporting

Proceed strictly gate by gate. Do NOT launch all phases in parallel. Stop after Phase V2-0 and REQUEST PLANNER REVIEW based on its committed Gate 0 artifact. Planner will decide next-stage budget and exact tasks using repository evidence. Kimi must not self-authorize V2-2/3/4 compute after failing a gate.
For each iteration, commit code+test changes separately from experimental outputs and keep working tree clean. Push to origin/main if authorized; do not rewrite history. Use meaningful commits; update status.json with v1_frozen info and v2_stage/gate after completing tasks.
Each delivery report: HEAD, files changed, test commands/results, data/protocol lock sha, seeds, actual GPU-hours, completed/failed/missing runs, deviation register, citations to result paths, and explicit GO/NO-GO proposal.
Do NOT fabricate completion, '100% green', reviewer acceptance, or time-to-finish.

## 11. Planning estimates, not promises

Assuming reliable access to four A800-class 80GB GPUs, already working scripts, and an obtainable independent confirmation set:
- initial protocol + fairness audit 2–4 workdays;
- strong baselines 4–8 workdays;
- interaction / structured search 10–20 workdays when justified;
- external confirmation 5–12 workdays;
- writing and review 5–8 workdays, some overlap possible after results lock.
Approximate elapsed time: 4–7 weeks for a focused improvement track; 7–10+ weeks for the full program with new independent validation, GPU failures or substantial reviewer-quality revisions. An early negative Gate1 can close compute and yield an honest revised paper in ~2–4 weeks. Do not treat these ranges as guaranteed or promise work in the background.
