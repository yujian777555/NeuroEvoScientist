# HOTFIX HANDOFF (paper-only, submission mode)

## Locked rules
- No experiments, no re-search, no result-file changes (results/, experiments/, configs/ read-only).
- Don't rescue negative results. Don't strengthen claims.
- Target: ARR Oct 2026 -> NAACL 2027.

## Verified facts so far
- Repo synced at dbc08e6; HEAD after my commits: 6aff2b5 → then Planner dbc08e6 (status ready).
- deliverables/final_submission/ exists with final PDF copy (SHA 3fb5fe1c... matches manifest).
- Fix3 premise VERIFIED: src/evaluator/memory.py tfidf_scores = pure TF cosine, NO IDF.
- MaAS VERIFIED: "Multi-agent Architecture Search via Agentic Supernet", Guibin Zhang, Luyang Niu, Junfeng Fang, Kun Wang, Lei Bai, Xiang Wang, ICML 2025 (oral), arXiv:2502.04180, OpenReview id imcyVlzpXh.
- Evo-Memory VERIFIED: "Evo-Memory: Benchmarking LLM Agent Test-time Learning with Self-Evolving Memory", Tianxin Wei et al., arXiv:2511.20857 (2025).
- Tectonic installed at .tectonic/Library/bin/tectonic.exe (isolated; .tectonic in .gitignore).
- PDF compile pipeline works: cd paper/arr2026 && ../../.tectonic/Library/bin/tectonic.exe main.tex
- Compliance scanner: src/scripts/compliance_scan.py (exit 0 = clean paper-facing).
- Citation audit: src/scripts/citation_audit.py (main.tex vs arr2026/references.bib).
- Page inspection: pymupdf render to .tmp_pages/ (gitignored), ReadMediaFile to view.
- GSM8K seeds sensitivity (for Fix 5): s0 none+CoT(d2), s1 recency+CoT(d2), s2 retrieval+CoT(d3).

## Fix checklist (16 fixes from user)
- [ ] Fix1 McNemar->paired exact sign test for QASPER (binary tasks keep McNemar): main.tex, manuscript_v3.md, experiments.md, method.md, phase21_tables.md (captions)
- [ ] Fix2 QASPER-7B wording downgrade: remove "not a capability failure"/absolute; use "substantial answer-format/extraction component ... does not establish that underlying answer quality is unaffected". Files: main.tex (abstract, results, Fig4 caption, limitations, conclusion), manuscript_v3.md, abstract_v2.md? (paper-facing), docs/* (keep as-is historical), README.md
- [ ] Fix3 TF-IDF-> term-frequency cosine retrieval / sparse lexical cosine retrieval (implementation lacks IDF): main.tex, manuscript_v3.md, method.md, experiments.md, related_work.md, README.md
- [ ] Fix4 "pre-registered" -> "pre-specified and commit-locked (before holdout inference)": all paper/ files
- [ ] Fix5 GSM8K seed stability: "CoT-dominant light-memory family; memory subtype varies (none/recency/retrieval)": main.tex + manuscript_v3.md
- [ ] Fix6 Fig2 caption: "Gene modes and shares over pooled final-generation populations from three independent dev-search seeds": main.tex + manuscript_v3.md
- [ ] Fix7 MaAS add to references.bib + arr2026/references.bib + related_work.md + main.tex paragraph (agentic supernet, inference resources; our difference: single frozen-backbone internal cognitive config + search-vs-holdout gap emphasis)
- [ ] Fix8 Evo-Memory add to references.bib (both) + short related-work paragraph (online/self-evolving memory vs our calibration-only fixed bank)
- [ ] Fix9 memory-scaling wording: "On GSM8K, controlled memory effect increases from ~0pp (1.5B) to +12.6pp (7B)"; section title "Memory effects are task- and scale-dependent"; report GSM8K/PubMedQA/QASPER separately: main.tex + manuscript_v3.md + abstract (abstract_v2.md is planner-locked; keep abstract consistent but minimal edit)
- [ ] Fix10 Limitations add QA-style single-agent scope sentence
- [ ] Fix11 main.tex section order: Conclusion -> Limitations -> Reproducibility/Ethics -> References (Limitations right before refs; keep content)
- [ ] Fix12 objective definitions: efficiency = 0.5*(1/(1+n_params/4e6)) + 0.5*(1/(1+avg_prompt_tokens/1024)) when tokens measured; adaptability = benchmark-specific proxy (GSM8K long-solution accuracy; PubMedQA "maybe" accuracy; QASPER falls back to capability) — main.tex method + manuscript_v3.md + metrics.md
- [ ] Fix13 multi-objective scope note: adaptability proxy not independent of capability for QASPER (limitations/method note)
- [ ] Fix14 stats caption: "Paired bootstrap 95% CIs for all tasks; exact McNemar for binary GSM8K/PubMedQA; two-sided exact paired sign test for continuous QASPER F1." (phase21_tables.md captions + main.tex)
- [ ] Fix15: do NOT touch results/experiments/configs (verified read-only discipline)
- [ ] Fix16: compliance scan, citation audit, anonymity grep, recompile PDF, inspect 7 pages, new SHA-256, update manifest, sync deliverables/final_submission/, commit+push

## Final report format (user-required)
Paper-only hotfix complete. / Experiments rerun: NO / Scientific results changed: NO / Main claim changed: NO / QASPER statistics: McNemar removed... / etc (see user message) / PDF pages / New PDF SHA-256 / Source commit / Final status: READY TO SUBMIT — ARR October 2026 / NAACL 2027 target

## Key numbers (locked, don't change)
GSM8K vs strongest fixed: +29.0pp (1.5B), +16.7pp (7B). Memory ablation: GSM8K ~0pp 1.5B / +12.6pp 7B; PubMedQA +18.0pp 1.5B; QASPER +1.5pp. QASPER-7B diag: F1(extracted)=0.000, F1(whole)=0.107/0.172, marker=1.00.

## Git/proxy
Push via: git -c http.proxy=http://127.0.0.1:7897 -c https.proxy=http://127.0.0.1:7897 push origin main (fetch+rebase first).
