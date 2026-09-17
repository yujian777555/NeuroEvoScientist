# Paper Figures Plan（终版，Phase-19 迁移）

> 全部图直接由提交的聚合产物生成（`results/`、`paper/phase18_figures_data.json`）。

## Figure 1: Framework

任务条件化认知架构协同设计流程：Genome (M,R,C) → 进化控制器 →
记忆银行（train split，无泄漏）→ 多目标评估 → Pareto 选择 → 新一代。
与旧版图的区别：无 tool/compression 基因；backbone 冻结标注。

## Figure 2: Architecture Landscape（48 点全景）

每基准一张 capability × token-cost 散点 + Pareto 前沿。
数据：`results/phase18_pareto_fronts.json`、
`experiments/landscape_{gsm8k,pubmedqa}/landscape.jsonl`。

## Figure 3: Task-Conditioned Gene Distributions

GSM8K vs PubMedQA 的 Pareto 集/终代种群基因频率对比（memory、reasoning、
context_policy 三联条形图）。
数据：`results/phase18_architecture_distribution.json`。

## Figure 4: Search-Efficiency Audit（诚实负结果）

ENSS vs Random 的 best-capability / hypervolume vs 评估数曲线
（预算 12–48 × 20 seed，含 CI 带）。结论：打平。
数据：`results/phase18_search_efficiency.csv(+curves.json)`。

## Figure 5: Holdout Cross-Task Transfer Matrix

2×2 转移矩阵（A_gsm / A_pubmed × 双任务 holdout）+ 双骨干对比，
附 bootstrap CI 与 McNemar p。
数据：`results/phase19_statistics.json`、`phase19_cross_task_matrix.csv`、
`phase19_backbone_transfer.csv`。

## Figure 6: Cost–Capability Tradeoff（上下文策略）

full/truncated/answer_only 的 token 成本 vs capability（holdout 实测）。
数据：`results/phase19_holdout_results.csv`。

## Table A: 主结果（双基准 × 方法 × seed 均值±std）

`paper/phase18_tables.md` + Phase-19 holdout 表。

## Table B: 继承配对研究（附录）

`results/phase18_inheritance_pairs.csv`：post-loss 20/20 改善、
capability 0/20 无差异。
