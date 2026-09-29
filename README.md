# NeuroEvoScientist

**Task-conditioned cognitive architecture co-design for LLM agents.**

> 本 README 对应锁定后的最终科学定位（Phase-21）。历史愿景文档见
> `docs/`（各 phase 计划与结果）；论文稿见 `paper/`。

## What this is

A controlled study and framework for co-designing an LLM agent's cognitive
architecture — **reasoning strategy, episodic memory/exemplar policy, and
context allocation** — above a **frozen** backbone, under multiple
capability–cost objectives.

Final genome (paper-facing):

```
G = (M, R, C)   + structured sub-genes (Phase-20)

M = episodic memory policy/substrate   {none, recency, retrieval, mamba2, hybrid}
R = reasoning strategy                 {direct, cot, verify, planner}
C = context policy                     {full, truncated, answer_only}
    + input-context budget (long-document tasks)
```

Quantization is FP16 in all reported experiments (not a searched gene).
No tool gene is varied.

## Benchmarks

- **GSM8K** — multi-step arithmetic reasoning (Cobbe et al., 2021)
- **PubMedQA** — biomedical research QA, yes/no/maybe (Jin et al., 2019)
- **QASPER** — long-context scientific-paper QA (Dasigi et al., 2021;
  LongBench version, Bai et al., 2023)

## What the experiments found

Supported:

- Cognitive architecture choices materially change capability–cost behavior;
  a searched configuration beats the strongest fixed baseline on untouched
  GSM8K holdout by +29 to +71 percentage points (McNemar p<0.001).
- Search-side architecture preferences differ clearly and stably by task
  (e.g., the long-context task shifts the optimum to retrieval-based memory,
  as pre-registered).
- Controlled same-genome memory ablations show memory contributions that
  grow with backbone scale (0pp at 1.5B, −12.6pp at 7B on GSM8K;
  +18.0pp on PubMedQA at 1.5B).

Negative / bounded findings (kept, not hidden):

- Equal-budget evolutionary search does **not** beat random search in the
  compact space (oracle audit, 20 seeds × 4 budgets).
- A real trainable Mamba-2 substrate is valid but not selected as beneficial.
- Dev-selected task-specific architectures do not universally generalize on
  holdout (PubMedQA/QASPER are beaten by the GSM8K-selected configuration).
- A QASPER "collapse" at 7B is a backbone–prompt/extraction interaction,
  not a capability failure (diagnosed in `docs/phase21_qasper7b_diagnostic.md`).

## Reproduce

```bash
pip install -r requirements-a800.txt
python -m pytest tests/ -q                      # 79 passed / 11 skipped (CPU)
python src/scripts/run_experiment.py --method enss --benchmark gsm8k \
    --model Qwen/Qwen2.5-1.5B-Instruct --limit 20   # real-pipeline smoke
python src/scripts/render_figures.py            # final figures from artifacts
```

Full protocol: `paper/reproducibility_appendix.md`.

## Paper artifacts

- Manuscript: `paper/manuscript_v3.md` (final), `paper/abstract_v2.md`
- Tables/figures data: `paper/phase21_tables.md`, `paper/phase21_figures_data.json`,
  `paper/figures/`
- Claim audit: `docs/claim_audit.md`, `docs/phase21_final_audit.md`
- Selection locks (pre-holdout): `results/phase19_selection_lock.json`,
  `results/phase20_selection_lock.json`

## Status

Experiments are **frozen** (Phase-21 stop rule). No new experimental
development unless a reviewer requests a specific additional experiment.

Freeze anchor commits: `57d2465` (Phase-21 lock), `5ad4b50` (submission freeze).

## License

See `LICENSE` (decision by the repository owner).
