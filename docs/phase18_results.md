# Phase-18 Results: Corrected Dual-Benchmark Replication + Search-Efficiency Audit

日期：2026-09-17
环境：A800 × 6 并行，Qwen2.5-1.5B-Instruct（fp16, greedy, HF_HUB_OFFLINE）
配置：phase17 schema（无 legacy 语义泄漏），limit=100，pop=16，gen=10，seeds={0,1,2}
产物：`results/phase18_*.csv/json`、`paper/phase18_tables.md`、`paper/phase18_figures_data.json`

## Table A: 修正 schema 主结果（3 seeds 均值；固定基线为确定性单次）

### GSM8K

| Method | Fitness | Capability | Efficiency |
|---|---|---|---|
| no_mamba2 | 0.6829±0.000 | 0.620±0.000 | 0.859 |
| Random | 0.6829±0.000 | 0.620±0.000 | 0.859 |
| **ENSS** | 0.6811±0.002 | 0.620±0.000 | 0.859 |
| no_memory | 0.5571±0.000 | 0.410±0.000 | 0.964 |
| Fixed Retrieval | 0.4070 | 0.250 | 0.803 |
| Fixed Recency | 0.3994 | 0.240 | 0.803 |
| Fixed Hybrid | 0.3836 | 0.210 | 0.810 |
| Fixed Mamba2 | 0.3623 | 0.260 | 0.628 |

### PubMedQA

| Method | Fitness | Capability | Efficiency |
|---|---|---|---|
| no_memory | 0.6272±0.000* | 0.440±0.000 | 0.873 |
| **ENSS** | 0.5012±0.000 | 0.530±0.000 | 0.727 |
| Random | 0.5012±0.000 | 0.530±0.000 | 0.727 |
| Fixed Retrieval | 0.4822 | 0.540 | 0.707 |
| Fixed Recency | 0.4781 | 0.520 | 0.727 |
| Fixed Hybrid | 0.4757 | 0.520 | 0.719 |
| Fixed Mamba2 | 0.4398 | **0.570** | 0.516 |

\* no_memory 高 fitness 源于无 exemplar 的极低 token 成本；其 capability 最低。

## 判据 C1–C8 终判

| Claim | 状态 | 证据 |
|---|---|---|
| C1 自动搜索 > 固定人工架构 | **supported（GSM8K 大幅；PubMedQA 以 fitness/效率维度成立）** | GSM8K capability 0.62 vs 0.21–0.26；PubMedQA fitness 0.5012 vs 0.44–0.48（capability 上 fixed_mamba2 0.57 反超——如实报告） |
| C2 不同任务偏好不同架构 | **supported（修正 schema 下复现）** | GSM8K→Verify+Truncated+Hybrid/Recency；PubMedQA→Verify+Full/AnswerOnly+Recency；两基准 Pareto 集基因分布不同（`phase18_architecture_distribution.json`） |
| C3 ENSS 比随机搜索更样本高效 | **unsupported（明确否定）** | Oracle 审计（48 点 landscape，预算 {12,24,36,48} × 20 seed）：AUC 与 hypervolume 在全部预算×基准上与随机打平（差 <0.01，方向不定）。按计划规则移除搜索优越性措辞 |
| C4 情景记忆显著影响能力/成本 | **supported** | no_memory 消融：GSM8K cap 0.41 vs 0.62（-34%），PubMedQA 0.44 vs 0.53（-17%）；token 成本反向变化 |
| C5 Mamba 提升性能 | **unsupported（负结果保留）** | Phase-17 触发 stop condition；Phase-18 未投入 GPU 试图扭转。允许措辞见下 |
| C6 权重继承改善适应效率 | **partially supported（n=20 配对）** | post-loss 继承侧 20/20 全胜（-0.070），pre-loss 起点更低（-0.266）；但 capability 差 20/20 全为 0——效率机制成立、能力增益不成立，降级为附录机制 |
| C7 上下文策略在能力与 token 成本间权衡 | **supported** | landscape 实测 token 数：full > truncated > answer_only，且能力大致递减（`phase18_landscape` 数据） |
| C8 神经架构自进化 | **partially supported（谨慎措辞）** | 采用计划推荐措辞：冻结 LLM 主干之上对可训练记忆基底+推理策略+上下文策略的进化协同设计 |

## Figure 数据

- Figure A（任务条件化基因分布）：`results/phase18_architecture_distribution.json`
- Figure B（搜索效率曲线）：`results/phase18_search_efficiency_curves.json`
- Figure C（48 点 Pareto 前沿）：`results/phase18_pareto_fronts.json`（GSM8K 前沿 8 点 / PubMedQA 10 点）
- Table B（继承配对）：`results/phase18_inheritance_pairs.csv`

## 论文走向建议（按计划的 Decision 节）

C1 + C2 + C4 成立，C3 不成立 → 走"narrower paper"路线：
**自动化任务条件化 agent 认知协同设计**；进化是搜索引擎，不声称优于随机。
