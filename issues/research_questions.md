# Research Questions for Planner

## Q1. Mock evaluator 信号过强（Phase-12, 2026-09-03）— 已由 Phase-13/14 解决

Mock 仅保留为 CI；真实信号已切换 GSM8K。

## Q2. 搜索空间与种群规模 — 已由 Phase-13/14 解决

空间已扩至 64 架构；Phase-14 实验 pop=16/32、gen=10/20。

## Q3. 【重要】真实 benchmark 下，memory/compression substrate 不影响 capability（Phase-14, 2026-09-15）

现象：当前 GSM8K 真实评测链路中，LLM 生成只受 `genome.reasoning` 影响
（通过 prompt 模板：direct/verify/planner/cot）。memory（mamba/attention/retrieval/hybrid）
与 compression（none/lora/qlora/int8）对应的 nn.Module 是占位结构，其前向结果
不进入 LLM 的 prompt 或推理过程。因此：

- capability 只能区分 4 种 reasoning 变体，无法区分 memory/compression
- efficiency 是参数量代理（压缩有区分度），adaptability 是长题子集准确率
- 风险：论文若声称"进化发现更优记忆基底"，当前实验设计支撑不了

可能方向（待 Planner 决策，Executor 不自行改设计）：
a) 让 memory substrate 真实参与：如 retrieval 模块真的检索上下文注入 prompt；
   mamba/attention 作为工作记忆压缩对话历史
b) 把 capability 定义扩到多轮 agent 任务（AgentBench），memory 在多轮中自然起作用
c) 接受当前设计，论文贡献聚焦 reasoning×compression 的进化 + 效率权衡，
   memory 留作 future work

## Q4. 评估成本与吞吐（Phase-14, 2026-09-15）

单 prompt 逐条生成 ~6.7s/题，全量矩阵（6 方法 × 640 个体 × 200 题）约 200+ 小时/方法，
不可行。已加批处理（batch=32，提速约 20-40×）+ 原子评估缓存（断点续跑）。
中规模配置（limit=100, pop=16, gen=10）每方法约 1.5-2h。
全规模（pop=32, gen=20, 全量 1319 题）仍需 Planner 权衡 budget。
