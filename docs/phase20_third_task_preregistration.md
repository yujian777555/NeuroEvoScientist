# Phase-20 Third-Task Pre-Registration: QASPER (LongBench)

> 本文件在任何 QASPER GPU 运行之前提交冻结（Phase-20 Task 4 要求）。

## 任务选择理由（为什么它探测不同的认知需求）

QASPER（LongBench 子集）是科研论文问答：输入是**整篇论文全文**（数千 token），
答案需要从长文中定位并综合证据。

与现有两任务的结构性差异：
- GSM8K：短问题、多步算术推理 → 需求集中在 reasoning 基因
- PubMedQA：摘要级上下文、三分类判断 → 需求集中在记忆选择的信噪比
- QASPER：**长上下文证据整合** → 需求集中在 context_policy 的 token 预算分配
  与记忆的证据保留能力（长文档必须截断/选择，上下文成本成为硬约束）

预期架构分析维度（预注册）：
1. context_policy.token_budget 与 exemplar_count 在长文档下的取舍；
2. retrieval 记忆（按查询选证据段）是否首次成为最优记忆基因；
3. reasoning.depth 对证据综合的影响。

## 数据与划分（泄漏安全）

- 来源：LongBench qasper（THUDM/LongBench data.zip，本地缓存
  `data/qasper/qasper.jsonl`，共 200 题）
- **可用数据仅 200 题**，故划分调整为：dev = items[0:50]（搜索/调试）；
  holdout = items[50:150]；校准/记忆银行 = items[150:200]。三段两两不相交
  （有测试守护）。
- 答案格式：free-form；评测指标 = LongBench 官方词级 F1，
  答案取生成文本整体。

## 冻结承诺

- 评估协议（区间、指标、prompt 模板结构、生成参数）在本文件提交后冻结；
- 看到 holdout 结果后不得更换任务或区间；
- 若 QASPER 未产生distinct 架构偏好，按计划 stop condition 2 如实报告并停止。
