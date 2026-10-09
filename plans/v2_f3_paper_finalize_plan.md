# F3 — Fast-Track V2 Manuscript and Submission-Readiness Plan
Date: 2026-10-09
Status: APPROVED BY PLANNER, PAPER-ONLY, NO GPU
Authority: `v2_quality/fasttrack/gates/gate2_decision.md`

## Objective
Produce an honest, anonymous, independently auditable V2 submission pack promptly after successful F1 fair-CoT comparison and single-shot F2 cross-benchmark SVAMP. **Do not redo V1 or run new experimental GPUs.** F3 finishes at Gate3 review, not automatic upload. Preferred turnaround: 3–5 workdays if tests/build and provenance checks pass; schedule estimate, not guarantee.

## F3-A — forensic data lock and result-to-source trace (first, blocking)
1. Add a READ-ONLY verifier (new source; don't modify the frozen F2 runner/adapter), e.g. `v2_quality/fasttrack/verify_f2_integrity.py`.
2. Hash complete bytes of committed SVAMP test/train JSON and compare to the exact pre-inference `confirmation_lock.json` and results manifest. Recompute full 300 ordered IDs, detect duplicates, verify model/runner/adapter SHA is consistent with evidence; regenerate exact paired counts directly from predictions with no output mutations.
3. Validate every 300-row prediction file has precisely same 300 IDs, no duplicate, full completion output, valid binary correct, adapter_score alignment and baseline genome hashes. Verify source model/dataset revision evidence separately from manifest-provided values; annotate unsupported provenance claims explicitly.
4. Record that old `load_locked_test_rows` only checks ordered ID hash and count, not source file bytes. This was a narrower guard than the Executor described. Write `v2_quality/fasttrack/f2_provenance_forensic.md` with PASS/PARTIAL/FAIL and actual outputs/tests. If raw-file SHA mismatches, stop manuscript claims; report BLOCKED. No selective reruns after reading confirmation outputs.

## F3-B — strongest evidence framing
Use three tiers in separate table panels and paragraphs:
1. V1 previous locked *descriptive* holdout: searched CoT vs four fixed Direct baselines; do not attribute +29.0/+16.7pp to search alone or memory. Phase18 equal-budget evolution vs random = no advantage, Mamba2 benefit unsupported.
2. F1 existing GSM8K/QASPER DEV re-use: 15 cells, 1.5B/7B; previously exposed to architecture selection, hence exploratory (n=100 GSM8K, n=50 QASPER). REF-B2 +1pp, p=1; REF-B1 +10pp at 1.5B p=0.087, +10pp at 7B p=0.041 (secondary unadjusted). No equivalence / robust interaction claim.
3. F2 prelocked original SVAMP test n=300, single 1.5B family, no tuning: REF=211/300, B2=215/300, B1=211/300; PRIMARY REF-B2 −1.33pp CI[−6,+3.33] p=0.6718; SECONDARY REF-B1 0pp CI[−5.33,+5.33] p=1.0. Distinguish independent from project selection (yes) from public-pretraining contamination (unknown) and GSM8K distribution identity (no).

**Crucial Pareto/cost truth:**
| cfg | accuracy | prompt tokens | output tokens | sum |
| REF | 70.33% | 68,017 | 50,049 | 118,066 |
| B2 | 71.67% | 197,017 | 44,137 | 241,154 |
| B1 | 70.33% | 19,117 | 48,264 | 67,381 |
B2 nominally slightly more accurate with 2.04× total tokens vs REF. B1 equals REF observed accuracy with ~1.75× fewer total tokens (REF dominated in the observed 2D accuracy/token plane by B1; avoid implying statistically demonstrated dominance). Do NOT suppress B1.

**Non-transfer wording guard:** F1 REF-B1 exploratory +10pp on GSM8K dev, F2 REF-B1 0pp on SVAMP; the F1 point estimate did not replicate. Not proof of a significant task-by-memory interaction; comparing p values is invalid evidence of heterogeneity. Need a formal interaction test for 'significant different effect across datasets', which is not authorized in F3; avoid such a claim.

## F3-C — manuscripts, figures and appendix
1. Create `v2_quality/paper/` as a separate deliverable. NEVER replace `paper/arr2026/` or `deliverables/final_submission/`; preserve prior SHA e42191b0502f4b1ca7f7ed2bdd6b8b735ab0755294e185d2cd83156d22ae931d.
2. Draft an 8-page-limit compliant ARR/ACL review-style main paper using a narrower contribution: task-conditioned cognitive configuration selection + fair-baseline/cost/generalization audit + negative findings. Suitable title option: 'When Does Task-Conditioned Cognitive Configuration Search Generalize? A Controlled Audit of LLM Agent Scaffolds'. Research contributions should be verifiable rather than marketed.
3. Main text must contain fair baseline definitions, search method distinction, principal F2 table with accuracy+tokens, paired 95% CIs and p, cross-benchmark differences with sampling limitations, strong appropriate related work (including MaAS/AgentSquare), limitations and ethics.
4. New figures must be reproducible using already immutable F1/F2 CSV/JSON or results. Suggested: (a) DEV and SVAMP capability-vs-prompt+completion token scatter **separate datasets/panels**; (b) REF-vs-B2 and REF-vs-B1 paired differences with CIs, explicitly not equivalence. Do NOT reuse V1 48-point landscape as a direct ENSS vs Random curve. Do NOT cite or scrape `paper/phase21_tables.md` (known numerical errors).
5. Exact test labels: binary = exact McNemar; QASPER continuous normalized F1 = paired exact sign test; paired bootstrap CI. QASPER extraction limitations discussed, not claimed fixed.
6. Mark F1 incomplete provenance (manifest only last 4 cells; unknown git sha) and F2 post-hoc byte-hash verification gap transparently. Include comparison scope, limited 1.5B external transfer, no statistical equivalence, no independent non-Qwen confirmation.
7. Exact data/citations/claims audit: every printed statistic back to frozen source, all references resolve, no phantom code/results.
8. Anonymous supplementary: src, F1/F2 protocols, configs, results, locked list, tests; scrub personal paths / raw GitHub usernames / Git history / author names. Never include dataset copies unless license review allows and they're necessary. Local absolute path `/202532803004/` must be scrubbed from review artifact. Do not share non-anonymized public repository URL in blinded PDF.
9. Compile with review template, check pages/images/clipping visually, bibliography, anonymity including PDF metadata, full test suite, reproducibility manifest, built PDF SHA256, actual source commit. Never claim visuals PASS without examining all rendered pages.
10. Candidate target venue and next official dates must be checked on publisher/ARR official website at delivery time. If later than 2026-10-12 ARR, do not claim eligibility for that NAACL 2027/COLING 2027 cycle. User decides target / upload.

## Gate3 deliverable and stop
- `v2_quality/paper/main.tex`, `main.pdf`, `references.bib`, figures, `manuscript.md`, anonymous supplementary, submission manifest.
- `v2_quality/fasttrack/f2_provenance_forensic.md`, new CPU verifier/tests, comprehensive `v2_quality/fasttrack/gates/gate3_decision.md`.
- `status.json` with exact HEAD, source-to-PDF hash, tests, page count, source data, limitations and 'READY FOR PLANNER GATE3 REVIEW', NOT `SUBMITTED`.
- Commit/push to origin/main, STOP. No further GPU, no silent experiment alteration or deadline promise.

## Official timing note, verified 2026-10-09
As of the official ARR dates/venue table and ACL 2027 main-conference CFP, 2026-10-12 is the final ARR deadline for NAACL 2027/COLING 2027; ACL 2027 names **2027-01-04** as the latest eligible ARR submission deadline. Links: https://aclrollingreview.org/dates and https://2027.aclweb.org/calls/main/ . This is a venue-specific latest date, not an instruction to wait until January: check newly announced ARR cycles and venue policy before choosing the earliest viable submission. ARR sustainable reviewing and service-contributor requirements also apply: https://aclrollingreview.org/cfp . Do not submit without the owner's action.
