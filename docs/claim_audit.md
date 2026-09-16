# Claim Audit（Phase-17 收官，2026-09-17）

按 `plans/phase17_plan.md` 的 Paper-claim rules 逐条审计。
旧 Phase-14/15/16 结果一律视为 legacy-schema，仅供审计，不作论文证据。

## 论文级 claim 审计表

| # | Claim | 状态 | 证据/说明 |
|---|---|---|---|
| C1 | 进化搜索能发现显著优于人工固定设计的 agent 架构 | **supported** | Phase-16 表 1/2（capability 2.5×）；Phase-17 表 1（0.62 vs 0.24-0.26）`results/phase16_matrix.csv`、`results/phase17_focused_matrix.csv` |
| C2 | 不同任务进化出不同认知架构（任务条件化） | **supported**（legacy-schema 下）| Phase-16：GSM8K→Verify/CoT+LoRA，PubMedQA→Planner+INT8/QLoRA，3 seed 稳定。注意：Phase-17 只跑了 GSM8K；**Task 6 双基准重跑后此 claim 才在新 schema 下成立** |
| C3 | ENSS 优于等预算随机搜索 | **partially supported** | Phase-16：GSM8K 0.6012 vs 0.5876（3 seed）✅，PubMedQA 微弱 ✅；Phase-17：GSM8K 0.6811 vs 0.6829 基本打平。结论不一致，需更多 seed/更大空间 |
| C4 | memory substrate 对 capability 有真实贡献 | **supported** | Phase-16 no_memory 消融：GSM8K -29%、PubMedQA -23% capability |
| C5 | 真实 Mamba/SSM 记忆基底提升性能 | **unsupported（不实 claim，禁止）** | Phase-17：Mamba2 候选 mean cap 0.49 < recency 0.62；进化未选择它。实现是真实的（可训练、顺序敏感、梯度通），但无性能优势证据 |
| C6 | 权重继承改善 ENSS | **partially supported（方向转正，弱证据）** | Phase-17 继承 vs 全新（等预算）：cap 0.535 vs 0.489，post-loss 0.621 vs 0.738，但 n=2。Phase-16（未训练基底）为负。当前只能声称"基底可训练时继承不再有害，且有适应效率改善的迹象" |
| C7 | LoRA/QLoRA 压缩提升效率 | **unsupported（已从方法中移除该语义）** | Phase-14-16 误标；Phase-17 起 context_policy 才是上下文预算基因 |
| C8 | "neural architecture self-evolution" | **partially supported** | 基底层现在有真实可训练神经组件参与进化；但 backbone 冻结、reasoning 仍是 prompt 级。措辞应精确为"agent 认知架构（记忆基底+推理策略+上下文策略）的进化搜索" |

## Phase-17 门禁状态

全部通过（见 docs/phase17_results.md 末尾清单）。

## 下一步建议（等 Planner）

1. Task 6：修正 schema 下重跑 GSM8K + PubMedQA 双基准（解锁 C2 在新 schema 下成立）
2. C3 需要更强分离设计：更大空间或更难基准
3. C5 按 stop condition 封存，不强行投入
