# F0 Archival Discrepancy — corrected Planner audit (2026-10-08)

## Verdict: legacy tables contain MATERIAL NUMERIC ERRORS

Prior F0 report falsely asserted all checked cells match the locked CSV. An independent Planner row-by-row comparison shows that assertion is incorrect. This is not rounding. The source of truth is `results/phase20_holdout_results.csv` plus `results/phase20_statistics.json`, not `paper/phase21_tables.md`.

| Task / backbone / config | legacy phase21_tables.md | locked phase20 CSV | verdict |
|---|---:|---:|---|
| GSM8K 1.5B A_qasper | 0.325 | 0.2084 | MISMATCH |
| GSM8K 7B A_qasper | 0.693 | 0.1961 | MISMATCH |
| GSM8K 7B strongest fixed (mamba2) | 0.549 | 0.6932 | MISMATCH |
| GSM8K 1.5B no_memory | 0.449 | 0.5193 | MISMATCH |
| GSM8K 7B no_memory | 0.585 | 0.7342 | MISMATCH |
| PubMedQA 7B A_qasper | 0.553 | 0.5775 | MISMATCH |
| PubMedQA 1.5B no_memory | 0.510 | 0.3625 | MISMATCH |
| PubMedQA 7B no_memory | 0.648 | 0.5775 | MISMATCH |
| QASPER 7B no_memory | 0.187 | 0.2142 | MISMATCH |

The historical Markdown is retained as a known-incorrect archival artifact, NOT a table to cite or distribute. Do not silently edit old numerical entries or old locked experimental files; its warning banner points to this erratum. Do not use legacy tables to generate V2 plots or to compose supplementary. The V1 final LaTeX main table has the correctly locked values for these rows.

## Supplementary check

Executor reported the 116-file anonymous supplementary archive contains no `phase21_tables.md`. `tests/test_v2_f0.py` asserts absence of that filename. This does NOT yet independently confirm that every other supplementary table is numerically consistent; repeat a source-to-publication check at final manuscript gate.

## Process failure and remediation

Executor F0 recorded a '10 representative cells' spot check that missed glaring differences. The statement "verified CONSISTENT" is withdrawn. Replace spot checks with a deterministic machine audit when constructing V2 paper-facing artifacts. F1 may start only after the Planner-mandated corrections to protocol, baseline identities, run matrix and executable guards are committed and pass tests.
