# Phase 20 — Current Sprint Plan (DONE)

依据 `plans/phase20_plan.md` + `plans/phase20_hotfix_plan.md` 执行完毕。

## Tasks 终态

- [x] Task 1 结构化基因组 + hotfix 门禁（H1-H6 全部修复并有回归测试）
- [x] Task 2 结构化算子（局部变异 + 块交叉 + 规范化去重）
- [x] Task 3 任务特定证据：锁定 → holdout 2×2×3 × 双骨干 → 配对统计
- [x] Task 4 第三任务 QASPER（预注册、泄漏安全划分、LongBench 兼容 F1）
- [x] Task 5 机制分析（10 案例，item ID + exemplar + 模型输出）
- [x] Task 6 跨骨干验证（1.5B→7B，排名一致性 + 崩溃案例记录）
- [x] Task 7 搜索空间刻画（random 仅诊断参考；C3 未重开）
- [x] Task 8 claim 锁定 v2（claim_audit.md 更新）

## 结论摘要

- C2a（任务条件化选择）：**强成立**（三任务基因分布 distinct，QASPER 预注册命中）
- C2b（自有任务占优）：**仅 GSM8K 成立**；PubMedQA/QASPER 自有配置落败（如实）
- 新发现：记忆作用随骨干放大；QASPER 7B 崩溃；dev 偏好 ≠ holdout 泛化

## Next

等 Planner 指示：论文收尾（Phase-21）或其他。
