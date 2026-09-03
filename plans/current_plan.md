# Phase 12 — Current Sprint Plan

## Goal

打通 MVP 实验闭环：Genome → Builder → Candidate Agent → Evaluation → Fitness → Evolution → New Generation。

## Tasks

- [x] `src/genome/search_space.py` — 加载 `configs/search_space.yaml`，枚举 8 种架构组合，随机采样
- [x] `src/genome/architecture.py` — reasoning 默认值对齐搜索空间（direct），新增 `describe()`
- [x] `src/models/builder.py` / `hybrid_agent.py` — 按 genome 组装 agent（mamba/attention 记忆、direct/verify 推理、none/lora 压缩，CPU 轻量占位实现）
- [x] `src/evolution/mutation.py` — 变异收敛到配置文件定义的 3 模块空间
- [x] `src/evolution/crossover.py` — 模块级均匀交叉
- [x] `src/evolution/controller.py` — 完整进化循环：评估 → fitness → NSGA3 Pareto 选择 + 锦标赛 → 交叉/变异 → 精英保留
- [x] `src/evolution/fitness.py` — capability/efficiency/adaptability 加权标量化（0.5/0.3/0.2）
- [x] `src/evaluator/benchmark.py` — MockEvaluator（确定性伪任务）+ benchmark 注册接口，预留 GSM8K/AgentBench/PubMedQA
- [x] `src/evaluator/metrics.py` — capability（任务均分）/ efficiency（参数量代理）/ adaptability（分布偏移任务均分）
- [x] `src/scripts/run_enss.py` — 入口脚本，逐代输出 + 最优 Agent
- [x] `status.json` / `CHANGELOG.md` / `requirements.txt`

## Verify

- `python src/scripts/run_enss.py` 在 CPU 环境跑完 10 代（pop=16）
- 输出逐代 `Agent` + `Fitness`，末代输出 `Best Agent`
- 所有产生的架构均属于 8 种合法组合
- 同 genome 重复评估 fitness 一致（确定性 Mock）

## Success Criteria

- 入口命令一次跑通无异常，适应度随世代有改进趋势
- status.json / CHANGELOG.md 更新并随 `[Phase-12]` commit 推送
