# NeuroEvoScientist: Task-Conditioned Cognitive Architecture Co-Design for LLM Agents

> Manuscript v1 skeleton（Phase-19 Task 8）。每个数值句内部标注来源产物。
> 证据基线：Phase-17/18/19（修正 schema）。Phase-14–16 仅作开发历史。

## 1. Introduction

- LLM agent 部署后认知结构固定；不同任务对记忆/推理/上下文的需求不同。
- 本文问题：能否在冻结主干之上，自动地按任务协同设计 agent 认知架构？
- 贡献 1–4（见 `paper/contribution.md`，逐条链到证据）。

## 2. Related Work

见 `paper/related_work.md`（无捏造引用；引用占位待正式文献工作）。

## 3. Problem Formulation

- 定义认知架构 genome G=(M,R,C)；多目标：capability、token 成本、延迟。
- 任务条件化目标：argmax per-task 前沿位置，而非单一全局最优。

## 4. Method: Cognitive Architecture Co-Design

见 `paper/method.md`：基因语义、进化算子、NSGA 选择、固定预算适应、
继承（附录机制）。冻结主干。

## 5. Experimental Protocol

见 `paper/experiments.md` 与 `configs/phase19_protocol.yaml`：
48 点空间、双基准、双骨干、泄漏安全区间、预注册锁定。

## 6. Main Results

- Table A：双基准主结果（`paper/phase18_tables.md` +
  `results/phase19_holdout_results.csv`）。
- GSM8K holdout：搜索配置大幅超固定基线（+33.8pp，p≈0；
  `results/phase19_statistics.json`）。
- PubMedQA：能力-成本权衡有竞争力，但 capability 维度不普遍占优
  （如实报告 fixed_retrieval 1.5B 反超）。

## 7. Task-Conditioned Transfer Analysis

- Figure 3/5：基因分布差异（Phase-18 稳定）+ holdout 2×2 转移矩阵
  （Phase-19，方向一致、效应小，诚实表述）。
- 成本维度：自有任务配置在 GSM8K 前沿上 −41% token 且能力不降。

## 8. Search-Efficiency Audit and Negative Results

- Oracle 审计：进化 ≈ 随机（Figure 4；`results/phase18_search_efficiency.csv`）。
- Mamba-2 负结果（Phase-17 stop condition；允许措辞）。
- 继承：效率改善、能力无差异（附录；`results/phase18_inheritance_pairs.csv`）。

## 9. Ablations and Cost Analysis

- no_memory：holdout capability −9.4pp（GSM8K 1.5B）/−11.2pp（7B），
  PubMedQA 7B −5.5pp（p=0.017）。
- 上下文策略 token-能力权衡（Figure 6）。

## 10. Limitations

- 单一模型家族（Qwen2.5）、紧凑离散空间、prompt 级推理策略、
  PubMedQA 三分类天花板效应、进化优势未在小空间显现。

## 11. Conclusion

任务条件化认知协同设计是可行且可复现的；审计纪律（锁定、泄漏防护、
配对统计、claim 审计）使负结果成为贡献而非威胁。

---

## 待补（论文写作阶段，需 Planner 批准）

- 正式参考文献（当前无捏造引用，占位）
- 图表渲染（数据已齐：`paper/phase18_figures_data.json` + Phase-19 产物）
- 投稿 venue 与排版模板
