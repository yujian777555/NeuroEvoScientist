# Gate 2 — Planner Independent Audit / GO to F3 (2026-10-09)

Executor F2 commit: `ddd52dfb66bf5005a583d282aceacdd650804518`.
Pre-inference lock commit: `297d24e18cfaf464680f7e1def8ed829176ebbe3`.
Runner-source commit: `2644295fa81860737594327bcd5dfa7328545f4d`.
**Verdict: GO to F3 manuscript work, NO MORE GPU without separate authorization.**
The scientific result is a valid negative or mixed outcome, not evidence of optimizer superiority.

## Verified result evidence

Planner fetched all three committed 300-row prediction files and independently aligned IDs and rescored matched binary pairs. Each row includes full output and adapter score; 300 distinct IDs in each file, all aligned by order, 900/900 adapter_score = correct.
- REF: 211/300 = 0.703333
- B2: 215/300 = 0.716667
- B1: 211/300 = 0.703333
- PRIMARY REF vs B2: wins 23, losses 27, ties 250, Δ = −1.333pp, two-sided exact McNemar p = 0.671811. Reported bootstrap CI [−6.00,+3.33]pp.
- SECONDARY REF vs B1: wins 34, losses 34, ties 232, Δ = 0pp, p = 1.000000. Reported CI [−5.33,+5.33]pp.
- DESCRIPTIVE B2 vs B1: wins 33, losses 29, ties 238, Δ=+1.333pp, p = 0.703537.
- Full manifest: all three rows, model revision, data revision, source runner SHA, adapter SHA, IDs, seed 0, cache status false, 0 reported errors, total 215.785 seconds ≈0.060 aggregate GPU-hours. The F1 manifest provenance gap is not retroactively fixed.

## Cost / Pareto interpretation (exact tokens from manifest)

| Config | Accuracy | Prompt tokens | Generated tokens | Prompt+generated |
|---|---:|---:|---:|---:|
| REF | 70.33% | 68,017 | 50,049 | 118,066 |
| B2 | 71.67% | 197,017 | 44,137 | 241,154 |
| B1 | 70.33% | 19,117 | 48,264 | 67,381 |

- B2 has nominally 1.33pp higher accuracy but 2.90x REF prompt tokens and 2.04x total tokens.
- B1 has identical observed accuracy to REF with **3.56x fewer prompt tokens and 1.75x fewer total tokens**. This is IMPORTANT: there is NO cost-performance advantage of REF over B1 on these observed outcomes. Do not hide B1.
- Lack of statistically significant difference is NOT equivalence or proof of zero memory value. CIs include positive and negative effects. Claim NO DETECTABLE REF advantage over B2 and B1 under the locked SVAMP test.

## Correct scientific conclusion

F1 (GSM8K 100-item DEV): REF-B1 +10pp (p≈0.087) exploratory. F2 (independent-from-project SVAMP 300-item test): REF-B1 0pp (p=1). It is accurate to say the +10pp exploratory dev estimate was **not replicated on the chosen cross-benchmark evaluation**; it is NOT yet statistically proven that the task × memory treatment interaction differs. Do not write 'significantly more task-dependent' or 'proven non-transfer' based solely on contrasting p-values.

F2 is independent of the *project's selection/inspection history* according to versioned lock and single-shot report; SVAMP is a public benchmark in a different distribution, so pretraining contamination and dataset-shift caveats apply. Negative result reinforces LIMITED GENERALIZATION, not formal optimization superiority or inferiority. F2 is one model family, 1.5B only.

## Provenance qualification — must resolve during F3, NO NEW EXPERIMENT

Found a narrower-than-described source integrity check: `v2_quality/svamp_adapter.py::load_locked_test_rows()` validates only item count and ordered ID hash; it does **not** SHA-256-verify the full source file bytes or the model/source revision at runtime. Preflight/manifest recorded file sha256, but merely recording is not full runtime verification. A modified text/answer with the same IDs would evade that loader. This does not invalidate the independently reproduced paired counts, but means the phrase 'any dataset divergence hard-stops at runtime' is overstated.

F3 must execute a POST-HOC read-only forensic provenance audit:
- Independently recompute SHA256 of committed `v2_quality/fasttrack/data/svamp_test.json`, training artifact as recorded, adapter code, locked ID order, and exact 300-ID overlap with every prediction file; compare against the pre-inference lock and runner manifest.
- Inspect the actual inference log / source archive provenance and explicitly distinguish observed facts from runtime checks and claimed VM snapshots. Do not modify original F2 evaluator or old results / SHAs; add a SEPARATE versioned integrity validator/test for all subsequent readers, document that the run-time loader did not check full byte hash.
- If the full file hash differs from frozen lock, STOP F3 scientific claims and return BLOCKED to Planner; do not silently rerun F2 after seeing outcomes.

## F3 scope and deliverables

F3 is an **evidence-based paper edit**, not a new research experiment.
- Preserve V1 `paper/arr2026/`, `deliverables/final_submission/`, Phase17–21 results and F2 original result files as read-only. New paper under `v2_quality/paper/`.
- Make strong CoT-matched baselines, item-level confidence intervals, total token cost and the B1 cheaper equal-observed-accuracy result prominent. DO NOT claim search optimizer, evolutionary method, or memory universal superiority, statistical equivalence, or confirmed task×memory interaction.
- Separate historic V1 comparisons with Direct-only fixed baselines from F1 reused DEV and F2 independent cross-benchmark confirmation. Honest research story can be 'When does task-conditioned configuration selection generalize? A controlled negative-results and cost audit.'
- Include correct QASPER paired sign-test labeling and output extraction limitation. Do not create new figures or claims from obsolete `paper/phase21_tables.md` (materially wrong), only locked CSV/JSON.
- Produce manuscript, updated figures from existing immutable artifacts, references, anonymous supplementary, compiled review PDF, manifest/SHA, method-result trace, limitations; run full tests, ACL/ARR format/anonymity/compliance checks and page-by-page inspection. No fake automated claim of visual inspection.
- Verify next ACTUAL venue and deadlines before formulating a submission recommendation; no assumption that missing 2026-10-12 window still serves NAACL/COLING 2027.
- **STOP at Gate3 (paper-ready review); never upload/submit automatically.**

The user's priority remains earliest SCIENTIFICALLY DEFENSIBLE submission. Do not reopen long research phases without a concrete evidence blocker.
