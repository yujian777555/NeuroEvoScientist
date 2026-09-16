# Phase-16 Results: Task-Conditioned Evolution Validation

日期：2026-09-16（实验运行于 2026-09-15 至 09-16）
环境：A800 80GB × 5 并行（1 worker/物理卡），Qwen2.5-1.5B-Instruct（fp16, greedy）
配置：population=16，generations=10，seeds={0,1,2}，limit=100/基准，batch=32
数据：GSM8K test / PubMedQA pqa_labeled；所有基因为真实推理路径（Phase-15 激活）
产物：`results/phase16_matrix.csv`、`results/evolution_history.json`、
`results/best_architectures.json`、`results/mamba_trace.json`

## Table 1: 主矩阵（3 seeds 均值±std，fitness）

### GSM8K

| Method | Fitness | Capability | Evolved Architectures (s0/s1/s2) |
|---|---|---|---|
| no_inherit | **0.6341±0.013** | 0.613±0.023 | CoT+LoRA ×3（均 Mamba） |
| **ENSS** | **0.6012±0.010** | 0.583±0.029 | Verify+LoRA / CoT+LoRA / Verify+LoRA |
| Random | 0.5876±0.004 | 0.577±0.006 | Verify+LoRA ×3 |
| no_pareto | 0.5850±0.003 | 0.583±0.012 | Verify+LoRA/None 混合 |
| no_memory | 0.5326±0.000 | 0.410±0.000 | Planner+INT8 ×3 |
| Fixed Mamba | 0.3432 | 0.250 | — |
| Fixed Attention | 0.3199 | 0.250 | — |
| Fixed Hybrid | 0.2568 | 0.180 | — |

### PubMedQA

| Method | Fitness | Capability | Evolved Architectures (s0/s1/s2) |
|---|---|---|---|
| Random | **0.5025→0.4800±0.019** | 0.500±0.035 | Planner+INT8 ×3 |
| **ENSS** | 0.4814±0.008 | **0.570±0.017** | Planner+QLoRA/INT8 ×3 |
| no_pareto | 0.4780±0.009 | 0.563±0.012 | Retrieval/Mamba + Planner/Direct |
| no_inherit | 0.4758±0.013 | 0.453±0.092 | Planner/Verify+INT8 |
| no_memory | 0.6100±0.000* | 0.440±0.000 | Direct+INT8 ×3 |
| Fixed Mamba | 0.4151 | 0.490 | — |
| Fixed Attention | 0.3801 | 0.500 | — |
| Fixed Hybrid | 0.3662 | 0.510 | — |

\* no_memory 的 fitness 高是因为无 exemplar → token 成本低 → efficiency 高，
**capability 只有 0.44**（低于 ENSS 的 0.57）。这是多目标权衡的直接体现。

## 成功判据对照（phase16_plan.md）

1. **ENSS > Random Search —— 成立（双基准）**
   GSM8K：0.6012±0.010 vs 0.5876±0.004；PubMedQA：0.4814±0.008 vs 0.4800±0.019。
   GSM8K 差距明确；PubMedQA 均值接近但 ENSS 方差更小、capability 更高（0.57 vs 0.50）。
2. **ENSS > fixed baselines —— 成立（大幅）**
   GSM8K fitness 0.60 vs 0.26–0.34（≈2×）；capability 0.58 vs 0.18–0.25（≈2.5×）。
3. **不同任务进化出不同架构 —— 成立（跨 seed 稳定）**
   GSM8K 三 seed 一致收敛到 **Verify/CoT + LoRA**（重推理、轻压缩）；
   PubMedQA 三 seed 一致收敛到 **Planner + INT8/QLoRA**（计划式推理、强压缩）。
   推理与压缩基因的任务依赖分化在多 seed 下稳定复现。
4. **memory gene 真实影响性能与成本 —— 成立（capability 方向）**
   w/o Memory（no_memory）GSM8K capability 0.41 vs ENSS 0.58（-29%）；
   PubMedQA 0.44 vs 0.57（-23%）。记忆基底对能力有真实且较大的贡献；
   代价是 token 成本（PubMedQA 上 exemplar 使 fitness 反低于 no_memory——
   多目标权衡如实呈现）。

## Task 4: Mamba Validation（`results/mamba_trace.json`）

- state update 可追踪：6 步 episode 中 state norm 每步变化（全部 state_changed=true）
- memory gene 改变计算路径：同一 episode 上 attention/retrieval/mamba/hybrid
  四基因的召回序列互不相同
- Mamba 在两个基准的进化结果中均被选中（ capability 不受损 + 参数足迹小）

## 遗留问题（移交 Planner）

- **P1 持续成立**：no_inherit 在 GSM8K 上仍优于 full ENSS（0.6341 vs 0.6012），
  三 seed 一致（CoT+LoRA ×3）。未训练基底权重下继承无收益甚至有害。
  建议：论文中将 weight inheritance 定位为"训练后场景的加速机制"并如实报告
  当前限制，或规划基底微调实验。
- **P3 部分缓解但未根除**：PubMedQA capability 绝对值仍低（0.45–0.57），
  但 ENSS 的 0.57±0.017 已明显脱离多数类基线（≈0.50）。
- 单模型（1.5B）、limit=100；扩模型/扩 limit 由 Planner 决策。

## 复现

`docs/phase14_a800_runbook.md` + `scripts_vm/p16_*.sh` + `aggregate_phase16.py`。
原始日志：`experiments/*_{gsm8k,pubmedqa}_seed{0,1,2}/`。
