# Kimi Code — FINAL Gate3 paper-only hotfix, then STOP

Repo https://github.com/yujian777555/NeuroEvoScientist | branch main
GPT=Planner, Kimi=Executor
Owner: wants earliest defensible publication; Oct 12 ARR is near.

## Authority: READ FIRST
Fetch/pull origin/main; read FULL:
- `v2_quality/fasttrack/gates/gate3_decision.md` — **Planner decision: CONDITIONAL GO** (this supersedes Executor recommendation).
- `v2_quality/paper/main.tex`, `manuscript.md`, `submission_manifest.md`, `audit_paper.py`
- `v2_quality/paper/audit_report.md` and `status.json`.

## Do the EXACT small paper correction, no GPU, no new experiment, no re-analysis of heldout predictions
1. Fix factual count throughout paper: **six predefined B0–B5 baselines (four CoT: B1–B4; two Direct: B0/B5), plus searched REF = seven total unique F1 configurations**. Never 'seven presets plus REF', 'seven CoT-matched presets' or 'six CoT plus two Direct'.
2. Fix CoT prompt-token cost claim: 8,091–67,391 = **8.33x**, with accuracy 49–60% on reused GSM8K dev; do not call '10x among CoT with similar accuracy'. Keep SVAMP B1=70.33% at 67,381 TOTAL tokens vs REF=70.33% at 118,066; no clear REF superiority.
3. Replace equivalence-sounding 'statistically indistinguishable' / casual 'ties' with 'no detectable accuracy advantage/difference at stated n', report effect sizes, CI and p; not equivalence.
4. Downgrade B4 one-off secondary p=.043 exploratory effect; it cannot prove context is MORE IMPORTANT than which preset; B4 specifically varies exemplar rendering, not universal context budget mechanism.
5. In `manuscript.md`, replace 'pre-registered' with 'pre-specified, commit-locked prior to evaluation' / 'pre-locked before inference'; synchronize actual scientific content of LaTeX/Markdown.
6. Arrange `Conclusion or Evidence Boundaries -> Reproducibility and Ethics -> Limitations -> References`, so the required Limitations is the last paper section before references; verify current ARR official CFP.
7. Tighten `audit_paper.py`: current pages check `len(doc)<=11` is misleading. Verify actual count of MAIN CONTENT pages <=8 and that Limitations/ethics/refs appear after the main conclusion; add deterministic regression tests for baseline counts, no 'pre-registered', no false 10x, no unwarranted equivalence. Re-run all tests/audits. Report actual coverage, not blanket claim of rigor.
8. Replace any categorical misuse claim in Ethics with appropriately qualified text.

Use ONLY locked V1/F1/F2 results. No GPU/LLM test inference, no rewriting old results, no new confound repairs. Preserve V1 PDF SHA e42191b0502f4b1ca7f7ed2bdd6b8b735ab0755294e185d2cd83156d22ae931d and ALL historical artifacts unchanged.

## Rebuild and delivery
Build NEW corrected V2 `main.pdf`, re-sync `main.tex`, `manuscript.md`, figures/bib if applicable, re-build anonymous `anonymous_supplementary.zip`, update `submission_manifest.md`, forensic report remains intact.
Render and individually inspect every PDF page, note layout fixes. Confirm PDF metadata/source/supp archive no author leaks, GitHub IDs, absolute server paths, hidden metadata; citations fully resolved; source-to-claim numeric checks; all CPU tests green; actual sha256/pages recorded.
Push updated `v2_quality/paper/` and `v2_quality/fasttrack/gates/gate3_final_check.md`, update `status.json` to `FINAL GATE3 HOTFIX COMPLETE — READY FOR OWNER UPLOAD` only if every guard passes. If blocked, mark BLOCKED with exact evidence. Stop; do NOT submit, do NOT enroll reviewers, do NOT modify public repo settings.

Report HEAD / clean / all changed files / test counts / F2 forensic integrity / old V1 hash unchanged / final PDF + supplementary sha256 + pages / proof of fixed textual errors and Limits order / anonymity and visual check / remaining administrative tasks and eligible venues. Official deadline Oct 12 2026 for NAACL/COLING last ARR, but don't promise eligibility without all-author OpenReview profiles and service-contributor policy compliance. Owner performs upload. Complete this phase now; no extra Planner–Executor research loops.
