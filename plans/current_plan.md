# Phase 17 — Current Sprint Plan (Focused experiment running)

依据 `plans/phase17_plan.md` 执行。

## Goal

让每个基因名对应真实机制，然后回答：真实可训练 Mamba/SSM 记忆基底 + 适应 + 继承是否改善 capability-efficiency Pareto 前沿。

## Tasks

- [x] Task 1 schema 修正（48 架构；lora/qlora 命名清除；旧结果标记 legacy-schema）
- [x] Task 2 真实 Mamba-2（transformers Mamba2Model；顺序/状态/梯度/state_dict 测试 VM 全过；无静默代理）
- [x] Task 3 固定预算适应 + 继承语义修正（继承 = 父代适应后权重；pre/post loss 记录）
- [x] Task 4 原始目标持久化（history.jsonl population 记录）
- [ ] Task 5 聚焦 GSM8K 实验（15 运行进行中：enss/no_inherit/no_mamba2/random × seeds 0-2 + 3 固定基线）
- [ ] Task 6 双基准重跑（等 Task 5 门禁通过）
- [ ] deliverables：results/phase17_* 三件套、docs/phase17_results.md、docs/claim_audit.md

## 泄漏纪律（Phase-17 门禁）

经验银行仅来自 train split；测试项永不入库；PubMedQA 校准/评估切片不相交。

## Verification gates 对照

- [x] 占位 nn.Linear 不再叫 Mamba
- [x] 真实 Mamba-2 通过顺序/状态/梯度测试
- [x] context policy 不再误标 LoRA/QLoRA/INT8
- [x] 无 train/test 泄漏
- [x] 继承比较使用等适应预算
- [x] 原始 Pareto 目标持久化
- [ ] 3-seed 聚焦实验完成
- [ ] claim_audit.md

## Next

cron 监控 → 汇总 → 结果文档 + claim 审计 → 汇报 Planner。
