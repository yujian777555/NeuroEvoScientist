# Related Work and Novelty Positioning（Phase-19 迁移版）

## 1. Evolutionary Discovery with LLMs (AlphaEvolve et al.)

AlphaEvolve 类工作通过 LLM 提议 + 自动评估 + 迭代选择进化可执行程序。
我们借用"进化循环"范式，但搜索对象不同：不是程序或模型权重，而是
LLM agent 的认知配置（记忆策略、推理策略、上下文策略）。

## 2. Neural Architecture Search

传统 NAS 优化静态网络结构。本文不搜索骨干网络结构（骨干冻结），
而是搜索骨干之上的 agent 认知架构——这是与 NAS 的边界，
论文措辞不得混淆（无 "full neural architecture self-evolution"）。

## 3. Agent Architecture / Workflow Search

现有 agent 搜索多优化多智能体拓扑或工作流。我们搜索的是**单个 agent
内部**的记忆-推理-上下文组合，并在多目标（能力-成本）下刻画整个
48 点格局（穷举 landscape oracle）。

## 4. State Space Models / Mamba

Mamba/Mamba-2 是高效长序列建模组件。本文搜索空间中包含一个真实可训练的
Mamba-2 记忆基底；在我们的协议下进化搜索更偏好更简单的 recency/hybrid
记忆——我们如实报告这一负结果，不声称 Mamba 带来收益。

## 5. Memory-Augmented / Retrieval-Augmented Agents

情景记忆与检索增强是 agent 设计的常见组件。我们的贡献不在于提出新的
记忆机制，而在于**在统一搜索空间中实证刻画记忆/推理/上下文选择的
任务依赖性**（含 holdout 与跨骨干转移验证）。

## Novelty Statement（限定版）

据我们所知，本文是首个对 LLM agent 认知架构（记忆×推理×上下文策略）
进行**冻结协议、泄漏安全、多目标、含负结果审计**的协同设计实证研究。
（不使用未经证实的 "first" 措辞；此句仅作定位陈述。）
