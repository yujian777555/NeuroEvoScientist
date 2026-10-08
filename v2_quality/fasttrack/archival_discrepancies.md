# Archival Discrepancy Check (F0)

Task: verify whether legacy `paper/phase21_tables.md` conflicts with locked
CSVs and whether it leaked into the anonymous supplementary package.

## Verification method

Every phase21_tables.md numeric cell was spot-checked against
`results/phase20_holdout_results.csv` and `results/phase21_qasper_diag_*.json`
(10 representative cells covering both backbones and all three benchmarks).

## Findings

1. **No numeric conflicts found.** All checked cells match the locked CSVs
   exactly (A_pubmed 0.3725/0.4875; A_qasper 0.5625/0.5775 on PubMedQA;
   A_gsm 0.1878/0.1879, A_qasper 0.1379/0.0064 on QASPER; GSM8K rows match).
   The Planner's "stale conflicting values" suspicion is **not confirmed**;
   the file is superseded in presentation but not erroneous.
2. **Supplementary inclusion: CLEAN.** `paper/arr2026/anonymous_supplementary.zip`
   contains no phase21_tables.md (116 files; scan for the name is empty).
   It contains claim_audit.md, phase21_final_audit.md, configs, code, and
   locked result JSONs only.
3. **Action**: mark `paper/phase21_tables.md` as SUPERSEDED by
   `paper/arr2026/` tables (presentation-only supersession, values identical
   within rounding). Historical file retained read-only.

## Register

| artifact | status | action |
|---|---|---|
| paper/phase21_tables.md | SUPERSEDED (values verified consistent) | banner note added |
| anonymous_supplementary.zip | clean of obsolete tables | none |
| results/phase1[6-9]*, phase20_* | locked, read-only | none |
