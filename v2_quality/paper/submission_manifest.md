# V2 Submission Manifest — NeuroEvoScientist F3 (2026-10-09)

**Status: READY FOR PLANNER GATE-3 REVIEW — NOT SUBMITTED.**

## Deliverables (all under `v2_quality/paper/`)

| Item | Path | SHA-256 |
|---|---|---|
| Final review PDF (7 pp) | `main.pdf` | `8b12eb2b0855bcfceceebe0bfc2a4661ea31d0c37772b1e3280ceab79813018a` |
| LaTeX source | `main.tex` | `bb506d42fc0d3c41a28c1cb9643733cdf78b9a25b5f9953bb4b91f37af341061` |
| Editable manuscript | `manuscript.md` | `df6920a25310413ed864ac59d69e876a480a937102d30f5a8d994087f2174830` |
| Anonymous supplementary | `anonymous_supplementary.zip` (106 files) | `3ac968f0d0e89e0357c0296bcfbc9173db235354d1668dc10a404f557510a839` |
| Bibliography | `references.bib` (22 entries, all cited) | — |
| Figures + script | `figures/`, `make_figures.py` | — |
| Audit report | `audit_report.md` (18/18 PASS) | — |
| Build scripts | `build_supplementary.py`, `audit_paper.py` | — |

Style: `acl.sty` review mode (line numbers), compiled with pdfTeX on a clean
VM checkout; PDF metadata author/title empty.

## Source-to-claim map (every headline number → immutable source)

| Claim in paper | Value | Source |
|---|---|---|
| Tier-1 GSM8K holdout A_gsm 1.5B / 7B | 0.518 / 0.859 | `results/phase20_holdout_results.csv` (frozen; recomputed 0.5185/0.8597) |
| Tier-1 vs strongest fixed baseline | +29.0 / +16.7 pp | same CSV (best fixed 0.2289 / 0.6932; McNemar p<0.001 in `results/phase20_statistics.json`) |
| Tier-1 evolution ≈ random | diffs <0.01 AUC/HV | `results/phase18_search_efficiency.csv` (320 rows, 20 seeds) |
| Tier-1 Mamba-2 negative | not selected beneficial | Phase-18/20 frozen results + V1 locked manuscript |
| Tier-1 memory ablation | 0pp@1.5B / +12.6pp@7B GSM8K; +18.0 PubMedQA; +1.5 QASPER | V1 frozen controlled-ablation results (same-genome) |
| F1 GSM8K dev cells (7 configs) | 11.0–60.0%, tokens | `v2_quality/fasttrack/f1_results/f1_summary.csv` + 15 prediction files |
| F1 REF−B2 / REF−B1 | +1.0pp p=1.0 / +10.0pp p=0.087 | `v2_quality/fasttrack/f1_results.md` (independently re-scored by Planner, gate1) |
| F1 7B REF−B1 (secondary) | +10.0pp p=0.041 | same |
| F2 SVAMP accuracies | REF 211/300, B2 215/300, B1 211/300 | `f2_results/run_manifest.json` + `predictions_f2_*.jsonl` (900 rows, re-verified byte-for-byte by `verify_f2_integrity.py`) |
| F2 token totals | 118,066 / 241,154 / 67,381 | `run_manifest.json` (prompt+completion) |
| F2 primary / secondary stats | −1.33pp CI[−6.00,+3.33] p=0.6718 / 0.00pp CI[−5.33,+5.33] p=1.0 | `f2_results/f2_statistics.json` (recomputed independently in forensic audit) |
| F2 cost ratios | 1.75× / 3.56× / 2.04× | recomputed from manifest token totals |
| SVAMP lock | 300 IDs, file SHAs, revision | `v2_quality/fasttrack/confirmation_lock.json` |
| Model / adapter revisions | Qwen2.5-1.5B `989aa798…`; adapter `0869a9e1…` | manifest + lock |

Nothing was taken from `paper/phase21_tables.md` (known numerical errors).

## Verification performed (all 2026-10-09)

- `v2_quality/fasttrack/verify_f2_integrity.py`: full-byte dataset hashes,
  300 ordered IDs, 3×300 prediction rows (IDs/order/uniqueness/full
  completions/binary scores/adapter alignment/genome+phenotype hashes),
  paired stats recomputation (McNemar + bootstrap), V1 PDF frozen hash —
  PASS with 2 documented PARTIAL provenance annotations
  (`f2_provenance_forensic.md`).
- `v2_quality/paper/audit_paper.py`: 18/18 PASS — anonymity (text +
  metadata), 22/22 citations defined and cited, all printed statistics
  traced to locked sources, V1 holdout recomputed from frozen CSV, review
  format.
- PDF: 7 pages rendered and visually inspected page-by-page (title break,
  figure label overlap, and a reference URL overflow were found and fixed;
  re-verified).
- Full CPU test suite: see commit message / status.json (103+2 tests).
- V1 frozen artifacts untouched: `paper/arr2026/main.pdf` SHA-256
  `e42191b0…931d` verified unchanged by the forensic verifier (check F).

## Candidate venue timing (verified live 2026-10-09)

From https://aclrollingreview.org/dates: **October 2026 ARR cycle —
submission deadline 2026-10-12**; venue table lists NAACL 2027 and COLING
2027 with "Final ARR Submission Date: October 12, 2026" (commitment
2026-12-23). ACL 2027 lists a January 2027 final ARR date (CFP:
2027-01-04). ARR reviewer-registration-by-all-authors is mandatory at
submission. Submitting to the 2026-10-12 cycle preserves NAACL 2027 /
COLING 2027 eligibility; the owner decides target and performs any upload.

## Known limitations carried into the paper

Single model family (Qwen2.5); SVAMP public-benchmark contamination
unknowable; Tier-3 is cross-benchmark, not i.i.d.; Tier-2 dev slices
exploratory with partial provenance; QASPER extraction sensitivity;
n=100/300 power; no equivalence claims anywhere; no optimizer-superiority
claims anywhere.
