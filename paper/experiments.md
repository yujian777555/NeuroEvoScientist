# Experimental Protocol（Phase-19 迁移版，对应已执行实验）

> 本文档描述实际执行的协议。所有数字以 `results/` 与 `docs/` 产物为准；
> 旧版预期性表述已移除。

## Research Questions

- RQ1: 自动协同设计能否发现显著优于简单固定基线的 agent 认知配置？
- RQ2: 不同任务是否偏好不同的认知配置（holdout 上是否存活）？
- RQ3: 记忆/上下文选择对能力与推理成本的影响有多大？
- RQ4（审计性）：紧凑离散空间中，进化搜索是否比等预算随机搜索更样本高效？

## Frozen Protocol（Phase-19）

- 协议与锁定配置：`configs/phase19_protocol.yaml`、
  `results/phase19_selection_lock.json`（holdout 推理前锁定）。
- 骨干：Qwen2.5-1.5B-Instruct（主）与 Qwen2.5-7B-Instruct（转移），
  冻结、贪心解码、max_new_tokens=256。
- 评估区间（无泄漏）：
  - GSM8K：开发 test[0:100]（Phase-17/18 搜索用）；holdout test[100:1319]；
    记忆银行/适应仅用 train split。
  - PubMedQA：开发 samples[0:100]；holdout samples[100:500]；
    校准 samples[500:1000]。
  - 区间两两不相交有单元测试守护（`tests/test_phase19.py`）。

## Search Space（报告的 48 点离散空间）

```
memory:   recency | retrieval | mamba2 | hybrid
reasoning: direct | cot | verify | planner
context_policy: full | truncated | answer_only
quantization: fp16 (fixed, not searched)
```

## Methods Compared

- ENSS（Pareto 进化 + 继承 + 固定预算适应）
- Random Search（等预算、等适应预算）
- Fixed baselines：recency / retrieval / hybrid / mamba2（Direct+Full）
- Ablations：no_memory（去除情景记忆）、no_pareto、no_inherit、no_mamba2

## Analysis Protocol

- 穷举 48 点 landscape 作为分析 oracle（每基准一张表，含原始目标）；
- 搜索效率审计：在线策略仅能查询已评估点，预算 {12,24,36,48} × 20 seed，
  指标为 hypervolume / regret / ε-Pareto 命中 / evaluations-to-threshold / AUC；
- 继承配对研究：n=20 对，等预算，pre/post loss 与 capability；
- holdout 统计：逐题预测 + 配对 bootstrap 95% CI（10000 次，固定种子）
  + McNemar 精确检验。

## Hardware

1–6 × NVIDIA A800 80GB（共享集群，1 worker/物理卡）。
