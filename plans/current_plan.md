# Phase 14 — Current Sprint Plan (Infra complete, GPU run blocked)

依据 `plans/phase14_plan.md` 执行。

## Goal

将 ENSS 从框架验证升级为论文级实验验证。

## Tasks

- [x] Task 1: 真实 LLM 后端 — `src/evaluator/backends.py`（QwenBackend: Qwen2.5-1.5B-Instruct，chat template 自动识别）
- [x] Task 2: A800 实验配置 — `requirements-a800.txt` + `docs/phase14_a800_runbook.md`（pop=32, gen=20，先冒烟再正式）
- [x] Task 3: 基线矩阵 — `src/scripts/run_experiment.py --matrix`：3 固定架构 + random + no_pareto + enss
- [x] Task 4: GSM8K benchmark — 真实评测管线已接 `--benchmark gsm8k`（数据自动下载）
- [x] Task 5: 消融 — no_pareto / no_inherit / no_mamba / random(w/o evolution) 全部实现

## Verify

- [x] `pytest tests/` — 21 passed
- [x] mock 基线矩阵端到端：enss > no_pareto > random > fixed（管线验证）
- [x] 日志产物：history.jsonl（图 1/2/3 数据）、results.json、矩阵 CSV（表 1/2 数据）
- [ ] **真实 GSM8K 进化实验 —— 阻塞：需 A800 GPU 环境**（本机 CPU-only，torch 1.10 无法加载 Qwen2.5）

## Success Criteria 对照（phase14_plan.md）

1. Real LLM backend runs — 代码完成，待 A800 首跑
2. GSM8K real evaluation works — 管线完成（脚本化后端测试通过），待真实运行
3. ENSS completes multiple generations — mock 已验证，真实待跑
4. Baselines implemented — 完成
5. First paper-quality result table — 表格生成器就绪，待真实数据填充

## Next

移交 A800 环境执行 runbook；或等待 Planner 指示 Phase-15。
