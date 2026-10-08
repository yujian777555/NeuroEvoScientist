# V2 FAST-TRACK — earliest defensible submission (2026-10-08)

STATUS: ACTIVE PLANNING OVERRIDE, awaiting Executor's protocol audit. Supersedes the `timeline and mandatory scope` in `plans/v2_quality_upgrade_plan.md`; the full V2 plan remains an optional research backlog. **Never overwrite V1 frozen paper or results**.

## Owner intent
Not obsessed with an October deadline, but wants to submit as soon as defensible. Optimize elapsed calendar time, not number of experiments. Goal: minimum sufficient upgrades with rigorous attribution and a timely submission; no 7–10 week research program by default.

## Venue/deadline reality
Official ARR dates show October 12, 2026 as the last ARR submission cycle for NAACL 2027 and COLING 2027. Review/service requirements require human checks. If no new experiments and the author explicitly prioritizes this specific cycle, the V1 paper can be submitted on time with limitations and existing locked claims; do NOT assert new stronger baselines were evaluated or independently validated.
A study with new co-design baselines cannot be responsibly compressed into four days as a guaranteed result. An upgraded V2 paper submitted after October 12 cannot use the same ARR cycle for NAACL/COLING 2027; find the next actually announced ARR/venue dates on official sites, without inventing a deadline (ACL 2027 calls currently indicate January 2027 ARR cutoff).
Do not automatically submit; human author makes the venue/portal decision.

## Default active route: FAST-TRACK V2 (target ~10–21 calendar days, subject to resources)

**Stage F0 (1–2 calendar days) — short audit and lock (NO GPU).**
Focus ONLY on baseline fairness, cached history and provenance, feasibility of the independent confirmation dataset, cost budget, answer parser freeze, exact CoT-matched comparator definitions. Old inconsistencies and obsolete archival tables: flag/SUPERSEDED; check whether any old table leaked into submission package.
Deliver `v2_quality/fasttrack/f0_gate.md`, a compact locked protocol + run matrix and budget. Permit reusing outputs of ongoing V2-0 (do not duplicate work). If no independent confirmation set, explicitly classify future analysis as exploratory. **STOP, request Planner gate approval before GPU.**

**Stage F1 (3–6 calendar days) — mandatory strong baselines, limited GPU.**
Run on discovery/dev first (NOT the repeatedly inspected V1 holdout as 'untouched'):
- Strong fixed CoT+NoMemory+Full.
- Strong fixed CoT+Recency+Full (same prompt/other controls).
- Strong fixed CoT+Retrieval+Full.
- A cost-controlled CoT+reduced exemplars/context configuration.
- Existing locked A_gsm as historical reference (comparisons with new runs labeled exploratory unless a new clean confirmation set is used).
Use both 1.5B and 7B only where justified; prefer 1.5B discovery, 7B transfer on prechosen shortlist.
Collect item predictions, accuracy/F1, token counts, latency and budget-matched Pareto; no re-search. Record strengths/weaknesses transparently.
Gate F1: compare search versus strongest FAIR CoT human baseline; if no convincing benefit, change claim/positioning to `configurations matter; search superiority unsupported` rather than launching optimizer rescue.

**Stage F2 (2–5 calendar days) — minimal independent confirmation and/or one informative interaction.**
If independent confirmation dataset or partition truly uncontaminated by V1 inspection exists and was frozen at F0: evaluate ONLY preselected small shortlist once using precommitted parser, and compare separately from old holdout.
Else, do NOT mislabel reused old holdout as new validation: report as exploratory, and consider a small rigorously separated confirmation benchmark even if it reduces scope.
Optional 2x2 interaction (Memory on/off × Direct/CoT) at matched context on DEV if required to support the main manuscript claim. Full factorial, new model family, and broad NAS-style search are deferred unless F1 reveals a decisive need.
Do not run Phase V2-3 evolutionary-vs-random search by default. V1's negative result remains authoritative in the compact space.

**Stage F3 (3–5 calendar days) — final writing, audit and submission (NO NEW SCIENTIFIC SEARCH).**
Generate a NEW versioned V2 manuscript/PDF under `v2_quality/paper/`. Leave `paper/arr2026/` and `deliverables/final_submission/` intact as V1.
- Honest matched baseline and cost-aware table.
- Distinguish configuration gain from optimizer efficacy.
- Check QASPER extraction/statistics, obsolete tables and supplementary.
- Audit protocol, code/results, citations, anonymity, ethics, PDF and service contributor requirements.
- Pick next actual venue/cycle once date and quality are known; no unsupported NAACL 2027 promises after Oct 12.
If Phase F1 yields null or unfavorable results, a sound negative-results and causal-audit paper is acceptable.

**STOP rule:** If F1 performance implies little added value, stop GPU work. No automatic F4+ research without owner approval. No more than a few expensive V2 experiments unless necessary to close a concrete scientific flaw.

## Explicit choices / fork
- **Fastest clock-time submission**: frozen V1 in October 12 ARR, no new experiments, all paperwork and conservative wording completed. Owner must authorize actual upload and accept current baseline weakness.
- **Default, higher-quality fast submission**: focused F0–F3; estimated 10–21 calendar days under stable A800 resources and suitable confirmation data. Venue may change. If independent evaluation/data or code repair is delayed, 3–5 weeks; not a guaranteed delivery time.
- **Extended V2**: full phases in `plans/v2_quality_upgrade_plan.md` only upon clear post-gate scientific motivation and owner preference; NOT currently authorized.

## Rules and acceptance
No overwrites of V1; preserve complete experiments/results. No data leakage or holdout relabeling; report confirmation limitations.
Minimum scientific passing evidence: fair baseline with controlled reasoning, cost-aware, appropriately paired statistics, traceable code commits and test logs; if new strong-baseline evidence does not support strong claims, explicitly downgrade them.
Kimi to report at F0: source SHA, exact files, status/clean, audit findings, 1.5B/7B cost proposal, independent-data feasibility, ETA conditional and GO/NO-GO. Request Planner before GPU.
