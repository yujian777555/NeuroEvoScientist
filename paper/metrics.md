# Evaluation Metrics（Phase-19 迁移版，对应实际测量）

## Capability

- 任务准确率（GSM8K 数值答案匹配；PubMedQA yes/no/maybe 决策匹配）
- holdout 上以逐题预测做配对统计（bootstrap CI、McNemar）

## Cost / Efficiency

- **prompt token 数**（真实 tokenizer 计数）——上下文策略的主要成本维度
- **延迟**（每次评估的实测 wall-clock 秒数）
- 参数量足迹代理（基底参数量；FP16 固定）
- 注：跨骨干不直接比较延迟（硬件/批量设置不同则不作对比）

## Adaptability

- 难/偏移子集准确率（GSM8K 多步题；PubMedQA "maybe" 类）

## Search Quality（审计指标，非 headline）

- Pareto hypervolume（capability × efficiency，参考点 (0,0)）
- 相对全局前沿的 hypervolume regret
- ε-Pareto 命中概率、evaluations-to-threshold、best-so-far AUC
- 重复评估率

## Evolution Process（描述性）

- 逐代 best/mean fitness 与 Pareto 前沿（`history.jsonl`）
- 最终种群的架构基因分布

## 已废止指标

- 旧"压缩基因效率"（legacy schema 误标，Phase-17 起移除）
- 任何把单一标量 fitness 当作主要科学结论的用法
