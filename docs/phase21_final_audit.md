# Phase-21 Final Audit（终版 claim lock，2026-09-24）

依据 `plans/phase21_plan.md` Task 5 锁定。仅 Phase-17–21 修正语义证据。

## Core claims（允许）

| # | Claim | 状态 | 证据 |
|---|---|---|---|
| 1 | 认知架构选择实质改变能力-成本行为 | **supported** | GSM8K holdout +29.0/+16.7pp vs 最强固定基线（`results/phase20_statistics.json`）；成本维度 token 计数 |
| 2 | 自动结构化协同设计可发现强配置 | **supported** | 同上；GSM8K 相对固定基线大幅优势 |
| 3 | 搜索侧架构偏好因任务而异（C2a） | **supported** | 三任务 distinct 收敛，PubMedQA 3/3 seed 一致，QASPER 预注册命中（`results/phase20_selection_lock.json`） |
| 4 | 任务/骨干交互显著，须显式评估 | **supported** | QASPER-7B 提取失配诊断（`docs/phase21_qasper7b_diagnostic.md`）；记忆消融随骨干放大 |
| 5 | 泄漏安全、可审计的架构搜索协议 | **supported** | 预注册锁定、逐题预测、配对统计、claim 审计链 |

## Limited / closed claims

| # | Claim | 状态 |
|---|---|---|
| C2b 自有任务普遍占优 | **unsupported**（仅 GSM8K 成立） |
| ENSS > 随机搜索 | **closed**（Phase-18 决定性，未重开） |
| Mamba 提升性能 | **closed**（真实实现、未被选中） |
| 记忆普遍受益 | **limited**：仅同基因受控消融处主张（GSM8K-7B +12.6pp、PubMedQA-1.5B +18.0pp；QASPER 微弱） |
| 全主干神经架构自进化 | **not allowed** |
| QASPER-7B"骨干依赖" | **修正为 backbone–prompt/extraction interaction**（诊断证据） |

## Phase-21 各任务状态

- [x] Task 1 任务感知表型规范化（实现 + 测试 79 全过；敏感度重跑完成，
  **C2a 稳健**：PubMedQA 逐基因一致、GSM8K 同族，见 docs/phase21_sensitivity.md）
- [x] Task 2 记忆消融解释修正（文档 + 受控消融数据：PubMedQA +18.0pp, QASPER +1.5pp）
- [x] Task 3 QASPER-7B 诊断（提取/格式失配，含 raw output 证据）
- [x] Task 4 机制案例补全（14 案例，含 QASPER 双骨干配对失效）
- [x] Task 5 本锁定
- [x] Task 6 manuscript v2 + abstract_v2 + limitations + tables + figures data
