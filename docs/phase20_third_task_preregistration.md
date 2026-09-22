# Phase-20 Third-Task Pre-Registration: QASPER (LongBench)

> 本文件在任何 QASPER GPU 运行之前提交冻结（Phase-20 Task 4 要求）。
> **2026-09-22 修订（hotfix gate）**：语义修正版取代初版；初版下产生的
> Phase-20 QASPER 运行（固定 2500 词截断、未规范化 F1、dense 命名）
> 一律标记 invalid，不作论文证据。

## 任务选择理由（为什么它探测不同的认知需求）

QASPER（LongBench 子集）是科研论文问答：输入是**整篇论文全文**（数千词），
答案需要从长文中定位并综合证据。

与现有两任务的结构性差异：
- GSM8K：短问题、多步算术推理 → 需求集中在 reasoning 基因
- PubMedQA：摘要级上下文、三分类判断 → 需求集中在记忆选择的信噪比
- QASPER：**长上下文证据整合** → 需求集中在 input_context_budget
  （文档预算）与记忆/上下文的证据保留能力

## 修正后的测量语义（hotfix H1-H6）

1. `input_context.budget`（词数，{512,1024,2048,4096}）直接控制进入模型的
   论文文档词数 —— 真实的基因控制文档预算；
2. 指标为 "LongBench-compatible normalized QA F1 on extracted final answer"
   （LongBench 官方规范化：小写、去标点、去冠词、空白规整；
   预测取 '####' 之后的文本，无标记时取整个续写）；
3. 检索度量命名 hashed_bow（哈希词袋余弦），不称 dense retrieval；
4. exemplar 预算为 exemplar_word_budget（词数，非 token）；
5. 嵌入为 SHA-256 稳定哈希（跨进程确定性，有子进程回归测试）。

## 数据与划分（泄漏安全）

- 来源：LongBench qasper（`data/qasper/qasper.jsonl`，共 200 题）
- dev = items[0:50]（搜索/调试）；holdout = items[50:150]；
  校准/记忆银行 = items[150:200]。三段两两不相交（有测试守护）。

## 预注册分析维度

1. input_context_budget 与 exemplar_count 在长文档下的取舍；
2. retrieval 记忆是否首次成为最优记忆基因；
3. reasoning.depth 对证据综合的影响。

## 冻结承诺

- 评估协议（区间、指标、prompt 结构、生成参数）在修订版提交后冻结；
- 看到 holdout 结果后不得更换任务或区间；
- 若 QASPER 未产生 distinct 架构偏好，按 stop condition 如实报告并停止。

