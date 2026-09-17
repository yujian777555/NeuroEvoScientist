# Phase 19 — Current Sprint Plan (Holdout running)

依据 `plans/phase19_plan.md` 执行。Phase-20 是条件阶段，等 Phase-19 门禁结果。

## Tasks

- [x] Task 1 协议冻结 + 选择锁定（commit 19c7c14，先于任何 holdout 推理）
- [x] Task 2 区间支持：评估器 start/limit + 逐题预测 + 不相交测试（51 tests 全过）
- [ ] Task 2 运行：GSM8K test[100:1319]、PubMedQA samples[100:500]（进行中，1.5B）
- [ ] Task 3 跨任务转移矩阵（同一批锁定配置双基准交叉，自动满足）
- [ ] Task 4 跨骨干转移（Qwen2.5-7B 下载中，完成后启动）
- [ ] Task 5 逐题统计（bootstrap CI + McNemar）
- [ ] Task 6 holdout 重审 C1/C2/C4/C7
- [ ] Task 7 论文迁移（7 个 paper/*.md 重写）
- [ ] Task 8 manuscript skeleton（manuscript_v1.md / abstract_v1.md / title_candidates.md）

## 锁定配置（10 个，不可更换）

A_gsm=Hybrid+Verify+Truncated；A_pubmed=Recency+Verify+Full；pareto×3；fixed×4；no_memory。

## Next

cron 监控 → Phase-19b（结果）→ Phase-19c（论文迁移）→ 汇报 Planner 门禁结论。
