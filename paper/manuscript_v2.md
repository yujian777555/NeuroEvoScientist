# NeuroEvoScientist: Task-Conditioned Cognitive Architecture Co-Design for LLM Agents — A Controlled Study of Generalization, Cost, and Failure Modes

> Manuscript v2（Phase-21 终版骨架）。证据基线：Phase-17–21（修正 schema）。
> 每个关键数值标注来源产物。

## 1. Introduction

LLM agent 部署后认知结构固定。本文问两个问题：认知架构选择是否实质影响
能力-成本行为？任务条件化的自动搜索能否泛化到未见数据？（贡献列表见
`paper/contribution.md`。）

## 2. Related Work

见 `paper/related_work.md`（占位引用待正式化）。

## 3. Problem Formulation

认知架构 genome G=(M,R,C)（+ 结构化子基因）；多目标：capability、
token 成本、延迟；目标为 per-task 前沿刻画而非全局最优点。

## 4. Method

见 `paper/method.md`：基因语义（含结构化子基因）、规范化与任务感知表型、
进化算子（生成机制，非优越性声明）、固定预算适应、泄漏安全协议。

## 5. Experimental Protocol

见 `paper/experiments.md`、`configs/phase19_protocol.yaml`、
`configs/phase20_protocol.yaml`、第三任务预注册、hotfix 语义门禁。

## 6. Main Results

- **R1 架构选择实质重要**：GSM8K holdout 搜索配置 vs 最强固定基线
  +29.0pp（1.5B）/+16.7pp（7B）（`results/phase20_statistics.json`）。
- **R2 任务条件化选择稳定且可解释**：三任务收敛到不同基因；QASPER
  预注册预测（retrieval 最优）命中（`results/phase20_selection_lock.json`）。
- **R3 dev 偏好不等于 holdout 泛化**：PubMedQA/QASPER 自有配置在
  holdout 上输给 GSM8K 配置（显著；同来源）。
- **R4 记忆贡献受控且随骨干放大**：同基因消融 1.5B 无差异 → 7B −12.6pp；
  PubMedQA 受控消融 +18.0pp（`phase21_ablation` 结果）。
- **R5 任务-骨干交互**：QASPER 7B"崩溃"经诊断为答案提取/格式失配
  （`docs/phase21_qasper7b_diagnostic.md`），非能力缺失。

## 7. Audit and Negative Results

- 进化 ≈ 随机（Phase-18 oracle 审计；不重开）
- Mamba-2 真实但未被选中（Phase-17 stop condition）
- 权重继承：适应效率改善、能力无差异（n=20 配对，附录）
- hotfix 语义门禁记录（稳定嵌入、表型去重、命名诚实化）

## 8. Mechanism Analysis

14 个可审计案例（`docs/phase20_mechanism_analysis.md`）：含 GSM8K 成败、
PubMedQA、QASPER 双骨干配对失效（raw output + 提取答案 + 检索 exemplar）。

## 9. Limitations

见 `paper/limitations.md`。

## 10. Conclusion

认知架构选择实质影响 agent 的能力-成本行为；自动协同设计能暴露清晰的
任务条件化偏好，但这些偏好会过拟合小搜索集并与骨干规模强烈交互。
严谨的 holdout 审计是把"搜索侧特化"与"可泛化架构优势"区分开的必要条件。
