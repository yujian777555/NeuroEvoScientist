# Expected Results → Observed Results Status（Phase-19 迁移版）

> 本文件原为实验前预期设计。现将每条预期替换为**实际观察结果状态**。
> 证据指针：`docs/claim_audit.md`、`results/phase18_*`、`results/phase19_*`。

## 原预期 1：ENSS > 无 Pareto 进化 > 随机搜索 > 固定架构

**观察：部分成立。**
- 搜索（进化或随机）>> 固定基线：成立（GSM8K holdout capability
  0.54 vs 0.21–0.23，+33.8pp，p≈0）。
- ENSS ≈ 随机搜索：**不成立**（Phase-18 oracle 审计决定性打平）。
  该排名假设已从论文中移除。

## 原预期 2：Mamba 记忆在长上下文任务上更优

**观察：不成立（负结果）。** 真实可训练 Mamba-2 基底参与搜索但未被选中；
PubMedQA landscape 上 Mamba2+Direct+AnswerOnly 恰是 capability 最高单点
（0.6175 holdout），但这是孤点而非进化偏好。按措辞规则封存。

## 原预期 3：Pareto 进化带来更优权衡

**观察：部分成立。** 进化种群的 Pareto 集刻画了真实的能力-成本权衡；
自有任务配置在 holdout 上占 capability-cost 前沿优势（GSM8K 上 −41%
token 且能力更高）。但"比随机搜索更优"不成立。

## 原预期 4（新增，计划外发现）：任务条件化架构偏好

**观察：方向一致、效应小。** 基因分布差异跨 seed 稳定（Phase-18）；
holdout 自有任务优势方向 4/4 一致但统计不显著（Phase-19）。
按规则降级为谨慎表述。

## 原预期 5（权重继承提升搜索效率）

**观察：效率维度成立、能力维度不成立。** n=20 配对：适应后 loss 20/20 改善，
capability 0/20 无差异 → 降级为附录机制。

## 方法学结论

"最终论文必须验证改进来自进化而非随机选择"——验证结果是**否定**的
（在当前 48 点空间）。这本身是本文的核心实证发现之一。
