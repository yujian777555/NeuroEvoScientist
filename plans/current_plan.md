# Phase 16 — Current Sprint Plan (Multi-seed matrix running)

依据 `plans/phase16_plan.md` 执行。

## Goal

产生论文核心证据：ENSS vs 固定/随机、任务依赖架构、memory 基底真实贡献。

## Tasks

- [x] Task 1 基础设施：延迟与 token 成本实测记录；跨 seed 评估缓存复用；多 seed 队列（22 个 GPU 运行已启动）
- [ ] Task 1 实验：矩阵跑完并聚合 `results/{phase16_matrix.csv, evolution_history.json, best_architectures.json}`
- [ ] Task 2 架构适应分析：GSM8K vs PubMedQA 最优架构的基因分布对比（写入 phase16_results.md）
- [x] Task 3 消融：no_memory 已实现（disable_memory）；w/o Evolution=fixed、w/o Pareto=no_pareto、w/o Inheritance=no_inherit 沿用
- [x] Task 4 Mamba 验证：validate_mamba.py 本地通过（状态可追踪 + 计算路径差异），产物 results/mamba_trace.json

## Verify

- [x] 38 pytest 全过
- [ ] 4 条成功判据在 3 seed × 2 基准上检验

## Success Criteria（phase16_plan.md）

1. ENSS > Random Search — 待多 seed 数据
2. ENSS > fixed baselines — Phase-15 已大幅成立，待复核
3. GSM8K 与 PubMedQA 产生不同架构 — Phase-15 弱成立，待复核
4. memory gene 真实影响性能与成本 — enss vs no_memory 对比，待数据

## Next

cron 监控 → 汇总 → docs/phase16_results.md → commit+push → 汇报。
