# Changelog

## [Phase-16] Task-conditioned validation infrastructure - 2026-09-15

### Added
- `src/scripts/validate_mamba.py` — Task 4 验证：mamba 记忆状态更新可追踪、四种记忆基因计算路径确实不同，产物 `results/mamba_trace.json`
- `src/scripts/aggregate_phase16.py` — 聚合 experiments/ 日志生成论文产物：`results/phase16_matrix.csv`（跨 seed 均值±方差）、`evolution_history.json`、`best_architectures.json`，附 ENSS-vs-Random 判定
- `tests/test_phase16.py` — no_memory 消融、延迟/token 记录、缓存键隔离
- `scripts_vm/p16_*.sh` — 5 卡多 seed 队列脚本

### Changed
- `src/evaluator/gsm8k.py` / `pubmedqa.py` — `disable_memory` 消融开关（w/o Memory Substrate）；每次评估记录 `latency_sec` 与 `prompt_tokens_total`；缓存键纳入消融标志
- `src/scripts/run_experiment.py` — 新增 `no_memory` 方法；矩阵扩至 8 方法；评估缓存改为按 method+benchmark 共享（跨 seed 复用，队列内串行无竞争）

### Test Results
- `pytest tests/` — 38 passed
- `validate_mamba.py` — MAMBA_VALIDATION_OK（state 逐步更新可追踪，四基因召回路径互不相同）
- 22 个 GPU 运行已在 5 卡启动（seeds 1-2 × 4 方法 × 2 基准 + no_memory 全 seed）

## [Phase-15] Substrate-activated dual-benchmark results - 2026-09-15

### Added
- `docs/phase15_results.md` — 双基准真实结果：Table 1/2（GSM8K + PubMedQA 全矩阵）、
  进化曲线、四条成功判据逐项对照、三个新问题（P1/P2/P3）移交 Planner
- `experiments/*_{gsm8k,pubmedqa}_seed0/` — 原始日志（gitignored），评估缓存支持断点续跑

### Results（真实 A800 × 5，Qwen2.5-1.5B-Instruct，limit=100, pop=16, gen=10, seed=0）
- 成功判据 1（任务依赖架构）：成立——GSM8K 进化出 Mamba+Verify+LoRA，
  PubMedQA 进化出 Mamba+Planner+QLoRA
- 成功判据 2（memory 基因影响真实计算）：成立（情景记忆注入 + 测试证据）
- 成功判据 3（进化优势超越 prompt 模板）：未成立——no_inherit 在 GSM8K 反超 ENSS
  （0.6488 vs 0.6039），random 在 PubMedQA 反超（0.5025 vs 0.4719）
- 成功判据 4（支撑 substrate evolution claim）：部分——搜索 vs 固定设计 capability
  差距 2.5×（0.60-0.64 vs 0.18-0.25），但进化 vs 随机无稳定优势
- 中途事件：另一租户抢占 30939:0，enss 迁移 30108:2 缓存续跑无损失

## [Phase-15] Neural substrate activation - 2026-09-15

### Added
- `src/evaluator/memory.py` — 真实情景记忆基底：attention=近因窗口、retrieval=TF-IDF 相似度 top-k、mamba=SSM 门控召回（MambaMemory 模块维护循环状态）、hybrid=检索+近因；compression 基因控制 exemplar 上下文预算（none 全文 / lora 截断 / qlora·int8 仅答案）
- `src/evaluator/pubmedqa.py` — PubMedQA（pqa_labeled 1000 题，yes/no/maybe）评估器：同样的激活基底管线 + 原子缓存
- `tests/test_memory.py`、`tests/test_pubmedqa.py`、`tests/fixtures/` 新夹具 — 含关键测试 `test_memory_gene_changes_prompt_content`：不同 memory 基因必须产生不同 prompt（基因组激活的真实性证明）
- `scripts_vm/queue_method.sh`、`queue_fixed.sh` — 双基准队列脚本

### Changed
- `src/evaluator/gsm8k.py` — 接入情景记忆（gold 历史前瞻构建，保持批处理有效）；prompt = memory exemplars + reasoning 模板；真实 token 成本计量；缓存键升级 `substrate-activated-v2`（Phase-14 缓存作废，prompt 语义已变）
- `src/evaluator/metrics.py` — efficiency 融合参数量代理 + 实测 prompt token 成本（压缩/记忆基因因此影响真实推理成本）
- `src/scripts/run_experiment.py` — 支持 `--benchmark pubmedqa`
- `scripts_vm/run_method.sh` — 增加 benchmark 参数

### Test Results
- `python -m pytest tests/` — 34 passed（本地与 VM 一致）
- GPU 冒烟（30939:1, Qwen2.5-1.5B, gsm8k limit=20）：Retrieval + CoT + None 0.4892 —— 与 Phase-14 最优不同，证明基因激活生效
- 固定基线已完成（真实推理）：gsm8k attention 0.3199 / mamba 0.3724 / hybrid 0.2568；pubmedqa 0.3801 / 0.4151 / 0.3662

## [Phase-14] Real GSM8K matrix results - 2026-09-15

### Added
- `docs/phase14_results.md` — 首份真实实验结果：Table 1 基线矩阵、Table 2 消融、Figure 1 进化曲线数据、关键发现与诚实声明
- `experiments/*_gsm8k_seed0/` — 原始日志（gitignored）：history.jsonl / results.json / 评估缓存

### Results（真实 A800 + Qwen2.5-1.5B-Instruct，GSM8K limit=100, pop=16, gen=10, seed=0）
- ENSS 最优：Mamba + CoT + INT8，fitness 0.5205（capability 0.39 / efficiency 0.88 / adaptability 0.30）
- 固定基线 capability 仅 0.11（Direct）vs 搜索架构 0.39–0.41（CoT/Planner）——最核心信号
- ENSS 第 2 代找到全局最优，第 5 代种群完全收敛（mean=best=0.520）
- ENSS = random = no_pareto 最优 fitness 相同（64 空间太小，进化优势未显现）
- w/o Mamba → Retrieval+Planner+INT8（capability 0.41 更高、总 fitness 更低，多目标权衡生效）
- 详细分析与局限声明见 docs/phase14_results.md 与 issues/research_questions.md（Q3/Q4）

## [Phase-14] Real GSM8K GPU experiment launched - 2026-09-15

### Added
- `src/evaluator/backends.py` — 批处理生成 `batch_generate`（left-padding，吞吐 ~20-40×）；transformers>=5 `dtype` 参数兼容；`batch_size` 可配
- `src/evaluator/gsm8k.py` — 原子评估缓存（tmp+fsync+os.replace，按 genome+model+limit 键控），崩溃可断点续跑
- `scripts_vm/smoke.sh`、`scripts_vm/run_method.sh`、`scripts_vm/queue_30522.sh` — VM 运行脚本（HF mirror、单卡钉扎、绝对路径）
- `tests/test_gsm8k.py::test_eval_cache_hit_skips_backend` — 缓存命中跳过后端

### Changed
- `src/scripts/run_experiment.py` — `--device` / `--batch-size` 参数；评估缓存按 method+seed 分文件（矩阵并行防竞争）
- `data/gsm8k/test.jsonl` — GSM8K 官方测试集 1319 题（本地缓存，已同步 VM）

### Experiment Results (real GPU, A800)
- 冒烟（30939 cuda:1, Qwen2.5-1.5B-Instruct, limit=20, pop=8, gen=3）：端到端跑通，
  best = Retrieval + CoT + INT8，真实 capability = 0.45（20 题子集）
- 基线矩阵（limit=100, pop=16, gen=10, batch=32）已在 5 张空闲 A800 上并行启动：
  random@30939:1 / no_pareto@30939:3 / enss@30108:1 / no_inherit@30108:2 /
  fixed×3+no_mamba@30522:3（遵守 1 worker/物理卡纪律，启动前 nvidia-smi 实测）
- 发现并记录研究问题 Q3：真实链路中仅 reasoning 影响 LLM 输出（见 issues/）

### Environment
- VM: 10.10.24.107 容器群，共享 GPFS `/202532803004`，python=`conda_envs/amber`
  （torch 2.5.1+cu121, transformers 5.7.0），模型经 hf-mirror 缓存 2.9G

## [Phase-14] Real experiment infrastructure - 2026-09-15

### Added
- `src/evaluator/backends.py` — 真实 LLM 推理后端：`QwenBackend`（默认 Qwen/Qwen2.5-1.5B-Instruct，自动 chat template + device_map="auto"）与通用 `HFTransformersBackend`（惰性加载、bf16/fp16 自动 dtype）；gsm8k.py 保留兼容 re-export
- `src/evolution/random_search.py` — 随机搜索基线（"w/o Evolution"），同等评估预算
- `src/evaluator/experiment_logger.py` — 实验日志：每代 `history.jsonl`（best/mean fitness、Pareto 前沿、架构分布 = Figure 1/2/3 数据）+ `results.json`（Table 1/2 数据）
- `src/scripts/run_experiment.py` — Phase-14 实验入口：6 种方法（3 固定架构基线 + random + no_pareto + enss）+ 消融（no_inherit / no_mamba）+ `--matrix` 一键矩阵 + CSV 结果表
- `requirements-a800.txt`、`docs/phase14_a800_runbook.md` — A800 环境与复现手册
- `tests/test_experiment.py` — 4 项测试（随机基线、no_pareto 消融、no_mamba 排除、日志器输出）

### Changed
- `src/evolution/controller.py` — 新增 `use_pareto` 开关：False 时退化为标量 fitness 锦标赛 + 截断选择（"w/o NSGA Pareto" 消融）
- `src/genome/search_space.py` — 支持 `exclude` 消融过滤（如排除 mamba）
- `src/evaluator/gsm8k.py` — HFTransformersBackend 迁移至 backends.py，本地保留 re-export

### Test Results
- `python -m pytest tests/` — 21 passed
- mock 基线矩阵（pop=8, gen=5, CPU）端到端跑通：enss 0.670 > no_pareto 0.662 > random 0.661 > fixed_mamba 0.545 > fixed_attention 0.467 > fixed_hybrid 0.457（仅管线验证，非论文结果）
- `run_enss.py` 回归正常；日志文件结构经测试校验
- 注：真实 LLM 后端未在真实模型上运行过（本机无 GPU），待 A800 首跑验证

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
