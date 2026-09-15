# Phase 15 — Current Sprint Plan (Matrix running, awaiting results)

依据 `plans/phase15_plan.md` 执行。

## Goal

把 ENSS 从 prompt 模板级进化升级为真实神经基底进化（回答 Q3）。

## Tasks

- [x] Task 1: 真实记忆基底 — `src/evaluator/memory.py`（attention/retrieval/mamba/hybrid 四种 episode 记忆控制器）
- [x] Task 2: 基因组激活 — 每个基因真实影响推理：memory 决定注入哪些经验、compression 决定上下文预算（真实 token 成本）、reasoning 决定指令模板；测试证明不同 memory 基因产生不同 prompt
- [x] Task 3: 科学基准 — `src/evaluator/pubmedqa.py`（pqa_labeled 1000 题），已注册并入 run_experiment
- [ ] Task 4: 重跑进化 — 6 方法 × 2 基准矩阵运行中（5 卡并行，cron 监控）

## Verify

- [x] `pytest tests/` — 34 passed（含基因组激活真实性测试）
- [x] GPU 冒烟通过，最优架构与 Phase-14 不同（基因真正影响结果）
- [ ] 矩阵完成后：GSM8K 与 PubMedQA 是否进化出不同架构（成功判据 1）

## Success Criteria 对照（phase15_plan.md）

1. 不同任务产生不同进化架构 — 待矩阵结果
2. memory 基因影响真实计算 — 已实现并有测试证据
3. ENSS 优势不只来自 prompt 模板 — 待矩阵结果
4. 结果支撑 neural substrate evolution claim — 待矩阵结果

## Next

矩阵完成（cron 自动检测）→ 汇总 → docs/phase15_results.md → 汇报 Planner。
