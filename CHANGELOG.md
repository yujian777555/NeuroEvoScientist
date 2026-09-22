# Changelog

## [Phase-20] structured genome + QASPER + main matrix launch - 2026-09-22

### Added
- `src/genome/structured.py` — 结构化基因组：条件子基因、规范化去重、确定性 phenotype hash
- `src/genome/structured_space.py`、`configs/phase20_structured_search_space.yaml`、`configs/phase20_protocol.yaml`
- `src/evolution/structured_operators.py` — 局部邻域变异（80%）+ 语义块交叉 + 规范化
- `src/evaluator/qasper.py` — 第三任务 QASPER（长上下文证据整合，LongBench 官方词级 F1），预注册划分 dev[0:50]/holdout[50:150]/calibration[150:200]
- `src/evaluator/prompts.py` — 推理基因模板引擎（depth/verifier_passes 真实生效）
- `src/scripts/run_structured_search.py`、`scripts_vm/p20_*.sh`
- `docs/phase20_third_task_preregistration.md` — 第三任务预注册（GPU 运行前冻结）
- `tests/test_phase20.py`、`tests/test_qasper.py` — 条件有效性/规范化/去重/局部性/管线/回归测试

### Changed
- `src/evaluator/memory.py` — retrieval 支持 dense 度量；hybrid 支持 retrieval_fraction；format_exemplar 支持 token_budget
- `src/evaluator/gsm8k.py`/`pubmedqa.py` — exemplar_count 覆盖、token_budget 透传、推理模板走 prompts 引擎
- `src/evolution/controller.py`/`random_search.py` — 可插拔算子 + 逐基因适应预算
- 修复：QASPER 原始行缺 question/answer 键导致适应崩溃（calibration 规范化 + 回归测试）

### Test Results
- VM 77 passed（本地 66 passed + 11 mamba2 skip）
- GPU 小规模验证：structured enss GSM8K dev cap 0.60，结构化基因全生效

## [Phase-19] paper lock + holdout robustness + cross-backbone transfer - 2026-09-17

### Phase-19a（锁定，先于 holdout 推理）
- `configs/phase19_protocol.yaml`、`results/phase19_selection_lock.json`（10 配置锁定）
- 评估器新增 start/limit 区间 + 逐题预测日志；不相交测试（`tests/test_phase19.py`）
- `src/scripts/phase19_holdout.py` holdout 运行器（done-skip + 缓存续跑）

### Phase-19b（结果）
- 40 个 holdout 运行完成（10 配置 × 2 基准 × 2 骨干）；32380 行逐题预测
- `src/scripts/phase19_statistics.py`（bootstrap 10000 + McNemar）、
  `phase19_rebuild_predictions.py`（从缓存 item_scores 重建，含 model/config 字段）
- 产物：`phase19_holdout_results.csv`、`phase19_item_predictions.jsonl`、
  `phase19_statistics.json`、`phase19_cross_task_matrix.csv`、`phase19_backbone_transfer.csv`
- 结论：C1 GSM8K 大幅成立（+33.8pp, p≈0）；C2 降级（方向一致但统计不显著，
  成本维度占优）；C4 成立且随骨干增强；任务偏好方向可转移至 7B

### Phase-19c（论文迁移）
- paper/ 七文件重写为修正语义；新增 `manuscript_v1.md`、`abstract_v1.md`、
  `title_candidates.md`；`docs/claim_audit.md` 终版；`docs/phase19_results.md`
- 事故记录：holdout runner 缺 import 崩溃→修复+缓存续跑零损失；
  预测文件缺 model 列→从缓存重建（未重跑推理）

## [Phase-18] corrected dual-benchmark replication and search-efficiency audit (final) - 2026-09-17

### Added（结果收官）
- `results/phase18_dual_benchmark.csv`、`phase18_search_efficiency.csv(+curves.json)`、`phase18_pareto_fronts.json`、`phase18_architecture_distribution.json`、`phase18_inheritance_pairs.{csv,json}`
- `paper/phase18_tables.md`、`paper/phase18_figures_data.json`
- `src/scripts/aggregate_phase18.py`、`docs/phase18_results.md`、终版 `docs/claim_audit.md`

### Results（全部判据终判）
- C1 supported（GSM8K cap 2.5×；PubMedQA 以 fitness/效率成立，fixed_mamba2 capability 反超如实记录）
- C2 supported（修正 schema 下跨 3 seed 稳定的任务依赖基因分布）
- C3 **unsupported**（oracle 审计：ENSS 与随机在全部预算/基准上打平，差 <0.01；搜索优越性措辞已移除）
- C4 supported（no_memory 消融 cap -34%/-17%）
- C5 unsupported（Mamba 负结果保留）
- C6 partially supported → 附录效率机制（n=20 配对：loss 20/20 改善，capability 0/20 无差异）
- C7 supported（真实 token 计数）
- C8 partial（限定措辞：冻结主干上的认知架构协同进化设计）

### Fixed
- 搜索审计策略停滞死循环（enss_policy 交配池耗尽空转 → 停滞踢脚 + 硬迭代上限）

## [Phase-18] corrected dual-benchmark replication and search-efficiency audit (infra) - 2026-09-17

### Added
- `configs/phase18_eval.yaml`、`configs/phase18_search_efficiency.yaml` — 冻结的审计配置
- `src/scripts/inheritance_study.py` — Task 4 配对继承研究（20 对、等预算、pre/post loss+capability+wall-clock）
- `src/scripts/analyze_search_efficiency.py` — Task 3 在线 oracle 审计：ENSS vs random 在预算 {12,24,36,48} × 20 seed 下的 best-capability 曲线、2D Pareto hypervolume、regret、ε-Pareto 命中、达标评估数、AUC
- `run_experiment.py --landscape` — Task 2 全 48 架构穷举评估（原子 JSONL、断点续跑）
- `tests/test_phase18.py` — hypervolume 正确性、oracle 在线约束、策略确定性
- `scripts_vm/p18_*.sh` — landscape/队列/杂项/继承脚本
- `fixed_hybrid` 基线加入 FIXED_BASELINES

### Fixed
- 继承研究父/子 substrate 维度不一致（state_size 16 vs 64）
- tar|ssh 同步与 nohup 启动合并导致静默丢任务（第三次同类事故；已立规矩：必须分开）

### Test Results
- 本地 47 passed / 11 skipped（mamba2 系在 VM 覆盖）

## [Phase-17] correct substrate semantics and validate real Mamba adaptation - 2026-09-17

### Added
- `src/scripts/aggregate_phase17.py` — 聚焦矩阵 / 继承曲线 / 逐代 Pareto 前沿聚合
- `results/phase17_focused_matrix.csv`、`phase17_inheritance_curve.json`、`phase17_pareto.json`
- `docs/phase17_results.md`、`docs/claim_audit.md`（逐条 claim 审计：supported/partially/unsupported + 证据指针）
- 回归测试 `test_memory_state_cached_until_store_or_invalidate`

### Results（phase17 schema，GSM8K，3 seeds）
- ENSS 0.6811 / no_inherit 0.6811 / random 0.6829 / fixed 0.36–0.41；
  进化架构 capability 0.62 vs 固定 0.24–0.26（2.5×）
- 继承在基底可训练后转正：继承候选 cap 0.535 vs 0.489、post-loss 0.621 vs 0.738（n=2，弱证据）
- 真实 Mamba2 未被进化选中（候选 cap 0.49 < recency 0.62）——按计划 stop condition 如实封存该 claim
- 工程事故：Mamba2 记忆状态每查询重算前向导致 24h 空转；修复为按银行配置缓存 + 回归测试

### Verification gates（plans/phase17_plan.md）
全部通过：真实 Mamba2、无语义误标、无泄漏、等预算继承比较、原始目标持久化、3-seed 完成、claim 审计

## [Phase-17] Substrate semantics correction + real Mamba - 2026-09-16

### Added
- `configs/phase17_search_space.yaml` — 修正后 schema：memory{recency/retrieval/mamba2/hybrid} × reasoning{direct/cot/verify/planner} × context_policy{full/truncated/answer_only} × quantization{fp16} = 48 架构；lora/qlora 命名从上下文压缩行为中移除
- `configs/phase17_adaptation.yaml` — 候选适应协议：train split 48 样本、30 AdamW 步、固定 lr/seed、冻结主干
- `src/evolution/adaptation.py` — 固定预算基底适应（下一经验嵌入预测目标），记录 pre/post loss、耗时、可训练参数量
- `tests/test_mamba2_substrate.py` — 真实 Mamba2 测试：顺序敏感、状态敏感、梯度流、state_dict、与旧线性代理差异、无占位假冒
- `tests/test_phase16.py` 缓存指纹隔离测试；`tests/test_gsm8k.py` 泄漏纪律测试
- `scripts_vm/p17_queue.sh` — 聚焦实验队列

### Changed（语义修正，breaking）
- `src/genome/architecture.py` / `search_space.py` — Phase-17 schema；旧 8/64 架构结果标记 legacy-schema 仅供审计
- `src/models/mamba_memory.py` — **真实 Mamba-2**（transformers Mamba2Model，维护中的实现）；不再静默回退占位
- `src/models/builder.py` — SubstrateAgent：候选的神经组件 = 可训练记忆基底
- `src/evaluator/memory.py` — 控制器重写：bank 仅来自 train split（**修复 Phase-15/16 的 test-gold 泄漏**）；mamba2 控制器用真实基底计算 order-dependent 记忆状态
- `src/evaluator/gsm8k.py` / `pubmedqa.py` — context_policy 基因名、可注入已适应控制器、substrate_fingerprint 缓存隔离、calibration split 接口
- `src/evolution/controller.py` — 继承改为转移**适应后**基底权重（同 memory 基因才继承）；确定性 per-genome 初始化；适应记录进 metrics
- `src/evolution/random_search.py` — 随机基线同等适应预算（公平比较）
- `src/evaluator/experiment_logger.py` — 逐代持久化全部个体的原始目标值（Pareto 分析不再依赖标量 fitness）
- `src/scripts/validate_mamba.py` — 新 schema 版 Mamba 验证（VM 上 MAMBA_VALIDATION_OK）

### Test Results
- 本地 43 passed + 10 skipped（mamba2 需 VM）；VM 53 passed / 0 skipped
- GPU 冒烟：适应协议生效（pre_loss 1.00 → post 0.74，30 步 0.5s，2.29M 基底参数）

## [Phase-16] Task-conditioned evolution validation - 2026-09-16

### Added
- `docs/phase16_results.md` — 多 seed 验证结果：双基准矩阵表（3 seed 均值±std）、
  四条成功判据对照、Mamba 验证结论、遗留问题 P1/P3
- `results/phase16_matrix.csv`、`results/evolution_history.json`、
  `results/best_architectures.json`、`results/mamba_trace.json` — 论文产物
- `experiments/*_seed{1,2}` + `no_memory_*_seed0` — 22 个新运行的原始日志

### Results（A800 × 5，Qwen2.5-1.5B，3 seeds × 2 benchmarks，pop=16, gen=10, limit=100）
- ENSS > Random：双基准成立（GSM8K 0.6012±0.010 vs 0.5876±0.004；PubMedQA 0.4814 vs 0.4800 且 capability 0.57 vs 0.50）
- ENSS >> Fixed：fitness ≈2×、capability ≈2.5×
- 任务依赖架构跨 seed 稳定：GSM8K→Verify/CoT+LoRA，PubMedQA→Planner+INT8/QLoRA
- 记忆基底真实贡献：no_memory capability 降 23–29%；token 成本权衡可见
- 事故记录：enss 队列因 HF hub 连接超时中断一次，HF_HUB_OFFLINE=1 修复 + 缓存续跑无数据损失
- 遗留：P1（no_inherit 仍反超 ENSS，0.6341 vs 0.6012）、P3（PubMedQA 绝对值低）移交 Planner

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
