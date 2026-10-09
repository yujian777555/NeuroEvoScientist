# Gate 1 Planner Review — CONDITIONAL GO to F2 (2026-10-09)

Executor F1 evidence: commit `451dfa5acd7c108175725f07379abdb0d2dce9d6`.
Independent Planner review: **accepted numerical F1 evidence**; F2 only after strict dataset/provenance PRE-FLIGHT.

## What Planner independently checked

- GitHub contains 15 per-item predictions files and 15 summary rows.
- Recomputed matched pairs from committed item-level files:
  - 1.5B GSM8K REF vs B1: 60/100 vs 50/100; 19 wins / 9 losses; two-sided McNemar p=0.087159.
  - REF vs B2: 60/100 vs 59/100; 10 wins / 9 losses; p=1.
  - REF vs B3: 60/100 vs 57/100; 10 wins / 7 losses; p=0.629059.
  - REF vs B4: 60/100 vs 49/100; 18 wins / 7 losses; p=0.043285.
  - 7B REF vs B1: 85/100 vs 75/100; 15 wins / 5 losses; p=0.041389.
  - QASPER REF vs B2: mean 0.1667 vs 0.1922 (50 items), paired non-tie sign p=0.749259.
- The F1 15-cell aggregate device runtime of ~0.16 GPU hours is plausible from summary wall-time values, but `run_manifest.json` is NOT a complete proof: it contains only four 7B cells and 215 seconds because multiple invocations overwrite the shared manifest.
- `git_sha: unknown` in runner manifest and exact model revisions not recorded. F1 report cites runner commit `7a35430` but that does NOT independently prove all remote VM files matched; preserve limitation. Reconstruct historical summary metadata only from logs that exist; NEVER invent missing hashes.
- QASPER predictions log item-level scores but not raw model output in the evaluator; report this evidence limitation (and avoid claiming zero missing raw traces for all cells). No fabrication or rewriting old outputs.

## Scientific interpretation: restrained

- No **detectable / convincing** improvement of REF over pre-specified, strong CoT-matched B2 on this previously used DEV subset. This does NOT establish statistical equivalence or rule out a modest benefit; n=100 is underpowered.
- B2 uses 3 memory exemplars, REF uses 1: in DEV REF uses fewer prompt tokens with near-equal accuracy, but cost superiority needs proper multi-objective reporting and fair inference context.
- REF vs B1 differences combine exemplar presence with memory policy, not a direct algorithmic search effect. Note F1 1.5B and 7B both show +10pp on DEV; **F1 alone does not demonstrate a growing memory effect with scale**. Prior V1 held-out scales differed in memory effect, but are inspected material and cannot support a newly selected universal scaling law.
- 7B p=0.041 and B4 p=0.043 are secondary/exploratory unadjusted comparisons; not independent or corrected-for-multiple-testing confirmatory proof.
- Search superiority remains unsupported in audited compact landscape (Phase18) and F1 dev; optimizer-centric superiority claim prohibited.
- QASPER dev is exploratory and extraction-sensitive; F1 does not unlock new claims about QASPER quality recovery.
- F1 numerical results are **accepted subject to provenance limitations**, not final paper-grade confirmation.

## Critical F2 preflight corrections

F0 dataset description was inaccurate. The HF `ChilleD/SVAMP` card reports train 700, test 300 and MIT license (not ~700 test / Apache-2.0). The new authoritative dataset registration is `v2_quality/fasttrack/confirmation_dataset.md`.

Before F2 GPU, Executor MUST:
1. Read `plans/v2_f2_authorized_kimi_prompt.md`, this verdict, and corrected SVAMP registry.
2. Prove exact dataset revision/artifact SHA and schema from the pinned HF source. Confirm original **test** split has 300 rows; select entire test and freeze IDs/hash, before any model inference/score-driven inspection. Never mix train labels or use Equation in prompts.
3. Version and test adapter `Body + Question -> question`, `Answer -> numeric gold` with synthetic fixtures. No change to legacy GSM8K evaluator/scorer used by V1.
4. Validate no exact/normalized overlap with V1 GSM8K questions and F1 cached prompts; report near-duplicate limitations. Avoid peeking labels until lock.
5. Freeze list `REF, B2, B1` now, model Qwen2.5-1.5B-Instruct; predefine PRIMARY paired contrast (REF vs B2 on SVAMP) and SECONDARY (REF vs B1); report both with CIs and per-cell real prompt/completion tokens. Additional contrasts not primary.
6. Provenance: per-run executable source commit/hash, exact model revision, dataset revision/hash, prompt/parser version hashes, caching keyed by these and question ID; consolidated manifest must include all 3 F2 cells; record aggregate GPU time.
7. Verify README/data notices for license; ensure F2 dataset version immutable. Run full tests and synthetic parser tests; commit confirmation_lock.json and preflight before any F2 inference.
8. If ANY preflight guard fails, STOP and push failure analysis; no silent fallback to MATH and no unauthorized additional test reads.

## F2 bounded authorization

**CONDITIONAL GO**: After ALL checks pass, run exactly three configurations REF, B2, B1 on SVAMP's locked 300-row test split, **1.5B only**, aggregate F2 cap **≤1.0 GPU-hour**. No search, no parameter tuning, no reusing V1 inspected holdout as confirmation. F2 result classified cross-benchmark confirmation on a PUBLIC benchmark, not truly out-of-pretraining-distribution guarantee.

After F2, commit/push exact predictions, per-cell metrics+tokens, paired statistics and `v2_quality/fasttrack/gates/gate2_decision.md`. STOP; do not draft a new final paper until Planner reviews Gate2.

No automatic additional GPU, no benchmark switch upon results, no anonymous upload or venue submission.
