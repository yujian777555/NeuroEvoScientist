# Submission Hardening — Final Non-Experimental Gate

## Status

Experiments are frozen and complete. This phase is **submission-only** and must not change any experimental result.

Planner review of commits `89adc7f` and `cd333ed` found that the repository has the required artifacts, but the paper package is **not yet ready to upload to a venue**. The remaining blockers are writing, consistency, reproducibility metadata, public-repository hygiene, and figure labeling.

No new experiments are allowed.

---

# Blocker 1 — Convert the manuscript from a research skeleton into a full English paper

`paper/manuscript_v2.md` is still a compact Chinese/English research skeleton with internal file pointers such as “see paper/method.md”. This is not a submission manuscript.

Create a complete paper:

`paper/manuscript_v3.md`

Required sections:
1. Abstract
2. Introduction
3. Related Work
4. Problem Formulation
5. Method
6. Experimental Setup
7. Main Results
8. Generalization Audit and Failure Analysis
9. Mechanism Analysis
10. Limitations
11. Conclusion
12. Reproducibility / Ethics statement as required by venue

Requirements:
- native-quality academic English;
- no internal repo directions such as “see paper/foo.md” in the prose;
- every numerical claim tied to an actual table/figure;
- clearly separate search/dev evidence from untouched holdout evidence;
- retain negative findings;
- no claim beyond `docs/phase21_final_audit.md`.

---

# Blocker 2 — Rewrite Related Work with real citations

`paper/related_work.md` is still an outline and contains an unsafe novelty sentence:

> “to our knowledge, this is the first ...”

while the same document says not to use an unverified “first” claim.

Remove all unsupported priority language.

Write actual citation-backed comparisons covering:
- LLM agent architecture / workflow optimization;
- automated prompt / reasoning strategy search;
- episodic and retrieval memory for agents;
- evolutionary computation / NAS;
- AlphaEvolve-style automated discovery;
- Mamba / state-space memory;
- multi-objective search.

Every named prior work must appear in `paper/references.bib`.

Do not fabricate references.

---

# Blocker 3 — Synchronize Method/Experiments with the final Phase-20/21 method

Current `paper/method.md` and `paper/experiments.md` still mainly describe the Phase-19 48-point flat space.

The final paper must distinguish two experimental layers:

### Compact audit layer
- Phase-18 48-point landscape;
- exhaustive Pareto/search-efficiency audit;
- source of the negative ENSS-vs-random result.

### Structured co-design layer
- Phase-20 hierarchical genome;
- conditional genes;
- task-aware phenotype canonicalization;
- task-specific input-context budget;
- local mutation / semantic-block crossover;
- Phase-20/21 holdout and sensitivity audit.

Do not present the 48-point space as the final structured search space.

Update both method and experiments accordingly.

---

# Blocker 4 — Fix final-figure semantics

## Figure 2
`render_figures.py::fig_gene_distributions()` currently uses the three locked representative architectures, not a 3-seed gene distribution, while its title says:

> “Converged genes per task (dev search, 3 seeds)”

This is misleading.

Choose one:
- render true seed-level gene frequencies from the dev-search results; or
- rename the figure to “Locked representative architecture per task”.

Preferred: true seed-level distributions, because C2a is a distribution/stability claim.

## Figure 6
The “48 configs” landscape comes from the Phase-18 compact space. Label it explicitly:

> “Phase-18 compact-space exhaustive landscape”

so readers do not confuse it with the later hierarchical Phase-20 space.

Regenerate figures after label/data correction.

---

# Blocker 5 — Reproducibility appendix must contain exact model revisions

Current appendix says model SHA is “in the VM HF cache”. That is insufficient for a public reproducibility package.

Record, if recoverable:
- exact Hugging Face revision / snapshot commit for Qwen2.5-1.5B-Instruct;
- exact revision / snapshot commit for Qwen2.5-7B-Instruct;
- exact dataset version/checksum or acquisition commit where possible;
- exact Python version;
- exact CUDA/runtime versions used in final runs.

If an exact revision cannot be recovered, say so explicitly rather than claiming it is recorded.

Also change “79+ tests” to the exact locked test count used at submission.

---

# Blocker 6 — README is scientifically stale

Current README still claims:
- “Evolutionary Neural Substrate Search” as the headline;
- tool-use and compression search;
- Mamba-enhanced memory as a contribution;
- self-evolving AI / scientific-agent scope not supported by final experiments.

Replace README with the locked paper positioning:

> Task-conditioned cognitive architecture co-design for LLM agents.

README must summarize:
- final genome and scope;
- GSM8K / PubMedQA / QASPER;
- supported and negative findings;
- reproduction commands;
- paper artifact paths;
- experiment-freeze commit.

Do not use legacy LoRA/QLoRA/tool-gene claims.

---

# Blocker 7 — Add a LICENSE or explicitly decide not to distribute code

The repository currently has no `LICENSE`.

Before making the repository public:
- choose an appropriate project license with the owner;
- add the license text;
- add third-party license/attribution notes if required.

Do not invent a license choice without owner approval.

---

# Blocker 8 — Submission compliance scan

Run a repository-wide paper/docs scan for forbidden wording:

- ENSS outperforms random search
- Mamba improves performance
- first / first-ever claims
- full neural architecture self-evolution
- LoRA/QLoRA as context compression
- universal task-specific superiority
- QASPER 7B capability collapse
- backbone-independent task preference

For every match, classify:
- historical/development-only and safe;
- paper-facing and must be corrected.

The final LaTeX/manuscript must have zero prohibited paper-facing matches.

---

# Blocker 9 — Venue-ready typesetting

Only after manuscript_v3 is complete:
- choose one venue;
- convert to that venue's current template;
- place figures/tables in the actual paper;
- verify page/word limits;
- anonymize repository URLs, author names, acknowledgments, and identifying commit links if double-blind rules require it;
- create a submission PDF and visually inspect every page.

Do not maintain two divergent manuscript versions.

---

# Final Gate

Submission package is READY only when all are true:

- [ ] manuscript_v3 is full English prose, not a skeleton;
- [ ] related work has verified citations and no unsupported “first” claim;
- [ ] method/experiments describe both compact and structured phases correctly;
- [ ] Figure 2 accurately represents seed evidence;
- [ ] Figure 6 explicitly labels the Phase-18 compact landscape;
- [ ] exact model/data revisions are recorded or limitations disclosed;
- [ ] README matches final scientific positioning;
- [ ] LICENSE decision completed by repository owner;
- [ ] paper-facing prohibited wording scan is clean;
- [ ] one venue template is selected and a final PDF passes visual inspection;
- [ ] experiments remain frozen.

Suggested commit message:

`[Submission] harden final manuscript and public reproducibility package`
