# F0 Locked Protocol (FAST-TRACK V2)

Date: 2026-10-08. Scope: F0 audit + protocol lock only. NO GPU was used.
Authority: `plans/v2_fasttrack_submission_plan.md` (active),
`plans/v2_quality_upgrade_plan.md` (controls/backlog).
V1 frozen at PDF SHA-256 `e42191b0…22ae931d`; nothing in V1 is modified.

## 1. Hypotheses under test (F1)

- H1 (capability): searched A_gsm does NOT beat the strongest CoT-matched
  fixed preset on GSM8K dev by a practically meaningful margin
  (null-friendly framing; we test for a *difference*, either direction).
- H2 (cost): A_gsm achieves its capability at materially fewer prompt tokens
  than CoT+full exemplar presets.
- H3 (memory, 7B): on GSM8K, enabling recency memory on the frozen CoT
  scaffold changes capability (direction measured, not assumed).
- H4 (Pareto): A_gsm occupies a frontier point among {B0..B5, REF} under
  capability × prompt-token cost.

Primary endpoint (pre-registered): GSM8K dev accuracy of B1 vs REF with
paired bootstrap CI and exact McNemar (binary items). Everything else is
secondary/exploratory.

## 2. Fixed baselines (definitions locked)

| ID | memory | reasoning | context/exemplars | role |
|---|---|---|---|---|
| B0 | none | direct | full / none | historical reference (descriptive) |
| B1 | none | cot depth 3 | full / none | **strongest CoT preset** |
| B2 | recency k=3 | cot depth 3 | full / 3 | CoT + recency memory |
| B3 | retrieval tf-cosine k=3 | cot depth 3 | full / 3 | CoT + retrieval memory |
| B4 | none | cot depth 3 | answer_only exemplar budget | CoT, reduced tokens |
| B5 | none | direct | full / none | low-token cost reference |
| REF | A_gsm frozen (recency k=3, cot d3, full, 1 exemplar) | — | — | V1 reference, never retuned |

Prompt template identical across all CoT cells (`reasoning_prompt`,
depth=3, greedy, 256 max new tokens, batch 32, FP16). Parser frozen:
GSM8K `####` numeric extraction; QASPER LongBench-compatible normalized F1
on extracted answer. No parser edits after first confirm read.

## 3. Splits and independence

- DEV: GSM8K test[0:100], QASPER items[0:50] (already-used dev slices;
  fine for method development).
- Phase-20 holdouts (GSM8K test[100:1319], PubMedQA[100:500],
  QASPER[50:150]) are **inspected material** — reused only descriptively,
  never as new confirmation.
- Independent confirmation candidates (see confirmation_dataset.md):
  SVAMP (ChilleD/SVAMP, HF sha 5e0bf1e5) and MATH (qwedsacf/competition_math,
  HF sha e839825f). To be locked at F1 end before any confirm read.

## 4. Statistics and multiplicity

- Paired bootstrap 95% CI (10,000 resamples, fixed seed 20261008).
- Exact McNemar for binary items; two-sided exact paired sign test for
  continuous QASPER F1. Effect sizes first; no p-only conclusions.
- One primary comparison (B1 vs REF on GSM8K dev). All others flagged
  exploratory; multiplicity note applies (Benjamini–Hochberg if any family
  claim is made).

## 5. Compute controls and stop rules

- 1.5B for discovery; 7B only for the prechosen shortlist transfer.
- Budget cap: see compute_budget.md (hard cap 12 GPU-hours for F1).
- Stop F1 early if B1 ≈ REF within ±2pp on GSM8K dev: then claim becomes
  "configurations matter; search superiority unsupported" and F2/F3 follow
  the negative-results route. No optimizer rescue iterations.

## 6. Integrity guards (fail-closed)

- Cache keys include genome + model + range + pipeline version.
- Any dataset/registry edit after a confirm read invalidates that read.
- Run manifest: run_id, git_sha, model sha, dataset sha, seed, runtime,
  tokens, GPU-hours, failure traces.
- No holdout peeking during F1; deviation register in f-reports.
