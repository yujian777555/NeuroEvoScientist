# Changelog

## [Phase-13] ENSS Upgrade - 2026-09-03

### Added
- `src/evaluator/gsm8k.py` — 真实 GSM8K benchmark 接口：JSONL 加载（显式路径 / 本地缓存 / datasets 库 / 官方镜像下载四级回退）、按 genome reasoning 模块条件化 prompt（direct/verify/planner/cot 四种模板）、数值答案抽取与匹配；无推理后端时明确拒绝打分（不伪造结果）；`HFTransformersBackend` 惰性加载真实模型
- `src/evolution/inheritance.py` — 权重继承：`inherit_state`（模块级兼容性 + 形状守卫）与 `build_child_with_inheritance`；接口为 Parent Genome + Parent State -> Child Genome + Inherited State
- `tests/` — 17 个 pytest 测试：NSGA 排序/前沿/多样性/环境选择、权重继承（全继承/部分继承/加载一致性/形状守卫）、GSM8K 管线（fixture + 脚本化后端）、搜索空间（64 组合、采样合法性、全架构可构建）

### Changed
- `configs/search_space.yaml` — 搜索空间 8 → 64 架构：memory +retrieval/hybrid，reasoning +planner/cot，compression +qlora/int8
- `src/models/hybrid_agent.py` — 新增 RetrievalMemory / HybridMemory / PlannerReasoning / CoTReasoning / Int8Wrapper；QLoRA 复用 LoRA（rank=4）；新增 `effective_parameters()` 压缩足迹代理
- `src/evolution/nsga3.py` — 重写为真正的多目标选择：快速非支配排序、拥挤度距离多样性保持、按前沿填充的环境选择、(rank, crowding) 二元锦标赛
- `src/evolution/controller.py` — 选择压力改为纯 Pareto 多目标（标量 fitness 仅用于日志）；集成权重继承（state bank，子代继承父代兼容张量）；精英通过 Pareto 生存保留
- `src/evaluator/benchmark.py` — gsm8k 注册为真实评估器（惰性导入）；MockEvaluator 标注 CI-only；Mock 先验扩展至 64 空间
- `src/evaluator/metrics.py` — efficiency 改用压缩调整后的有效参数量
- `src/genome/architecture.py` / `search_space.py` — 显示名与回退配置同步 64 空间
- `src/scripts/run_enss.py` — 支持 `--benchmark gsm8k --model <hf-model> --limit --data-path --no-inheritance`；输出继承张量计数

### Test Results
- `python -m pytest tests/` — 17 passed
- `python src/scripts/run_enss.py`（mock, CPU）：64 架构空间 10 代跑通，best fitness 0.65 → 0.67，收敛到 Mamba + CoT + QLoRA（efficiency 0.86 由 QLoRA 贡献，体现多目标权衡而非单一 capability 导向）
- 权重继承冒烟：跨代共转移 486 个张量
- 确定性校验：相同 seed 两次运行输出逐字节一致
- 注：GSM8K 真实推理路径已通过脚本化后端管线测试，但未在真实 LLM 上运行（本机无 GPU/模型）

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
