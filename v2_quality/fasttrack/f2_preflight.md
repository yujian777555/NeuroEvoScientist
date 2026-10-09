# F2 Preflight — SVAMP Confirmation (Phase A, no GPU)

Date: 2026-10-09
Executor: Kimi (Executor role; Planner authorization in `plans/v2_f2_authorized_kimi_prompt.md`)
Status: **ALL HARD CHECKS PASSED — cleared for Phase B single-shot GPU run**

This document records the complete Phase-A evidence required by the F2
authorization. No GPU inference was performed before this file and the
companion `confirmation_lock.json` were committed.

---

## 1. Dataset verification (hard check)

- Dataset: `ChilleD/SVAMP`, HF revision `5e0bf1e5e7c0e9c4bc39180d224f41f3f801b7ef`
  (matches the revision registered in `v2_quality/fasttrack/confirmation_dataset.md`).
- Local copies (provenance-frozen, read-only for the run):
  - `v2_quality/fasttrack/data/svamp_test.json` — 300 rows,
    sha256 `9b5590fce66ea78ecfc7d0fc4a91fb801ffe289340269f8d9d28b21acad04ae6`
  - `v2_quality/fasttrack/data/svamp_train.json` — 700 rows,
    sha256 `bb3b4cd2957f07643bbf9f8f8f5faba3bfb47fcb1d9034655b03060a76675e2b`
    (recorded for provenance only; **NEVER used**)
- Fields per row: `ID`, `Body`, `Question`, `Equation`, `Answer`, `Type`.
- Split used: `test` only, all 300 items, original file order.

## 2. Confirmation lock (hard check)

- `v2_quality/fasttrack/confirmation_lock.json` created **before any inference**,
  containing:
  - all 300 test IDs in original order;
  - `test_ids_sha256 = 4e462b134a5cf3dd633944804318ec2a48e67fc1e58f6f8e2c329cf9b22bc03f`;
  - locked configs: `REF`, `B2`, `B1` (genomes frozen in
    `v2_quality/fasttrack/baselines_f1.json`);
  - backbone `Qwen/Qwen2.5-1.5B-Instruct`, model revision
    `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`;
  - primary contrast REF vs B2; secondary REF vs B1;
  - adapter/scorer source sha256
    `0869a9e101fc3512755154991dfb126a2cf88a6b295847346d250899af7f369d`
    (= sha256 of `v2_quality/svamp_adapter.py`, verified identical at preflight).
- Lock generator: `src/scripts/f2_freeze_lock.py`
  (sha256 `4fe3e4e551ba1b87ce8b7db634eebbe08ada970fabc2e1eb4da64d242343c381`).

## 3. Locked configurations (from `baselines_f1.json`, unchanged)

| Config | memory_type | memory_k | exemplar_count | reasoning | reasoning_depth | context_mode |
|--------|-------------|----------|----------------|-----------|-----------------|--------------|
| REF    | recency     | 3        | 1              | cot       | 3               | full         |
| B2     | recency     | 3        | 3              | cot       | 3               | full         |
| B1     | none        | 0        | 0              | cot       | 3               | full         |

REF is the F1 search-selected configuration (A_gsm); B2 is the strongest
CoT-matched preset; B1 is the no-memory CoT control. No configuration was
re-selected, re-tuned, or modified for F2.

## 4. Adapter and scorer (hard check)

- `v2_quality/svamp_adapter.py` (version `svamp-adapter-v1`):
  - `to_prompt_question(row)`: uses **Body + Question only**;
    `Equation`/`Answer` never enter prompts.
  - `extract_model_answer(completion)`: last numeric value after the `####`
    marker; tolerant of negatives, decimals, and thousands separators.
  - `score(pred, gold)`: exact numeric equality.
  - `load_locked_test_rows(...)`: validates rows against
    `confirmation_lock.json` (count, order, ID hash); any mismatch is a hard
    error, so drift between lock and data is impossible at run time.
- Calibration/exemplar bank rule (unchanged from V1/F1): memory exemplars come
  from the GSM8K train calibration bank only. SVAMP train is never read by the
  agent builder.

## 5. Overlap / contamination checks (hard check + caveat)

- Normalized exact-match overlap between the 300 locked SVAMP test items and
  the full GSM8K corpus (train+test, Body+Question normalization):
  **0 / 300**.
- Caveat carried into the paper: SVAMP is a **public benchmark**; pretraining
  contamination cannot be ruled out. F2 is a **cross-benchmark** confirmation,
  not a same-distribution independent holdout. These limitations are recorded
  in `confirmation_lock.json.caveats` and must appear in the paper wording.

## 6. Isolation of V1 artifacts (hard check)

- F2 writes only to new paths:
  `v2_quality/fasttrack/f2_results/` and `v2_quality/fasttrack/caches/f2_*`.
- No V1 file is touched: `paper/arr2026/`, `deliverables/final_submission/`,
  historical `results/`, `experiments/`, `configs/`, selection locks remain
  read-only. Verified: Phase-A diff contains only new V2 files.

## 7. CPU test suite (hard check)

`python -m pytest tests/test_v2_f2.py -q` → **5/5 passed** (2026-10-09):

1. `test_adapter_prompt_uses_body_plus_question_only` — prompt mapping
2. `test_scorer_numeric_formats` — numeric scorer incl. negatives / decimals / thousands separators
3. `test_lock_integrity` — 300 IDs, order, hash consistency
4. `test_lock_predates_inference` — lock exists and is consistent before run
5. `test_no_overlap_with_gsm8k_calibration_bank` — 0/300 normalized overlap

## 8. Provenance & traceability plan for Phase B (per authorization §A.7)

ONE manifest (`v2_quality/fasttrack/f2_results/run_manifest.json`) covering
all 3 cells in a single run, recording:

- exact source commit SHA (git HEAD at push time of Phase B code) — no
  invented SHAs; if the VM copy lacks `.git`, the SHA is taken from the local
  repo used to build the sync archive;
- model weight revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`;
- dataset file SHAs + 300-ID lock hash (Section 1–2);
- prompt+parser SHA (`svamp_adapter.py` sha256);
- cache identity (isolated `caches/f2_*` dirs);
- normalized phenotype hash per config;
- seed; per-item raw completions + scored values (full JSONL, V2-internal);
- per-cell error count and device GPU-second accounting.

The F1 manifest defect (coverage of only the last 4 cells, unknown git SHA)
is fixed by construction: single manifest, all 3 cells, SHA recorded from the
archiving step.

## 9. Budget and stop rules

- GPU cap: **1.0 aggregate GPU-hour** for all 3 cells (3 × 300 generations,
  1.5B model). Estimated need ≈ 0.2–0.4 GPU·h based on F1 timings.
- If at risk of exceeding the cap or any cell fails: STOP, flag INCOMPLETE,
  no selective partial averages described as complete.
- One shot only: no re-runs, no config changes after seeing results.

## 10. Phase-A checklist sign-off

| # | Check | Result |
|---|-------|--------|
| 1 | Dataset revision + file SHAs verified | PASS |
| 2 | 300-item lock created before inference, hash recorded | PASS |
| 3 | Configs = frozen REF/B2/B1, no re-selection | PASS |
| 4 | Adapter Body+Question only; scorer tested | PASS |
| 5 | GSM8K overlap 0/300; contamination caveat recorded | PASS |
| 6 | V1 artifacts untouched; F2 outputs isolated | PASS |
| 7 | CPU tests 5/5 | PASS |
| 8 | Manifest/traceability plan defined (fixes F1 defect) | PASS |

**Phase A verdict: PASS — proceeding to Phase B (GPU single shot) is authorized.**
