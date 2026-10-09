# SVAMP Confirmation Dataset — Gate 1 Corrected Registry

Date: 2026-10-09; supersedes the inaccurate F0 description.

## Actual verified source

- Dataset: Hugging Face `ChilleD/SVAMP`.
- F0-pinned repository revision: `5e0bf1e5e7c0e9c4bc39180d224f41f3f801b7e` (must resolve to a reproducible exact dataset snapshot before running).
- Dataset card reports **700 train rows and 300 test rows**, totaling 1000, **not 700 test rows**.
- Required source fields: `ID`, `Body`, `Question`, `Equation`, `Answer`, `Type`, `question_concat`. Prediction input MUST come from `Body` + `Question` only, never `Equation` or `Answer`.
- HF dataset card reports **MIT** license, **not Apache-2.0**. Confirm file-level notices before redistribution.
- Original SVAMP authors' challenge set includes 1000 items; the ChilleD mirror is split into 700 train/300 test. The source's 300-row test split is the intended V2 confirmation partition. No mixing of train/test.
- This is a separate public math-word-problem **benchmark**, not an independent same-distribution GSM8K holdout and not evidence of immunity to pretraining contamination.
- References: https://huggingface.co/datasets/ChilleD/SVAMP and https://github.com/arkilpatel/SVAMP

## Confirmation lock before ANY model inference or gold read

1. Resolve pinned revision and file sha256, list split names and row counts using metadata/schema access.
2. Freeze **ALL 300 test IDs** (prefer the whole original test rather than a performance-contingent subset) and exact ordered IDs + file/content hashes in `v2_quality/fasttrack/confirmation_lock.json`; commit and push before running a model.
3. Independently map `Body + Question` -> `question`, `Answer` -> numeric scoring value, exact `ID` to item_index using a versioned adapter. Equation is NEVER provided to prompt.
4. Check exact and normalized duplicate texts against V1 GSM8K dev/holdout/calibration before inferencing; duplicates require a pre-registered exclusion rule and should be documented before model outputs. Do not touch the V1 holdout predictions/labels to tune prompts or parser.
5. Only after the immutable lock is committed, test parser/gold extraction with a separate synthetic fixture (no SVAMP test labels) and run evaluator adapter unit tests.
6. REF/B1/B2 must use the same old GSM8K calibration-only exemplar bank; keep cross-benchmark transfer protocol clear. No SVAMP train labels as memory.
7. If validation fails, **STOP** and report, no automatic switch to MATH after observing scores; changing confirmation benchmark requires Planner approval and a new pre-inference lock.
8. All V2 runs require a fully versioned manifest with actual runner source SHA (if VM lacks .git, record the exact source archive SHA256 or immutable GitHub commit mapped to copied script), model weight revision(s), dataset artifact sha, per-cell prompt+completion token totals, GPU device time, cell success/error, seed, cache identity, and complete per-item evidence.

## Intended F2 conclusion

One-shot cross-benchmark, unseen-to-project SVAMP test set, 3 **prelocked** configurations REF/B2/B1, Qwen2.5-1.5B-Instruct (exact revision). A paired contrast can substantiate relative transfer to SVAMP, **not** prove search algorithm superiority or a universal scale-dependent memory effect. Treat public pretrained contamination as an explicit limitation.
