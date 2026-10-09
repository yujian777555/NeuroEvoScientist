# Kimi Code — NeuroEvoScientist F3 FINAL PAPER HANDOFF

GitHub repo: https://github.com/yujian777555/NeuroEvoScientist
Branch main | GPT=Planner, Kimi=Executor
As of 2026-10-09, **Gate2=GO to F3**. The owner wants the earliest defensible V2 submission; no more research sprawl or GPU runs.

## STEP 1 — fetch the live authoritative instructions
Sync origin/main with `git fetch` + `git pull --ff-only`. Read FULL:
1. `v2_quality/fasttrack/gates/gate2_decision.md` (Planner independently audited F2; critical claim limits)
2. `plans/v2_f3_paper_finalize_plan.md` (COMPLETE F3 specification)
3. `v2_quality/fasttrack/f2_results.md`, `f2_results/run_manifest.json`, `f2_results/f2_statistics.json`
4. `v2_quality/fasttrack/gates/gate1_decision.md`, F1 prediction files and F1 report
5. `v2_quality/fasttrack/confirmation_lock.json` and `v2_quality/svamp_adapter.py`
6. `status.json`

Do not work from old chats or an outdated local checkout.

## STEP 2 — mandatory forensic F2 integrity check FIRST (CPU ONLY)
One defect was discovered: the original `load_locked_test_rows()` validated count and ordered IDs but NOT full dataset bytes at run time. Do not claim the full SHA was runtime-checked.

Without changing or rerunning any V1/F1/F2 evidence, create a new READ-ONLY forensic verifier that hashes the **entire saved SVAMP test bytes**, train artifact, adapter implementation, ordered IDs, and all 3×300 predictions, and checks them against the committed pre-inference lock and F2 manifest; verify model/source provenance as far as actually supported. Make it run on a normal checkout, fail on any mismatch, and put exact checks/results into `v2_quality/fasttrack/f2_provenance_forensic.md`.

If dataset SHA mismatches, STOP and report BLOCKED. Never massage metrics or rerun a public test after inspecting its scores to repair the story.
Ensure frozen V1 PDF hash unchanged.

## STEP 3 — create the separate V2 submission paper (NO GPU)
Write a FULL paper package under `v2_quality/paper/` and keep old V1 `paper/arr2026/` and `deliverables/final_submission/` untouched.

Positioning:
**'Task-conditioned LLM agent cognitive configurations affect accuracy and inference cost, but evolutionary search superiority and universal transfer are unsupported; transparent fair-baseline, cost and cross-benchmark audits matter.'**

Do not overclaim: this is QA-style single-agent scaffolding, not tool-use agent or backbone neural architecture search.

Must include:
- Locked old V1 results carefully scoped: +29.0/+16.7pp against four **Direct-only** fixed baselines, not search's isolated contribution.
- Equal-budget Phase18 ENSS≈Random negative result.
- F1 15 DEV-only comparisons, show strong CoT preset B2=0.59 vs REF=0.60 (1.5B GSM8K, +1pp p=1), REF-B1 +10pp p=0.087 (exploratory); 7B dev +10pp p=0.041 (secondary, unadjusted), and QASPER dev limitations.
- F2 300 original SVAMP test, 1.5B: REF 211/300=70.33%, B2 215/300=71.67%, B1 211/300=70.33%. PRIMARY REF–B2 -1.33pp CI [-6.00,+3.33] p=0.6718; SECONDARY REF–B1 0pp CI[-5.33,+5.33] p=1.
- F2 cost table: REF 68,017 input +50,049 output =118,066; B2 197,017+44,137=241,154; B1 19,117+48,264=67,381. **Crucial honesty: B1 has same observed accuracy as REF and uses ~1.75× fewer total tokens. REF has NO demonstrated accuracy or cost superiority over B1 in F2.**
- Compare F1 REF-B1 +10pp vs F2 0pp only as 'F1 positive point estimate not replicated cross-benchmark' — NOT a formal significantly different task×memory interaction, not equivalence, not proven universal lack of transfer.
- Address same Qwen model family, SVAMP public benchmark possible pretraining contamination, distribution shift, n=100/300 power, F1 missing exact VM source provenance, missing QASPER raw outputs, QASPER 7B extraction effects.
- Main table and graphical comparisons sourced from actual immutable CSV/JSON and 300-item prediction files, not stale `paper/phase21_tables.md` (known wrong values).
- ARR/ACL anonymous review formatting, accurate statistical labels (binary exact McNemar / continuous QASPER paired sign), proper recent Related Work MaAS/AgentSquare/Evo-Memory, Limitations/Ethics/References.

Compile new `v2_quality/paper/main.pdf`, preserve `main.tex`, `manuscript.md`, bibliography, figures, anonymous supplementary ZIP and manifest with PDF SHA, page count, exact commit, tests, citations and source-to-claim map. Visually render ALL pages and inspect. Do not assert success if not verified.

## STEP 4 — final checks, GitHub handoff, STOP
Run full CPU tests, the new file-hash forensic validator, data/citation and anonymity scans and PDF QA. Verify V1 hash unchanged and no historical experiment/result files modified.
Check official ARR/target venue schedules for the next actually eligible review cycle; do not promise NAACL 2027 eligibility after 2026-10-12. Do NOT submit via browser or OpenReview.
Commit and push the F3 outputs and `v2_quality/fasttrack/gates/gate3_decision.md`; update status.json to `V2 F3 COMPLETE / WAITING PLANNER GATE3 REVIEW`.

**Report:** HEAD and working tree; source hash checks; actual CPU tests; 300/300 per-item outcomes traced; all 3 model/cost numbers and paired stats; manuscript page count + SHA256; anonymous supplementary verification; candidate venue with official URL and verified future dates; remaining scientific risks and Gate3 GO/NO-GO. No GPU work and no unapproved experiments.

Proceed immediately. Only pause for a hard forensic failure or science-integrity blocker; otherwise finish the paper now, not more preliminary planning.
