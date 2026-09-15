# Phase-16 Plan: Task-conditioned Evolution Validation

## Goal

验证 ENSS 是否真正能够根据任务自动发现不同的 Agent cognitive architecture。

Phase-15 已完成：
- real episodic memory substrate
- attention/retrieval/mamba/hybrid memory genes
- PubMedQA benchmark interface
- token-cost efficiency metrics

Phase-16 不增加新模块，重点产生论文核心证据。

---

# Research Question

RQ1:
ENSS 是否优于固定架构和随机搜索？

RQ2:
不同任务是否会进化出不同的 cognitive substrate？

RQ3:
memory substrate 是否真正贡献能力和效率？

---

# Task 1: Task-conditioned Evolution Experiment

Benchmark:

1. GSM8K
2. PubMedQA

Methods:

- Fixed Attention
- Fixed Mamba
- Fixed Hybrid
- Random Search
- Evolution without Pareto
- ENSS

统一实验配置，保存：

- best architecture
- generation history
- fitness curve
- token cost
- latency

---

# Task 2: Architecture Adaptation Analysis

重点分析：

GSM8K 最优架构是否偏向：

- reasoning
- verifier
- efficient memory

PubMedQA 最优架构是否偏向：

- retrieval
- long-context memory
- hybrid substrate

目标证明：

同一个 ENSS 框架可以产生 task-specific agent brain。

---

# Task 3: Ablation

必须完成：

## w/o Evolution

固定架构。

## w/o Pareto

单目标优化。

## w/o Memory Substrate

无 episodic memory。

## w/o Inheritance

无权重/状态继承。

---

# Task 4: Mamba Validation

检查：

Mamba memory 是否真正进入 inference path。

要求：

- state update 可追踪
- memory gene 改变计算路径
- 与 attention/retrieval 对比

---

# Success Criteria

Phase-16 成功标准：

1. ENSS > Random Search
2. ENSS > fixed baselines
3. GSM8K 与 PubMedQA 产生不同 evolved architectures
4. memory gene 对性能和成本产生真实影响

---

# Output

生成：

results/

- phase16_matrix.csv
- evolution_history.json
- best_architectures.json

更新：

- docs/phase16_results.md
- status.json

Commit:

[Phase-16] task-conditioned evolution validation
