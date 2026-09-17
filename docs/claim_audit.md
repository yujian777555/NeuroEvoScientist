# Claim Audit（Phase-19 holdout 后终版，2026-09-17）

证据基线：仅 Phase-17/18/19 修正 schema 产物。Phase-14/15/16 仅作开发历史。
Holdout：GSM8K test[100:1319]、PubMedQA samples[100:500]（与搜索/校准均不相交）。

| # | Claim | 终判 | 证据指针 |
|---|---|---|---|
| C1 | 自动协同设计发现优于简单固定基线的配置 | **supported（限定措辞）** | GSM8K holdout：+33.8pp/+14.8pp，p≈0（`results/phase19_statistics.json`）。PubMedQA 1.5B 上固定 retrieval 基线 capability 更高（−3.5pp n.s.）——允许措辞："在某些任务上大幅改进固定基线，在其他任务上产生有竞争力的能力-成本权衡"，禁止"普遍能力优越" |
| C2 | 不同任务偏好不同认知架构 | **partially supported（降级措辞）** | 方向性一致（4/4 比较为正）但效应小、个体不显著（`phase19_statistics.json`）；能力-成本权衡维度成立（GSM8K 自有配置 −41% token 且能力更高）。保留表述："任务间架构基因分布稳定不同 + 自有任务配置在能力-成本前沿占优" |
| C3 | ENSS 样本效率优于随机搜索 | **unsupported（永久关闭）** | Phase-18 oracle 审计决定性证据；Phase-19 不重开 |
| C4 | 情景记忆选择实质影响能力/成本 | **supported** | holdout 消融退化持续且显著：GSM8K +9.4/+11.2pp（p≈0）、PubMedQA 7B +5.5pp（p=0.017）；注意区分"有示例信息"与"特定记忆基底更优"——本文只主张前者 |
| C5 | Mamba 提升性能 | **unsupported（永久关闭，负结果保留）** | Phase-17 stop condition 触发；允许措辞见 phase18_plan Task 5 |
| C6 | 权重继承改善适应效率 | **partially → 附录机制** | n=20 配对：post-loss 20/20 改善、capability 0/20 无差异（`phase18_inheritance_pairs.csv`） |
| C7 | 上下文策略能力-成本权衡 | **supported** | holdout 真实 token 计数（`phase19_holdout_results.csv`） |
| C8 | 神经架构自进化 | **partial（限定措辞）** | "冻结 LLM 主干之上，可训练记忆基底+推理策略+上下文策略的进化协同设计"；禁止暗示全主干 NAS |

## 论文门禁结论（Phase-19 stop rules 裁决）

C2 在 holdout 上以"方向一致但统计不显著 + 成本维度占优"的形式部分存活。
按规则不走 fullest claim；论文框架 = **任务条件化认知协同设计 + 多目标
能力-成本刻画 + 负结果审计**（narrower paper 路线，Phase-18 已定，Phase-19 维持）。

## 可转移性补充证据

任务偏好方向在 Qwen2.5-1.5B 与 7B 间一致（无排名反转），支持
"backbone-independent 的方向性任务偏好"这一辅助观察。
