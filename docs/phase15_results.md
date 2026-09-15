# Phase-15 Results: Neural Substrate Activation Experiments

日期：2026-09-15
环境：A800 80GB × 5 并行（1 worker/物理卡），Qwen2.5-1.5B-Instruct（fp16, greedy）
配置：population=16，generations=10，seed=0，limit=100/基准，batch=32
与 Phase-14 的本质区别：**每个基因真实影响推理**（memory 决定注入哪些历史经验、
compression 决定上下文预算/token 成本、reasoning 决定指令模板）。

## Table 1: GSM8K（真实推理，capability = 准确率）

| Method | Best Architecture | Fitness | Capability | Efficiency | Adaptability |
|---|---|---|---|---|---|
| no_inherit | Mamba + CoT + LoRA | **0.6488** | **0.64** | 0.694 | 0.603 |
| **ENSS (full)** | Mamba + Verify + LoRA | 0.6039 | 0.60 | 0.657 | 0.534 |
| Random | Mamba + Verify + LoRA | 0.5834 | 0.57 | 0.666 | 0.493 |
| no_pareto | Mamba + Verify + LoRA | 0.5811 | 0.57 | 0.658 | 0.493 |
| no_mamba | Retrieval + Verify + None | 0.5378 | 0.56 | 0.512 | 0.521 |
| Fixed Mamba | Mamba + Direct + None | 0.3432 | 0.25 | 0.727 | 0.000 |
| Fixed Attention | Attention + Direct + None | 0.3199 | 0.25 | 0.531 | 0.178 |
| Fixed Hybrid | Hybrid + Direct + None | 0.2568 | 0.18 | 0.465 | 0.137 |

## Table 2: PubMedQA（真实推理，yes/no/maybe）

| Method | Best Architecture | Fitness | Capability | Efficiency | Adaptability |
|---|---|---|---|---|---|
| Random | Mamba + Planner + INT8 | **0.5025** | 0.54 | 0.654 | 0.182 |
| no_inherit | Mamba + Planner + INT8 | 0.4904 | **0.56** | 0.641 | 0.091 |
| **ENSS (full)** | Mamba + Planner + QLoRA | 0.4719 | 0.55 | 0.656 | 0.000 |
| no_mamba | Retrieval + Planner + INT8 | 0.4682 | 0.55 | 0.583 | 0.091 |
| no_pareto | Retrieval + Planner + INT8 | 0.4682 | 0.55 | 0.583 | 0.091 |
| Fixed Mamba | Mamba + Direct + None | 0.4151 | 0.49 | 0.567 | 0.000 |
| Fixed Attention | Attention + Direct + None | 0.3801 | 0.50 | 0.434 | 0.000 |
| Fixed Hybrid | Hybrid + Direct + None | 0.3662 | 0.51 | 0.371 | 0.000 |

## 成功判据对照（phase15_plan.md）

1. **不同任务产生不同进化架构 —— 成立（弱证据）**：
   GSM8K → Mamba+Verify+LoRA；PubMedQA → Mamba+Planner+QLoRA（ENSS 最优）。
   reasoning 与 compression 基因因任务而异；memory 基因两任务都收敛到 Mamba。
2. **memory 基因影响真实计算 —— 成立**：情景记忆真实改变 prompt 内容
   （测试证明 + exemplar 注入推理流）。
3. **ENSS 优势不只来自 prompt 模板 —— 不成立/存疑**：
   GSM8K 上 no_inherit（0.6488）反超 full ENSS（0.6039）；PubMedQA 上
   random（0.5025）反超 ENSS（0.4719）。进化未展现对随机搜索的稳定优势。
4. **结果支撑 neural substrate evolution claim —— 部分支撑**：
   搜索 vs 固定设计的差距巨大且真实（GSM8K capability 0.60-0.64 vs 0.18-0.25，
   约 2.5×），且架构因任务而异；但"进化算法本身优于随机搜索"未获证据。

## Figure 1 数据（ENSS 进化曲线，best/mean fitness）

GSM8K：gen1 0.604/0.465 → gen5 0.604/**0.569**（峰值收敛）→ gen10 0.604/0.497
PubMedQA：gen1 0.464/0.405 → gen3 0.472/0.442（Planner 变体出现）→ gen10 0.472/0.456

注：mean 后期回落是 Pareto 多样性保持的正常现象（保留效率/适应度权衡个体）。

## 给 Planner 的问题（重要）

- **P1. 继承反超**：no_inherit 在 GSM8K 上 capability 0.64 vs ENSS 0.60。
  假设：占位基底权重未经训练，继承的"旧权重"在新架构上反而是噪声，
  拖累 episode 内记忆选择质量（mamba gate 为未训练权重）。
  选项：(a) 接受（基底未训练时继承本就无收益，如实写 limitation）；
  (b) 加入轻量基底微调再评（成本↑）；(c) 继承仅限同构模块（已是）。
- **P2. 进化≈随机**：64 空间对 160 次评估仍偏小；且单 seed。
  选项：(a) 扩空间（如 state_size、memory_k 基因化）；(b) 多 seed 跑方差；
  (c) 在更大任务集上做。
- **P3. PubMedQA 信号弱**：1.5B 模型 capability 0.49-0.56，接近 3 类随机水平
  （多数类基线约 0.5）。Adaptability（maybe 题）几乎全 0。
  选项：(a) 换更区分度的科学基准（如 MedQA/BioASQ）；(b) 换更强 backbone
  （受限于计划约束，暂缓）；(c) 接受并用 GSM8K 为主证据。

## 复现

`docs/phase14_a800_runbook.md` + `scripts_vm/queue_method.sh`（双基准队列）。
原始日志：`experiments/*_{gsm8k,pubmedqa}_seed0/`。
