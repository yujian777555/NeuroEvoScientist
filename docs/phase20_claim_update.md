# Phase-20 Claim Update（2026-09-23）

依据 Phase-20 结构化空间 + holdout 配对统计更新 `docs/claim_audit.md` 相关条目。
C3/C5 未重开。

## C2（任务条件化架构偏好）—— 重新分级为两个子 claim

### C2a 任务条件化选择（搜索侧分布差异）—— **supported（强）**
- 三任务在结构化空间中收敛到截然不同的基因组合，PubMedQA 三 seed 完全一致
- QASPER 预注册预测（retrieval 成为最优记忆基因）命中
- 证据：results/phase20_selection_lock.json + dev 搜索结果

### C2b 自有任务配置 holdout 占优 —— **partially supported（仅 GSM8K）**
- GSM8K：A_gsm 大幅优于一切（+29~71pp，p≈0），含成本维度
- PubMedQA/QASPER：自有配置在 holdout 上**输给** GSM8K 配置（显著）
- 措辞红线：不得声称"任务特定配置在其任务上更优"作为普遍结论；
  只能说"搜索选择的架构因任务而异，且该选择在 GSM8K 上带来大幅优势"

## 新发现（可入论文）

- **N1**：记忆贡献随骨干规模放大（GSM8K no_memory 差距 1.5B 0pp → 7B −12.6pp）
- **N2**：QASPER 上检索+exemplar 策略在 7B 上不迁移（崩溃），长上下文任务存在
  强骨干依赖
- **N3**：dev 区间搜索出的偏好不等于 holdout 泛化优势（小样本过拟合警告）

## 对 narrower-paper 定位的影响

维持不变：任务条件化认知协同设计 + 多目标审计 + 负结果。C2b 的复杂化
（GSM8K-only 成立）写入 limitation 与讨论。
