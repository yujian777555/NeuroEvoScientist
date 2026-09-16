# Phase 18 — Current Sprint Plan (Running)

依据 `plans/phase18_plan.md` 执行。冻结方法，纯审计/复现阶段。

## Tasks

- [x] 配置冻结：phase18_eval.yaml / phase18_search_efficiency.yaml
- [ ] Task 1 双基准复现：enss/random/fixed×4/no_memory × seeds 0-2 × GSM8K+PubMedQA（GSM8K 侧复用 Phase-17 数据；其余运行中）
- [ ] Task 2 48 点 landscape：GSM8K + PubMedQA 穷举（运行中，两卡并行）
- [x] Task 3 搜索效率审计实现：oracle 在线策略 + hypervolume/regret/ε-命中/ETT/AUC（等 landscape 完成后本地跑）
- [ ] Task 4 继承配对研究：20 对（运行中）
- [x] Task 5 Mamba 结论冻结（claim_audit 中维持 negative，不再投入 GPU）
- [ ] Task 6 终版 claim 审计 + 论文门禁

## 事故记录（本阶段）

1. 继承研究父/子 substrate state_size 不一致 → 崩溃；已修（统一由 build_memory_controller 构造）
2. tar|ssh 同步 + nohup 启动合并写法令启动静默丢失（第三次）→ 规矩：同步与启动必须分开两条 ssh

## Next

cron 监控 → 汇总分析 → C1–C8 判定 → 文档与提交。
