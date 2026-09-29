# Experimental Setup (final, Phase-21)

## Research questions

- RQ1: Do cognitive architecture choices materially change capability–cost
  behavior above a frozen backbone?
- RQ2: Do tasks induce different architecture preferences, and do they
  survive held-out evaluation?
- RQ3: How large is the episodic-memory contribution under controlled
  same-genome ablation?
- RQ4 (audit): Is evolutionary search more sample-efficient than
  equal-budget random search in this space?

## Benchmarks and splits (leakage-safe)

| Benchmark | dev/search | holdout | calibration (memory/adaptation) |
|---|---|---|---|
| GSM8K | test[0:100] | test[100:1319] | train split only |
| PubMedQA | samples[0:100] | samples[100:500] | samples[500:1000] |
| QASPER | items[0:50] | items[50:150] | items[150:200] |

Pairwise disjointness of search/holdout/calibration ranges is enforced by
unit tests. Pre-registered selection locks (`results/phase19_selection_lock.json`,
`results/phase20_selection_lock.json`) were committed before any holdout
inference.

## Backbones

Qwen2.5-1.5B-Instruct (search/selection) and Qwen2.5-7B-Instruct
(transfer-only; no re-search). Greedy decoding, max 256 new tokens,
batch size 32, FP16. Exact HF revisions are recorded in the reproducibility
appendix.

## Protocol layers

### Compact audit layer (Phase-18)

- Exhaustive 48-point landscape per benchmark (capability, efficiency,
  token cost, latency, adaptation cost), used as the analysis oracle.
- Search-efficiency audit: online ENSS vs uniform random at budgets
  {12, 24, 36, 48} x 20 seeds; metrics: best capability, Pareto
  hypervolume, regret, epsilon-Pareto hits, evaluations-to-threshold, AUC.

### Structured co-design layer (Phase-20/21)

- Structured search on each benchmark's dev slice (population 16,
  generations 10, seeds 0-2), local mutations and block crossover.
- Locked per-task representatives, then held-out evaluation on all three
  benchmarks x both backbones with per-item predictions.
- Paired statistics: bootstrap 95% CIs (10,000 resamples, fixed seed) and
  exact McNemar tests on identical items.
- Controlled same-genome memory ablations (memory on/off, everything else
  frozen).
- Diagnostic-only QASPER failure analysis at 7B (raw outputs, marker
  compliance, extracted vs whole-continuation F1).

## Metrics

Capability = task accuracy (GSM8K numeric match; PubMedQA yes/no/maybe;
QASPER LongBench-compatible normalized QA F1 on the extracted final answer).
Cost = measured prompt-token count, latency, parameter footprint. Raw
objectives are persisted per candidate; no scalar aggregate is used for
selection or for headline claims.

## Hardware

1-6 x NVIDIA A800 80GB (single GPU suffices to reproduce).
