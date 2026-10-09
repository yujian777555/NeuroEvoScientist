# Kimi Code — F2 conditional authorization (Planner, 2026-10-09)

Repo: https://github.com/yujian777555/NeuroEvoScientist
Branch main | Planner GPT, Executor Kimi.
Owner wants earliest scientifically defensible V2 submission. Work ONLY on minimal F2 confirmation: no optimizer rescue, no large-scale experiments.

## READ FIRST and follow authority order
1. `v2_quality/fasttrack/gates/gate1_decision.md` (Planner audited, **CONDITIONAL GO**)
2. `v2_quality/fasttrack/confirmation_dataset.md` (**corrected HF dataset data**)
3. `v2_quality/fasttrack/baselines_f1.json` (freeze REF, B2, B1 genomes)
4. `v2_quality/fasttrack/protocol_f0.md` (scientific controls)
5. `v2_quality/fasttrack/f1_results.md` and F1 committed predictions
6. `status.json`

## F1 conclusion you MUST retain
- Independent pair audit verified REF vs B2 1.5B GSM8K DEV +1pp, McNemar p=1; REF vs B1 +10pp, p=0.087; 7B DEV +10pp, p=0.041; QASPER DEV REF below B2.
- NO established evolutionary optimizer advantage over manually selected CoT presets; no proof of statistical equivalence.
- F1 is exploratory on already-used DEV. One secondary unadjusted p < 0.05 is NOT a confirmatory claim.
- F1 run_manifest.json only covers last four 7B runs, git SHA unknown; prior F1 provenance incomplete. You must transparently document it, not invent SHAs.
- QASPER F1 predictions omit raw outputs, so do not claim complete raw evidence.
- F0's SVAMP description was wrong: **ChilleD/SVAMP train=700, test=300, license MIT**; use only 300 test as separate evaluation (public; cannot guarantee absence from LLM pretraining).

## PHASE A — F2 PRE-FLIGHT (no GPU)
1. Sync main. Inspect `ChilleD/SVAMP` pinned revision `5e0bf1e5e7c0e9c4bc39180d224f41f3f801b7e`, its actual parquet artifact hashes and original test=300 schema `ID,Body,Question,Equation,Answer,Type,question_concat`. If mirror revision cannot be verified fail closed. **Do not use the train split as confirmation**.
2. Freeze COMPLETE 300 test IDs sorted deterministically (or original fixed order) into `v2_quality/fasttrack/confirmation_lock.json`; record full revision, artifact sha256, exact IDs/order, counts, adapter and parser SHA. Commit and push this lock BEFORE any model predictions or performance-driven label inspection. Avoid reading gold unnecessarily before lock. Do not replace benchmark based on scores.
3. Add new versioned SVAMP adapter UNDER `v2_quality/` (no V1 evaluator modifications), taking input strictly `Body + Question`; `Equation` and `Answer` only for scoring after inference; maintain prompt `reasoning_prompt` and old GSM8K calibration-only memory controller. No SVAMP train labels in exemplar bank.
4. Explicitly design numeric scorer for SVAMP gold answer formatting and model output `#### number`, including negatives/decimals, commas and unanswerable cases if relevant. Prove parsing with synthetic unit fixtures (not SVAMP held-out answers). Fail closed on missing prediction, duplicate ID, parser version mismatch.
5. Check exact/normalized question overlaps with old GSM8K and memory-bank questions without using V1 holdout performance labels. Record potential template/near-duplicate caveat. All candidates share identical test IDs, backbone, version, decoding, prompt builder, scorer and calibration bank.
6. Freeze research: PRIMARY = REF vs B2 paired SVAMP accuracy difference (fair CoT + recency preset, 1 vs 3 exemplars), SECONDARY = REF vs B1 (CoT no-memory), compare capability & prompt+completion token costs; all exploratory additional comparisons. Preselect no more than 3.
7. Ensure exact runtime source commit or archive SHA, model weight revision, dataset SHA, prompt+parser SHA, cache identity, normalized phenotype hash, seed, per-item output/scored values (FULL raw completions stored securely in non-anonymous V2 data), per-cell error count and device GPU-second accounting in ONE manifest for all 3 cells (no overwrite-on-invocation).
8. Run CPU tests for adapter, isolation, lock, baseline equality, hash integrity and scoring; write `v2_quality/fasttrack/f2_preflight.md`. If any failure: push BLOCKED and STOP, do not use GPU.

## PHASE B — F2 SINGLE SHOT (GPU preauthorized after ALL checks pass)
- Qwen2.5-1.5B-Instruct exact pinned model revision; identical decoding, FP16 and prompts.
- Full 300-row original SVAMP TEST, once per locked config REF, B2, B1. No train/test cross-contamination, no retuning, no seed fishing.
- F2 cap **1.0 aggregate GPU-hour**. If at risk, STOP and flag INCOMPLETE; no selective partial averages described as complete.
- Save per-item output, exact scoring, real total input/output tokens, latency, wall/device time, hashes and trace.
- Paired bootstrap CI and exact McNemar; compare multiobjective accuracy vs tokens. If results unfavorable to REF, report them as-is.
- Do not run a 7B model, MATH, or any alternative dataset or optimizer.

## PHASE C — GATE 2 SUBMISSION
Push `confirmation_lock.json`, `f2_preflight.md`, versioned adapter/test code, prediction files, summary, complete manifest, paired stats, `v2_quality/fasttrack/gates/gate2_decision.md`, status.json.
Report:
HEAD and source / model / dataset shas, 300-row lock hash, CPU test counts, number completed, cache use, actual aggregate GPU h, all 3 accuracy/token results and paired CIs/tests, differences from F1, failure traces, Gate2 GO/NO-GO, and **whether proposed paper is exploratory or externally confirmed cross-benchmark**.
Preserve V1 PDF/LaTeX/Results untouched. STOP at Gate2, wait Planner review. No final manuscript rewriting or upload without next authorization.
