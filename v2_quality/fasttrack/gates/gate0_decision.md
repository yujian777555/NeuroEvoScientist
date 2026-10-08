# Gate 0 Planner Verdict — CONDITIONAL GO → F1 PRE-FLIGHT → GPU RUN

Date: 2026-10-08
Reviewer: GPT Planner
Source Executor F0: `e32fb95`
Verdict: **CONDITIONAL GO, PRE-FLIGHT MANDATORY**. Executor is authorized to begin F1 **after** passing the checks below; no need for an additional human approval if all checks pass. Any failed check = STOP / NO-GO and report.

## Independent review corrections

The Executor's F0 statement that old `paper/phase21_tables.md` "matches locked CSVs" was wrong. Material differences were independently verified (e.g., GSM8K 7B A_qasper old 0.693 vs CSV 0.1961, strongest fixed old 0.549 vs CSV 0.6932, memory-off old 0.585 vs CSV 0.7342). See `archival_discrepancies.md` and corrected warning in old table.
The 15 F1 cells originally contained TWO duplicate comparisons:
- B0 and B5 were both Direct + no memory.
- B1 and B4 were both CoT + no exemplar; changing exemplar-only context cannot affect their rendered prompt.
Planner corrected all seven machine-readable baseline definitions in `baselines_f1.json`; `run_matrix.csv` now refers to these identities.
Protocol's original 12 GPU-hour F1 cap conflicted with compute budget; corrected to **F1 ≤1.5 aggregate GPU-hours**.
The 100-item DEV slice cannot support an equivalence claim from ±2pp/nonsignificance. All F1 claims are exploratory until independent confirmation.

## Required F1 PRE-FLIGHT (NO GPU; hard checks)

1. `git fetch`, clean and reset work against current origin/main; read `protocol_f0.md` (now Planner corrected), `baselines_f1.json`, `run_matrix.csv`, `compute_budget.md`.
2. Run `python -m pytest tests/test_v2_f0.py -q` plus existing targeted evaluator/genome tests. Record PASS counts. Planner wrote new regression checks but has not executed them in Executor environment.
3. Test constructor validity and task-aware `StructuredGenome` normalized phenotype uniqueness for every B0..B5, REF on BOTH GSM8K/QASPER.
4. For at least one fixed representative DEV item from each task, invoke actual production prompt builder **without model inference** and compare identical-model prompt hashes:
   - B0 != B5, B1 != B4
   - B1 != REF (memory injected into REF)
   - B5 vs REF differs by reasoning template while identical exemplars/context
   - B3 uses term-frequency cosine implementation despite legacy enum `tfidf`.
   - If hashes are unexpectedly identical, STOP; do not waste GPU.
5. Compare `REF` canonical effective genome against `results/phase20_selection_lock.json` A_gsm, and enforce same backend, model revision, tokenizer, decoding, parser and QASPER doc budget across cells. Ensure configs are not reselected after the fact.
6. Ensure fresh V2 cache/result output paths, no read/write to Phase-20 holdout during F1. If historical cache is reused, it must be marked and matched by full cache identity; safer new isolated cache.
7. Gate F1 device-time ≤ 1.5 aggregate GPU-hours. The run estimate (~43.2 device minutes base) is not a wall-clock promise.
8. Commit any necessary runner changes, document baseline hash manifest and preflight PASS evidence in `v2_quality/fasttrack/f1_preflight.md`. A test failure = NO-GO; deliver logs and stop.

## F1 execution authorization

After all preflight checks pass, **execute only the 15 DEV-only cells** from `run_matrix.csv`. 1.5B GSM8K/QASPER discovery and pre-selected B1/REF 7B dev transfer. Run one predefined seed per cell, capture per-item outputs, accuracy/F1, prompt AND completion tokens, latency and aggregate GPU-hours. Compare aligned items, bootstrap paired 95% CIs and correct binary/F1 sign tests, show Pareto capability-vs-tokens. Report exact source/model/dataset SHA, seed, failures and caching.

**DO NOT** run independent SVAMP/MATH confirmation now. Reserve confirmation data untouched for Planner Gate F2, and do not infer clean external validation from mere HF mirror reachability. Avoid saying no pretraining contamination is guaranteed.

## Gate F1 finish conditions

Produce and commit `v2_quality/fasttrack/gates/gate1_decision.md`, a concrete F1 results/evidence report and an immutable proposed F2 ≤3-configuration shortlist + confirmation dataset integrity checks. Do not declare statistically equivalent on n=100 because confidence intervals overlap, and do not make unqualified optimizer superiority claims. If fixed CoT baseline performs as well or better, take honest negative-result route without rescue experiments.

Stop after F1 and request Planner Gate 1; F2 GPU NOT AUTHORIZED yet.

## Protected assets

The V1 review PDF and hash e42191b0502f4b1ca7f7ed2bdd6b8b735ab0755294e185d2cd83156d22ae931d, `paper/arr2026/`, `deliverables/final_submission/`, Phase17–21 `results/`/`experiments/`/`configs/` and locked selection remain immutable. The legacy Markdown table warning text is corrected but original erroneous numbers intentionally preserved with explicit disclaimer.

