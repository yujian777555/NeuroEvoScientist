# Gate 3 Planner Verdict — CONDITIONAL GO / PAPER-ONLY FINAL HOTFIX
Date: 2026-10-09
Executor F3 evidence: `7a0980d6a99352e3f1b75ffd953ec6d560c8299d`
Status commit: `4d73c623ba3eff31664bf008a99af6e570837254`

## Decision

**SCIENTIFIC DATA ACCEPTED, CURRENT PDF NOT YET CLEARED FOR OWNER UPLOAD.** One small NO-GPU editorial correction round is mandatory; then regenerate and re-audit V2 PDF/supplementary and hand back for the owner's upload decision. No experiments, model inference, new benchmark reading, selection or optimization runs.

### Independently verified
- F2 3x300 aligned rows and binary exact McNemar counts were independently verified earlier at Gate2: REF=211/300, B2=215/300, B1=211/300; REF-B2 wins23/loss27 p=0.671811; REF-B1 wins34/loss34 p=1.0.
- Forensic `f2_provenance_forensic.md` documents full bytes of committed dataset and predictions consistent with lock, with narrower runtime guard and on-VM model revision still PARTIAL. No new data discrepancy identified in Gate3 paper sources.
- New LaTeX presents observed F2 accuracy/token totals and V1 Direct-only confounding. Evolution≈random and Mamba null retained.
- Executor reports 105 tests, 18 checks and rendered PDF visually inspected; Planner independently reviewed source, audit code and manifest, but **could not independently download or render PDF binary** from GitHub in this environment. Therefore visual checks remain Executor-attested, not Planner-verified. Do not falsely state otherwise.

### Mandatory precise paper edits (apply in BOTH main.tex and manuscript.md)

1. **Miscounted presets and CoT variants (FACTUAL ERROR).**
   Actual F1 contains seven total distinct configs: SIX fixed/predefined B0–B5 (FOUR CoT B1–B4 + TWO Direct B0/B5) PLUS ONE searched REF. Replace every instance of 'seven presets plus REF', 'seven CoT-matched presets', 'six CoT presets plus two direct controls' or similar false count. Correct standard wording:
   `six predefined baselines (four CoT-matched and two Direct controls) plus the searched REF`.
   The run matrix has 15 cells across datasets/models, not seven baselines plus a reference.

2. **Unsupported 10x cost among similar-accuracy CoT presets.**
   GSM8K 1.5B CoT prompts: B1 8,091; B4 14,491; B3 27,683; B2 67,391; REF 24,391. All CoT configurations span 67,391/8,091=**8.33x**, with accuracies 49–60%, which are not all statistically established as 'similar'. Replace '10x across presets with similar accuracy' and '10x among CoT presets' by factually bounded:
   `CoT variants span ~8.3x in prompt tokens on GSM8K dev, with observed accuracies 49%-60%; the cost–accuracy tradeoff is configuration-dependent.`
   SVAMP total-token ratios: REF/B1 = 118,066/67,381 = 1.75x; B2/REF = 241,154/118,066 = 2.04x; preserve.

3. **Avoid statistical equivalence language.**
   'statistically indistinguishable'/'ties' can be read as formal equivalence. Explicitly say `no statistically detectable accuracy difference` with actual effect/CI; never conclude equivalence from p>0.05. Dev REF 60.0 vs B2 59.0 p=1, F2 REF vs B2 −1.33pp CI[−6,+3.33] p=.67; REF vs B1 0pp CI[−5.33,+5.33] p=1.

4. **F1 B4 effect interpretation too strong.**
   Original paper says B4 secondary p=.043 'context budget matters more than which strong preset'. This is exploratory, unadjusted, on reused n=100 dev; a single contrast does NOT rank feature importance. Replace with `the reduced-exemplar-verbosity B4 preset was lower on this exploratory dev slice (+11pp REF-B4, unadjusted p=.043); causal prioritization requires further controls.`
   Cite total-token costs descriptively; no search advantage.

5. **Replace external preregistration language in Markdown.**
   `manuscript.md` still contains 'pre-registered' for F1/F2. Replace with `pre-specified, committed before evaluation` or `pre-locked before F2 inference`. This project has an internal Git commit lock, not public external preregistration. Make LaTeX and Markdown fully consistent.

6. **ARR Limitations placement and checks.**
   Official ARR CFP says standalone **Limitations** section at the end of the paper before references and outside page limit. Source currently has `Limitations` then `Reproducibility and Ethics` then references. Prefer `Conclusion/Evidence Boundaries -> Reproducibility and Ethics -> Limitations -> References`, with Limitations directly before bibliography. An Ethics statement is optional; don't delete it. Make no new result claims in Limitations.
   URL: https://aclrollingreview.org/cfp#limitations

7. **Audit quality, exactness and limitations.**
   Existing `audit_paper.py` declares D.pages PASS under `len(doc)<=11`, which does NOT check main text ≤8 pages or isolate non-counted limitations/ethics/reference pages. Replace/augment with an actual page-boundary analysis from the compiled PDF or robust manual recorded content-end check; verify 8-page MAIN CONTENT maximum (the existing PDF has 7 total). Add regression tests that verify all baseline count claims and 'pre-registered' absence in both main.tex and manuscript.md; check new PDF SHA and anonymized supplementary. Avoid asserting that 18/18 checks prove all scientific details have been independently checked.

8. **Ethics tone (recommended).**
   Replace ungrounded absolute `we see no foreseeable misuse beyond ...` with a modest, concrete discussion of public model/benchmark limitations and possible misuse without a categorical exclusion.

## Scope and acceptance
- No modification of any V1/F1/F2 locked experiment outputs, model setup, existing predictions, `results/`, `experiments/`, `configs/`, old V1 review package `paper/arr2026/`, `deliverables/final_submission/`.
- Rebuild `v2_quality/paper/main.pdf`; sync final source, manuscript, bibliography, anonymized supplementary, `submission_manifest.md`, audit report, exact SHA and page count; visually render/inspect every PDF page and anonymous supplement, including build paths and embedded metadata.
- Run full test suite, citation/anonymity checks, source-to-claim audit and new guard assertions; record exact PASS/FAIL counts. If any integrity check fails, STOP and report BLOCKED. No paper upload by Executor.
- Deadline: Official ARR lists **Oct 12 2026** as final NAACL 2027 / COLING 2027 eligible ARR cycle. Submission is possible only if final PDF and author/service registration are ready in time; do NOT claim registration complete. For ACL 2027, official CFP latest ARR is Jan 4 2027. https://aclrollingreview.org/dates , https://2027.aclweb.org/calls/main/ .
- ARR October sustainable-reviewing requirements require *all authors' complete OpenReview profiles* and qualified service contributor for guaranteed review, subject to capacity. Human must verify. https://aclrollingreview.org/cfp .
- This paper has NLP/QA content but ARR checklist warns generic LLM-agent work does not automatically fall in scope: explicitly position contribution as QA/scaffold evaluation and generalization, not pure search engineering.
- STOP at FINAL-GATE3 after this short editorial fix, push outputs and report. The owner decides to upload the exact rebuilt PDF.

## Outcome
**Conditional GO for publication-ready textual hotfix and rebuild only**; NO-GO for submitting the currently reviewed 7-page `8b12eb2...` PDF without these corrections. No more GPU needed.