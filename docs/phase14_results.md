# Phase-14 Results: First Real GSM8K Evolution Experiment

日期：2026-09-15
环境：A800 80GB × 5（1 worker/物理卡），Qwen2.5-1.5B-Instruct（fp16, greedy, max_new_tokens=256）
配置：GSM8K test 子集 limit=100，population=16，generations=10，seed=0，batch=32
原始日志：`experiments/*_gsm8k_seed0/`（history.jsonl + results.json + 评估缓存）

## Table 1: Baseline Matrix（真实 GSM8K）

| Method | Best Architecture | Fitness | Capability | Efficiency | Adaptability |
|---|---|---|---|---|---|
| **ENSS (full)** | Mamba + CoT + INT8 | **0.5205** | 0.3900 | 0.8840 | 0.3014 |
| Random Search | Mamba + CoT + INT8 | **0.5205** | 0.3900 | 0.8840 | 0.3014 |
| Fixed: Attention | Attention + Direct + None | 0.1985 | 0.1100 | 0.4325 | 0.0685 |
| Fixed: Mamba | Mamba + Direct + None | 0.2654 | 0.1100 | 0.6558 | 0.0685 |
| Fixed: Hybrid | Hybrid + Direct + None | 0.1655 | 0.1100 | 0.3227 | 0.0685 |

## Table 2: Ablations（真实 GSM8K）

| Ablation | Best Architecture | Fitness | Capability | Efficiency | Adaptability |
|---|---|---|---|---|---|
| Full ENSS | Mamba + CoT + INT8 | 0.5205 | 0.3900 | 0.8840 | 0.3014 |
| w/o NSGA Pareto | Mamba + CoT + INT8 | 0.5205 | 0.3900 | 0.8840 | 0.3014 |
| w/o Weight Inheritance | Mamba + CoT + INT8 | 0.5205 | 0.3900 | 0.8840 | 0.3014 |
| w/o Mamba Memory | Retrieval + Planner + INT8 | 0.4939 | 0.4100 | 0.7530 | 0.3151 |
| w/o Evolution (random) | Mamba + CoT + INT8 | 0.5205 | 0.3900 | 0.8840 | 0.3014 |

## Figure 1 数据：Evolution Curve（best/mean fitness per generation）

| Gen | ENSS best | ENSS mean | no_pareto best | random best(批内) |
|---|---|---|---|---|
| 1 | 0.495 | 0.435 | 0.495 | 0.495 |
| 2 | 0.520 | 0.483 | 0.520 | 0.503 |
| 3 | 0.520 | 0.486 | 0.520 | 0.511 |
| 4 | 0.520 | 0.507 | 0.520 | 0.483 |
| 5 | 0.520 | **0.520** | 0.520 | 0.511 |
| 6–10 | 0.520 | 0.520 | 0.520 | 0.35–0.51（不收敛） |

## 关键发现

1. **搜索 vs 固定设计的差距真实存在**：固定架构（Direct 推理）capability 仅 0.11；
   搜索到的架构（CoT/Planner 推理）达 0.39–0.41。这是本实验最有论文价值的信号。
2. **ENSS 第 2 代即找到全局最优，第 5 代种群完全收敛**（mean = best = 0.520）；
   random 在同预算下也碰到最优解，但批间波动大、无收敛性。
3. **ENSS ≈ random ≈ no_pareto 的最优 fitness 相同**：64 架构空间太小（pop×gen=160
   次评估已 2.5× 覆盖空间），进化相对随机的优势无法体现。与 Q2 预判一致。
4. **w/o Mamba 消融中最优变为 Retrieval+Planner+INT8**（capability 0.41 更高，
   但 efficiency 低 → 总 fitness 低）：体现多目标权衡在起作用。
5. **w/o inheritance 结果完全一致**：当前占位模块无训练过程，继承只省初始化成本；
   该消融要等真实微调介入后才有区分度（记录待 Planner）。

## 诚实声明（给 Planner）

- capability 的差异**全部来自 reasoning 模块的 prompt 模板**（Q3 问题的直接证据）：
  memory/compression 不影响 LLM 输出。Mamba 胜出是因为 efficiency 代理（参数量小）
  + capability 不受损，而非记忆能力本身被验证。
- 单 seed（seed=0）、limit=100 中规模；结论需 seeds 0/1/2 + 更大 limit 复核。
- 结论 1 严格说是"**推理策略的进化选择显著优于固定 Direct**"，
  要支撑论文标题级 claim 需要 Q3 的三个方向之一落地。

## 复现

见 `docs/phase14_a800_runbook.md`；本次实际执行脚本 `scripts_vm/run_method.sh`。
