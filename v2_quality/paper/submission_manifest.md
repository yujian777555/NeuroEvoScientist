# V2 Submission Manifest — NeuroEvoScientist F3 (2026-10-09, Gate-3 final hotfix)

**Status: READY FOR OWNER UPLOAD DECISION — NOT SUBMITTED.**

## Deliverables (all under `v2_quality/paper/`)

| Item | Path | SHA-256 |
|---|---|---|
| Final review PDF (7 pp; 4 content + Ethics/Limitations + refs) | `main.pdf` | `4d20ab6ecf0cd53e37766f091d55fe81b93f81259923a6bd6ac49649cd8613ab` |
| LaTeX source | `main.tex` | `e1ea7810e4259d7687c3a8494da99aab949d42835c65ad9f5cbc7122a2bc4c21` |
| Editable manuscript | `manuscript.md` | `28c99a6d5ae1f56e87dadaec9f15ba8126b35a255041816c21ccb4194309f9ca` |
| Anonymous supplementary | `anonymous_supplementary.zip` (106 files) | `041a096da9befa93b929a45a1772f5c575583d173ae46749d35ce6cb30c1f900` |
| Bibliography | `references.bib` (22 entries, all cited) | — |
| Figures + script | `figures/`, `make_figures.py` | — |
| Audit report | `audit_report.md` (28/28 PASS, incl. Gate-3 textual guards) | — |
| Build scripts | `build_supplementary.py`, `audit_paper.py` | — |

Gate-3 final hotfix applied to BOTH `main.tex` and `manuscript.md`
(Planner verdict `v2_quality/fasttrack/gates/gate3_decision.md`):
(1) F1 baseline count corrected to six predefined baselines (four
CoT-matched B1–B4, two Direct controls B0/B5) plus the searched REF;
(2) CoT prompt-token spread stated as ~8.3× with observed accuracies
49–60% (no "10×" / "similar accuracy" claim); (3) equivalence-sounding
wording replaced by "no statistically detectable accuracy
difference/advantage" with effect sizes, CIs, p; (4) B4 effect downgraded
(exploratory, unadjusted, single contrast — no factor-importance ranking);
(5) "pre-registered" replaced by pre-specified / pre-locked wording
everywhere; (6) section order now Evidence → Reproducibility and Ethics →
Limitations → References (Limitations directly before refs, per ARR CFP);
(7) audit hardened: real content-page count (4 ≤ 8) from compiled PDF
section boundaries + deterministic regression guards
(`tests/test_v2_paper_text.py`); (8) Ethics misuse sentence replaced with
qualified risk wording.

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
- `v2_quality/paper/audit_paper.py`: 28/28 PASS — anonymity (text +
  metadata), 22/22 citations defined and cited, all printed statistics
  traced to locked sources, V1 holdout recomputed from frozen CSV, real
  main-content page count from compiled PDF (4 ≤ 8), section order
  (Ethics → Limitations → References), and all Gate-3 textual regression
  guards. Scope note: listed items only, not every scientific detail.
- PDF: 7 pages rendered and visually inspected page-by-page after the
  Gate-3 hotfix rebuild (title, figures, tables, section order,
  references).
- Full CPU test suite: 111/111 PASS (including `tests/test_v2_paper_text.py`
  deterministic hotfix guards and `tests/test_v2_f2_forensic.py`).
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
