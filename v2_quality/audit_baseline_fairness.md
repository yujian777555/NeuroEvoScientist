# V2-0 Baseline Fairness Audit

Date: 2026-10-08 (post-Phase-21, pre-any-V2-experiment)
Scope: audit only. No GPU, no new scores; all numbers read from locked artifacts.
Sources: `results/phase20_holdout_results.csv`, `results/phase20_selection_lock.json`,
`results/phase20_statistics.json`, `results/phase19_holdout_results.csv`,
`results/phase18_search_efficiency.csv`, `paper/phase21_tables.md`.

## 1. Baseline configuration table (as actually run)

| Config | memory | reasoning | context | exemplars | input budget | notes |
|---|---|---|---|---|---|---|
| A_gsm (searched) | recency k=3 | **CoT depth 3** | full | 1 | 2048 | V1/V2 reference |
| A_pubmed (searched) | none | direct | full | 0 | 1024 | canonical no-memory |
| A_qasper (searched) | retrieval hashed_bow k=4 | direct | truncated 256w | 8 | 1024 | |
| fixed_recency | recency k=3 | **direct** | full | 3 | 2048 | |
| fixed_retrieval | retrieval tfidf k=3 | **direct** | full | 3 | 2048 | |
| fixed_mamba2 | mamba2 | **direct** | full | 3 | 2048 | |
| fixed_hybrid | hybrid | **direct** | full | 3 | 2048 | |
| no_memory | recency k=3 | CoT depth 3 | full | 0 injected | 2048 | A_gsm genome, memory off |

## 2. The confound, verified against locked data

All four fixed baselines use **Direct** reasoning. The searched A_gsm uses **CoT**.
The +29.0pp (1.5B) / +16.7pp (7B) margin over "strongest fixed" therefore
conflates prompt-strategy difference with any search/memory contribution.

Locked GSM8K holdout numbers (verified against `phase20_holdout_results.csv`):

| Config | 1.5B | 7B | prompt tokens (shared) |
|---|---|---|---|
| A_gsm (recency+CoT) | 0.5185 | 0.8597 | 300,124 |
| no_memory (A_gsm minus memory) | 0.5193 | 0.7342 | 101,427 |
| best fixed (1.5B: fixed_recency; 7B: fixed_mamba2) | 0.2289 | 0.6932 | 808,447 / 881,587 |

Verified readings:

1. **At 1.5B, the CoT-style no-memory configuration accounts for the observed margin in this comparison, but component-specific attribution needs matched Direct/CoT controls.** A_gsm minus memory
   (same CoT prompt, no exemplars) already reaches 0.5193 ≈ A_gsm 0.5185
   with ~3x fewer prompt tokens. The searched-memory contribution at 1.5B is
   null (−0.08pp, p=1.0 in the paired test).
2. **At 7B, memory contributes +12.6pp on top of CoT** (0.7342 → 0.8597,
   p<0.001) — the only controlled memory effect on GSM8K.
3. **The fixed baselines were not token-starved**: they used 2.6–3.2x more
   prompt tokens than A_gsm yet lost badly. Cost is not the driver; the
   Direct-vs-CoT prompt difference is the confound.
4. Phase-18 audit: evolution ≈ budget-matched random (both reach the same
   optimum in the 48-point space). No search-algorithm advantage exists to
   attribute.

## 3. What +29.0pp / +16.7pp can and cannot show

CAN claim (and V2 keeps claiming only this): automatically discovered
configurations can substantially exceed four Direct+Full fixed presets on
GSM8K holdout.

CANNOT claim: (a) that the margin demonstrates evolutionary search value
(the same region is reachable by random); (b) that memory drives the 1.5B
gain (paired ablation is null there); (c) that the margin survives a
CoT-matched fixed preset — that is exactly what V2-1 must test.

## 4. Fair-baseline design for V2 F1 — Planner correction

Authoritative versioned baseline definitions are in `v2_quality/fasttrack/baselines_f1.json`. Original F0 proposal accidentally duplicated B0/B5 (Direct/no-memory), and B1/B4 were behaviorally identical because both lacked exemplars. The new controls are distinct:

| ID | memory | reasoning | context | distinguishing comparison |
|---|---|---|---|---|
| B0 | none / 0 exemplars | direct | full | Direct with zero memory |
| B1 | none / 0 exemplars | CoT d3 | full | CoT vs B0; memory off vs REF |
| B2 | recency k3 / 3 exemplars | CoT d3 | full | exemplar count vs REF |
| B3 | TF-cosine retrieval k3 / 1 exemplar | CoT d3 | full | memory type vs REF |
| B4 | recency k3 / 1 exemplar | CoT d3 | answer_only, 128-word exemplar limit | context verbosity vs REF |
| B5 | recency k3 / 1 exemplar | direct | full | reasoning strategy vs REF |
| REF | recency k3 / 1 exemplar | CoT d3 | full | V1 locked A_gsm |

Prompt-hash and canonical phenotype-identity checks are mandatory before GPU. `B1` is a pre-defined strong CoT preset, not a pre-proven strongest CoT baseline; winner claims require transparent selection and independent confirmation.

## 5. Interaction design (V2-2, pre-specified cells)

Factorial Memory {off, recency} × Reasoning {direct, cot} × Context
{full, answer_only-budget} = 8 cells; GSM8K + QASPER; report main and
interaction effects with CIs. No "single-gene" language for mixed changes.

## 6. Open questions for Planner

1. Is B1 (CoT+Full+no-memory) acceptable as THE strong preset, given it is
   already measured at 0.5193/0.7342 on the (inspected) Phase-20 holdout?
   V2-1 must evaluate on DEV only; confirm reads only after lock.
2. QASPER parser: current extraction takes text after the last '####'.
   Any parser change must be a versioned sensitivity study over ALL configs.
3. PubMedQA's ceiling limits separation; V2-1 primary task = GSM8K, with
   QASPER as the structurally different second task.

## 7. Corrected archival warning

The initial F0 archival audit incorrectly claimed `paper/phase21_tables.md` matches locked Phase-20 CSV. This is false. See `v2_quality/fasttrack/archival_discrepancies.md`: several GSM8K and PubMedQA entries differ materially, including GSM8K 7B A_qasper legacy 0.693 vs locked 0.1961. Use frozen CSV, not historical markdown tables, for new comparisons.
