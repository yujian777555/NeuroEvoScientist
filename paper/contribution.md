# Main Contributions（Phase-19 迁移版，终版语义）

> 语义基线：Phase-17 修正 schema + Phase-18 审计 + Phase-19 holdout 验证。
> 证据指针见 `docs/claim_audit.md`；旧版措辞（tool/compression 基因、
> "self-evolving neural architecture"）已废止。

## Contribution 1: Task-Conditioned Cognitive Architecture Co-Design

We propose a unified search framework that co-designs an LLM agent's cognitive
architecture — episodic memory policy, reasoning strategy, and context policy —
above a **frozen** LLM backbone.

Paper-facing genome (matches the reported search space exactly):

```
G = (M, R, C)

M = episodic memory policy/substrate   {recency, retrieval, mamba2, hybrid}
R = reasoning strategy                 {direct, cot, verify, planner}
C = context policy                     {full, truncated, answer_only}
```

Quantization is fixed to FP16 in all reported experiments and is not presented
as a searched gene. No tool gene is varied in the reported experiments.

## Contribution 2: Multi-Objective Empirical Characterization

We provide a complete 48-point architecture landscape on two benchmarks
(GSM8K, PubMedQA) with raw Pareto objectives — capability, prompt-token cost,
latency, adaptation cost — rather than a single scalar score.

Evidence: `results/phase18_pareto_fronts.json`,
`experiments/landscape_{gsm8k,pubmedqa}/landscape.jsonl`.

## Contribution 3: Task Dependence and Negative Findings

- Architectures preferred by math reasoning and biomedical QA differ, with
  stable gene-distribution shifts across seeds (Phase-18) and a
  capability–cost advantage for own-task configurations on held-out data
  (Phase-19).
- Equal-budget evolutionary search does **not** beat random search in this
  compact space (Phase-18 oracle audit, budgets 12–48 × 20 seeds).
- A real, trainable Mamba-2 memory substrate is included in the space but is
  **not** automatically beneficial — evolution preferred simpler recency/hybrid
  memory (Phase-17).

We report these negative results as contributions to scientific credibility.

## Contribution 4: Reproducible Audit Protocol

Corrected gene semantics, leakage-safe calibration/evaluation splits,
per-item predictions, paired bootstrap + McNemar statistics, an explicit
claim audit, and held-out + cross-backbone transfer evaluation.

Evidence: `configs/phase19_protocol.yaml`, `results/phase19_selection_lock.json`,
`results/phase19_statistics.json`, `docs/claim_audit.md`.
