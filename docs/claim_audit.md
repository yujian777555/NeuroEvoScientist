# Claim Audit（Phase-19 holdout 后终版，2026-09-17）

证据基线：仅 Phase-17/18/19 修正 schema 产物。Phase-14/15/16 仅作开发历史。
Holdout：GSM8K test[100:1319]、PubMedQA samples[100:500]（与搜索/校准均不相交）。

| # | Claim | 终判 | 证据指针 |
|---|---|---|---|
| C1 | 自动协同设计发现优于简单固定基线的配置 | **supported（限定措辞）** | GSM8K holdout：+33.8pp/+14.8pp，p≈0（`results/phase19_statistics.json`）。PubMedQA 1.5B 上固定 retrieval 基线 capability 更高（−3.5pp n.s.）——允许措辞："在某些任务上大幅改进固定基线，在其他任务上产生有竞争力的能力-成本权衡"，禁止"普遍能力优越" |
| C2 | 不同任务偏好不同认知架构 | **partially supported（Phase-20 细分）** | C2a（搜索侧分布差异）强成立：三任务收敛到不同基因，PubMedQA 三 seed 一致选 none+direct，QASPER 预注册预测（retrieval 最优）命中（`results/phase20_selection_lock.json`）；C2b（自有任务 holdout 占优）仅 GSM8K 成立（+29~71pp, p≈0），PubMedQA/QASPER 上自有配置输给 GSM8K 配置（`results/phase20_statistics.json`） |
| C3 | ENSS 样本效率优于随机搜索 | **unsupported（永久关闭）** | Phase-18 oracle 审计决定性证据；Phase-19 不重开 |
| C4 | 情景记忆选择实质影响能力/成本 | **supported** | holdout 消融退化持续且显著：GSM8K +9.4/+11.2pp（p≈0）、PubMedQA 7B +5.5pp（p=0.017）；注意区分"有示例信息"与"特定记忆基底更优"——本文只主张前者 |
| C5 | Mamba 提升性能 | **unsupported（永久关闭，负结果保留）** | Phase-17 stop condition 触发；允许措辞见 phase18_plan Task 5 |
| C6 | 权重继承改善适应效率 | **partially → 附录机制** | n=20 配对：post-loss 20/20 改善、capability 0/20 无差异（`phase18_inheritance_pairs.csv`） |
| C7 | 上下文策略能力-成本权衡 | **supported** | holdout 真实 token 计数（`phase19_holdout_results.csv`） |
| C8 | 神经架构自进化 | **partial（限定措辞）** | "冻结 LLM 主干之上，可训练记忆基底+推理策略+上下文策略的进化协同设计"；禁止暗示全主干 NAS |

## 论文门禁结论（Phase-19/20 合并裁决）

C2a（任务条件化选择）强成立；C2b（自有任务占优）仅 GSM8K 成立。
论文框架 = **任务条件化认知协同设计 + 多目标能力-成本刻画 + 负结果审计**
（narrower paper 路线）。措辞红线：不得把 C2b 写成普遍结论。

## Phase-20 新增发现（docs/phase20_claim_update.md）

- N1：记忆贡献随骨干规模放大（GSM8K no_memory 差距 1.5B 0pp → 7B −12.6pp）
- N2：QASPER 检索策略在 7B 上不迁移（−13pp，骨干依赖真实存在）
- N3：dev 区间搜索偏好 ≠ holdout 泛化优势（小样本搜索过拟合警告）

## 可转移性补充证据

任务偏好方向在 Qwen2.5-1.5B 与 7B 间一致（无排名反转），支持
"backbone-independent 的方向性任务偏好"这一辅助观察。
