# Independent Confirmation Dataset Feasibility (F0)

## Requirement

Phase-20 holdouts are inspected material. V2 needs either a genuinely
independent confirmation set or an explicit exploratory label.

## Candidates verified available (HF mirror, 2026-10-08)

| Dataset | Source | HF revision (sha) | Items | Relation to V1 tasks | License |
|---|---|---|---|---|---|
| SVAMP | ChilleD/SVAMP | `5e0bf1e5e7c0e9c4bc39180d224f41f3f801b7e` (mirror API) | ~700 test-style arithmetic word problems | same domain as GSM8K but different construction (variation perturbations of ASDiv problems) | Apache-2.0 per dataset card — verify before redistribution |
| MATH (algebra) | qwedsacf/competition_math | `e839825f9ec5c6cfa585c654a5` (mirror API) | ~12.5k problems | competition math, harder than GSM8K | MIT per upstream repo — verify before redistribution |

Feasibility: **viable**. Recommended primary: SVAMP (closest in style to
GSM8K, fully untouched by all V1 runs). MATH-algebra as secondary if SVAMP
proves too easy to separate.

## Contamination caveats (must be stated in the paper)

- No public benchmark can be guaranteed absent from LLM pretraining.
- V1 never evaluated or inspected SVAMP/MATH; independence from our
  *inspection* history is clean.
- QASPER/PubMedQA have no suitable same-distribution untouched set left
  (QASPER: 200 items fully partitioned; PubMedQA: all 1000 partitioned).
  For those tasks, V2 results remain exploratory unless a new source is
  locked at F1.

## Lock discipline

The confirmation item IDs will be frozen at F1 completion (before any
confirm read) in `v2_quality/fasttrack/confirmation_lock.json`, recording
dataset sha + exact indices.
