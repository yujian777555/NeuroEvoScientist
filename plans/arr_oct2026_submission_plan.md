# Final Submission Plan — ARR October 2026 -> NAACL 2027

## Decision

Primary route:

**ACL Rolling Review, October 2026 cycle -> commit to NAACL 2027 if reviews are adequate.**

Fallback from the same ARR cycle:

**COLING 2027**, subject to venue-specific commitment rules and fit.

Rationale:
- the paper is fundamentally an NLP/LLM-agent empirical study;
- both NAACL and COLING are natural topical fits;
- the October 2026 ARR cycle is the next available review window;
- the project is experimentally frozen, so the remaining work is formatting, anonymity, citation integration, and submission compliance only.

Do not reopen experiments.

## Fixed dates

- ARR October 2026 submission deadline: **2026-10-12**
- ARR reviewer/service registration deadline: **2026-10-14**
- ARR author response: **2026-11-24 to 2026-11-30**
- ARR meta-review release: **2026-12-17**
- ARR cycle end: **2026-12-20**
- NAACL 2027 / COLING 2027 commitment deadline listed by ARR: **2026-12-23**

Re-check the official ARR dates page immediately before submission in case of an announced correction.

## Mandatory ARR account/service preparation

Before submission:
1. Every author must have a complete OpenReview profile.
2. Add ORCID, affiliation history, current email, conflicts, and DBLP/ACL Anthology links where applicable.
3. Identify the qualified service contributor required by ARR's October 2026 sustainable-reviewing policy.
4. Ensure reviewer/service registration is completed by the published deadline.
5. Do not assume a paper is guaranteed review without satisfying the current service-capacity policy.

This is an administrative desk-rejection risk and must be treated as seriously as formatting.

## Task 1 — Final manuscript consistency fixes

Use `paper/manuscript_v3.md` as the only prose source.

Locked corrections:
- GSM8K vs strongest fixed baseline = **+29.0pp at 1.5B / +16.7pp at 7B**.
- Values around +71pp refer to cross-task architecture comparisons, never the strongest fixed baseline.
- Multi-objective selection wording = **NSGA-II-style non-dominated sorting + crowding distance**.
- Do not state or imply canonical NSGA-III was used.
- ENSS > random remains closed.
- Mamba benefit remains closed.
- Universal own-task holdout superiority remains closed.
- QASPER 7B = backbone–prompt/extraction interaction, not capability collapse.

Run `src/scripts/compliance_scan.py` after all prose edits.

## Task 2 — Convert manuscript_v3 into ARR LaTeX

Create one authoritative venue version:
- `paper/arr2026/main.tex`
- `paper/arr2026/references.bib`
- `paper/arr2026/figures/`

Use the current official ARR/ACL long-paper template.

Requirements:
- double blind;
- no author names, affiliations, acknowledgments, GitHub username, personal URLs, or identifying commit URLs in the review PDF;
- insert actual citations with BibTeX keys, not author-name prose only;
- insert Tables A-C as real LaTeX tables;
- insert Figures 2-6 as real figures;
- include the required `Limitations` section before references;
- include any Responsible NLP / ethics material required by the current ARR form/template;
- do not exceed the current long-paper page limit.

Do not maintain a divergent scientific narrative between Markdown and LaTeX. LaTeX is formatting/translation of the locked manuscript only.

## Task 3 — Anonymous reproducibility package

The public repository currently identifies the owner. Do not link it directly from a double-blind submission unless current ARR anonymity rules explicitly allow it.

Prepare one of:
- anonymous supplementary archive uploaded with the submission; or
- an anonymized repository/archive with identifying metadata removed.

The review artifact may contain:
- code;
- configs;
- reproduction instructions;
- result-generation scripts;
- exact public model/dataset revisions.

It must not contain:
- user/owner identity;
- identifying Git history;
- personal paths;
- institution names if they reveal authorship;
- non-anonymous acknowledgments.

The final public GitHub repository can be released after anonymity constraints allow.

## Task 4 — Final figure audit

Regenerate all figures after the final script corrections.

Verify manually:
- Fig. 2 uses true final-generation distributions across seeds, not just locked representatives.
- Fig. 6 says it is the **Phase-18 compact-space exhaustive landscape**.
- Axis labels are readable at two-column print size.
- No figure claims a result stronger than the table/statistics.
- No color is the sole carrier of meaning.

## Task 5 — Citation audit

Every Related Work claim must map to a BibTeX entry.

Especially verify:
- ADAS;
- AgentSquare;
- EvoPrompt;
- ReAct;
- Toolformer;
- Reflexion;
- DSPy;
- RAG;
- Mamba/Mamba-2;
- NSGA-II;
- NAS / regularized evolution;
- AlphaEvolve.

Remove unused NSGA-III citation unless it is discussed only as background; do not cite it as the implemented selector.

## Task 6 — License decision

The repository owner must explicitly select a license before public code release.

Recommended choices to consider:
- Apache-2.0: permissive plus explicit patent grant;
- MIT: simpler permissive license.

Executor must **not** choose on the owner's behalf.

License is not a reason to alter or delay the anonymous review PDF if code is supplied as anonymous supplementary material, but it must be resolved before public release if the paper promises an open-source repository.

## Task 7 — Final PDF gate

Before submission:
- compile from a clean environment;
- inspect every page visually;
- check no text/figure clipping;
- verify all citations resolve;
- verify all references appear;
- verify no internal repo paths appear in prose;
- verify no author-identifying metadata is embedded in PDF properties;
- run compliance scan;
- run an anonymity grep over the LaTeX source and supplementary package;
- record final PDF SHA-256;
- record the exact source commit used to build the PDF.

Required output:
- `paper/arr2026/main.pdf`
- `paper/arr2026/submission_manifest.md`

## Final state

Only after the PDF gate passes change project status to:

**READY TO SUBMIT — ARR October 2026 / NAACL 2027 target**

No Phase-22 experiments.

Suggested final packaging commit:

`[Submission] prepare anonymous ARR 2026 paper package`
