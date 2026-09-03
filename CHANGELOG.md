# Changelog

## [Phase-12] MVP Evolution Loop - 2026-09-03

### Added
- `src/genome/search_space.py` — SearchSpace 类：加载 `configs/search_space.yaml`，枚举 8 种架构组合，随机采样（PyYAML 缺失时回退内置配置）
- `src/genome/__init__.py`、`src/models/__init__.py`、`src/evolution/__init__.py`、`src/evaluator/__init__.py`
- `src/evaluator/benchmark.py` — MockEvaluator（确定性伪任务打分）+ benchmark 注册接口，预留 GSM8K / AgentBench / PubMedQA 挂点
- `src/evaluator/metrics.py` — capability / efficiency / adaptability 三目标计算
- `src/scripts/run_enss.py` — 入口脚本：逐代输出最优 Agent + Fitness（含种群均值），末代输出 Best Agent
- `plans/current_plan.md`、`status.json`、`requirements.txt`、`issues/research_questions.md`

### Changed
- `src/genome/architecture.py` — reasoning 默认值对齐搜索空间（direct）；新增 `describe()` 输出如 "Mamba + Verify + LoRA"
- `src/models/hybrid_agent.py` — 按 genome 组装 agent：mamba/attention 记忆、direct/verify 推理、none/lora 压缩（CPU 轻量占位实现）
- `src/evolution/mutation.py` — 变异空间收敛到配置文件定义的 3 模块（移除 retrieval/hybrid/moe/tree_search/int8）
- `src/evolution/crossover.py` — 模块级均匀交叉（保留 GenomeCrossover 兼容包装）
- `src/evolution/controller.py` — 完整进化循环：评估 → fitness → 锦标赛选择 → 交叉/变异（mutation_rate=0.3）→ 精英保留（elite=2）
- `src/evolution/fitness.py` — 支持可配置权重的标量化（0.5/0.3/0.2）

### Test Results
- `python src/scripts/run_enss.py`（CPU, Python 3.9, torch 1.10）：10 代 × 16 个体一次跑通
- 收敛结果：Best Agent = Mamba + Verify + LoRA，fitness 0.60（capability=0.66, efficiency=0.56, adaptability=0.49）
- 种群均值 0.56 → 0.58，呈收敛趋势
- 确定性校验：相同 seed 两次运行输出逐字节一致；seed=7 亦收敛到同一最优架构
