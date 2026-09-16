# Phase-17 Results: Corrected Substrate Semantics + Real Mamba-2 Validation

日期：2026-09-17（实验 09-16 至 09-17）
环境：A800 × 4，Qwen2.5-1.5B-Instruct（fp16, greedy, HF_HUB_OFFLINE）
配置：GSM8K（train split 经验银行 + 48 样本校准，无 test 泄漏），
limit=100，pop=16，gen=10，seeds={0,1,2}，适应预算 30 AdamW 步/候选
产物：`results/phase17_focused_matrix.csv`、`phase17_inheritance_curve.json`、
`phase17_pareto.json`、`mamba_trace.json`（真实 Mamba-2 轨迹）

## Table 1: 聚焦矩阵（GSM8K，3 seeds 均值）

| Method | Fitness | Capability | 收敛架构 |
|---|---|---|---|
| no_mamba2 | **0.6829** | 0.620 | Recency + Verify + Truncated ×3 |
| Random | **0.6829** | 0.620 | Recency + Verify + Truncated ×3 |
| **ENSS** | 0.6811 | 0.620 | Recency/Hybrid + Verify + Truncated |
| no_inherit | 0.6811 | 0.620 | Recency/Hybrid + Verify + Truncated |
| Fixed Retrieval | 0.4070 | 0.250 | — |
| Fixed Recency | 0.3994 | 0.240 | — |
| Fixed Mamba2 | 0.3623 | 0.260 | — |

## 核心问题：真实 Mamba2 + 适应 + 继承是否改善 Pareto 前沿？

**答案：否（在本协议下）。** 演化收敛的最优是 Recency/Hybrid 记忆，
真实 Mamba2 基底候选的平均 capability 0.49，低于获胜的 recency 策略（0.62）。
继承方向性改善（见下）但不足以让 Mamba2 系架构胜出。

## 继承实验（Task 3，等预算对照）

| 初始化 | n | mean capability | mean post-adaptation loss |
|---|---|---|---|
| 继承（父代适应后权重） | 2 | **0.535** | **0.621** |
| 全新初始化 | 19 | 0.489 | 0.738 |

方向首次转正：继承的候选适应后 loss 更低、capability 更高（样本量小，n=2，
标注为弱证据）。Phase-16 的"继承有害"在基底可训练后消失——
P1 的机制假设（未训练权重是噪声）被证实。

## 中途工程事件（如实记录）

- Mamba2 状态缓存 bug：recall 每查询重算整个银行的前向，CPU 熔化 24h。
  修复（每银行配置缓存一次）后速度恢复，并新增回归测试。
- 监控一度被旧 schema 同名目录误报，已加 schema 校验。

## 成功判据（phase17_plan.md 门禁）

- [x] 占位 nn.Linear 不再叫 Mamba（真实 Mamba2Model）
- [x] 真实 Mamba-2 通过顺序/状态/梯度测试（VM 53 tests 全过）
- [x] context policy 不再误标 LoRA/QLoRA/INT8
- [x] 无 train/test 泄漏（银行仅 train split，有测试）
- [x] 继承比较等适应预算
- [x] 原始 Pareto 目标持久化（history.jsonl population + phase17_pareto.json）
- [x] 3-seed 聚焦实验完成
- [x] claim 审计更新（docs/claim_audit.md）

## Stop-condition 触发声明

按计划 Stop conditions：真实 Mamba 集成在受控适应后**未提供获胜信号**，
因此：
- 不再投入 GPU 强行支撑 Mamba claim；
- Mamba2 基因如实保留在空间中（真实实现、可训练、可继承），
  但论文 claim 中**不**声称"Mamba 记忆提升性能"；
- 保留更强的贡献：任务条件化的 agent 记忆/推理/上下文策略进化搜索。
