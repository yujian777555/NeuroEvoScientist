# Claim Audit（终版，Phase-18 收官，2026-09-17）

仅采信修正 schema（Phase-17/18）证据。Phase-14/15/16 结果仅作开发历史参考。

| # | Claim | 终判 | 证据指针 |
|---|---|---|---|
| C1 | 自动搜索优于固定人工架构 | **supported** | `results/phase18_dual_benchmark.csv`；GSM8K cap 0.62 vs 0.21–0.26；PubMedQA fitness 0.501 vs 0.44–0.48（附注：PubMedQA capability 维度 fixed_mamba2 0.57 反超，全文不得隐去） |
| C2 | 不同任务偏好不同认知架构 | **supported** | `results/phase18_architecture_distribution.json`；GSM8K→Verify+Truncated，PubMedQA→Verify+Full/AnswerOnly，跨 3 seed 稳定 |
| C3 | ENSS 比等预算随机搜索更样本高效 | **unsupported** | `results/phase18_search_efficiency.csv`：AUC/HV 全预算打平（<0.01）。按 Phase-18 规则从摘要/贡献中移除搜索优越性措辞；进化保留为实现机制 |
| C4 | 情景记忆选择实质影响 capability/成本 | **supported** | no_memory 消融 cap -34%（GSM8K）/ -17%（PubMedQA）；`phase18_dual_benchmark.csv` |
| C5 | Mamba 提升性能 | **unsupported（负结果）** | Phase-17 聚焦实验；允许措辞："搜索空间包含真实可训练 Mamba-2 基底；在本协议下进化更偏好更简单的 recency/hybrid 记忆，说明 ENSS 能拒绝无益的复杂基底" |
| C6 | 权重继承改善适应效率 | **partially supported → 附录机制** | `results/phase18_inheritance_pairs.csv`（n=20 配对）：post-loss 20/20 改善；capability 0/20 无差异。不得作为头条贡献 |
| C7 | 上下文策略在能力与成本间权衡 | **supported** | landscape 实测 token 计数（`experiments/landscape_*/landscape.jsonl`） |
| C8 | 神经架构自进化 | **partially supported（限定措辞）** | "冻结 LLM 主干之上，可训练记忆基底+推理策略+上下文策略的进化协同设计"；不得暗示全主干 NAS |

## 论文门禁结论

C1 + C2 + C4 成立、C3 不成立 → 按计划走 narrower paper 路线：
**任务条件化的 agent 认知架构协同设计**；进化是搜索引擎而非被声称的优越优化器。
