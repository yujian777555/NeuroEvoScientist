# Research Questions for Planner

## Q1. Mock evaluator 信号过强（Phase-12, 2026-09-03）

现象：MockEvaluator 的模块先验（verify +0.12 capability、mamba +0.08、lora +0.10 adaptability）
使 Mamba+Verify+LoRA 在 8 架构空间中成为绝对占优解，第 1 代即被采样到，之后 best fitness
无变化（0.60），只有种群均值上升（0.56→0.58）。

影响：MVP 闭环验证目标已达成；但若用于论文实验，该信号无法支撑任何架构层面的结论。

待 Planner 决策：
- Phase-13 是否直接接入 GSM8K（小模型 + 有限题目子集）作为首个真实信号？
- Mock 评估器是否保留为 CI 冒烟测试？（建议保留）

## Q2. 搜索空间与种群规模

8 架构空间下 population=16 意味着初始种群几乎必然覆盖最优组合，"搜索"压力有限。
扩大空间（retrieval/hybrid 记忆、moe 推理、int8 压缩等已在早期骨架中出现）还是保持
小空间先接真实 benchmark？按第一原则本阶段未扩大，等待指示。
