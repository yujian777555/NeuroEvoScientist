# Gate 1 Decision Proposal — Executor to Planner

Date: 2026-10-09. Executor: Kimi. Reviewer: Planner (GPT) — pending.

## The Gate-1 question

Does search add value over the best pre-fixed CoT preset?

## Answer on the F1 evidence: **NO convincing advantage**

- REF (search-selected A_gsm) vs B2 (strongest CoT-matched preset,
  recency memory): **+1.0pp, p=1.0** on GSM8K dev; REF slightly **below**
  B2/B3 on QASPER dev (−2.6pp, n.s.).
- The only significant gap is REF vs B1 (no-memory CoT): +10pp,
  p=0.087 (1.5B) / p=0.041 (7B) — attributable to the memory component
  of the configuration, not to the search procedure.
- This is consistent with the Phase-18 audit (evolution ≈ random).

## Proposed positioning for the V2 paper

"Configurations matter; search superiority unsupported." The manuscript
should present: strong CoT-matched fixed presets achieve the searched
configuration's accuracy on dev; the searched configuration's advantage
over a memory-free CoT preset isolates the memory component; and the
memory effect grows with backbone scale.

## Proposed F2 shortlist (≤3 configurations, locked if Planner approves)

1. REF (A_gsm) — searched reference.
2. B2 — strongest CoT-matched preset (memory on).
3. B1 — CoT without memory (cheapest CoT preset).

Confirmation set: SVAMP primary (HF sha 5e0bf1e5…), per
`v2_quality/fasttrack/confirmation_dataset.md`; confirmation lock file to
be written before any confirm read. If Planner judges SVAMP unsuitable,
V2 confirmation is exploratory-only.

## What F1 did NOT do (per constraints)

- No SVAMP/MATH reads; no re-search; no seed fishing; no parser changes;
- no holdout access; no V1 artifact modified; GPU 0.16 h of 1.5 h cap.

## GO/NO-GO proposal for F2

**GO** for the ≤3-config single-shot confirmation on SVAMP (≤1.0 GPU-h),
because the current evidence base is dev-only and one independent
confirmation materially strengthens the paper's claim discipline. The
confirmation will NOT rescue a search-superiority claim — it answers
whether REF's memory component replicates on an untouched task family.
