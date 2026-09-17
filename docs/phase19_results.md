# Phase-19 Results: Held-Out Robustness + Cross-Backbone Transfer

日期：2026-09-17
协议：`configs/phase19_protocol.yaml` + `results/phase19_selection_lock.json`
（holdout 推理前锁定，commit 19c7c14）
数据：GSM8K test[100:1319]（1219 题，Phase-18 从未触碰）；PubMedQA samples[100:500]
（400 题，与校准段 [500:1000] 不相交）；骨干 Qwen2.5-1.5B / 7B-Instruct
产物：`results/phase19_holdout_results.csv`、`phase19_item_predictions.jsonl`（32380 行）、
`phase19_statistics.json`、`phase19_cross_task_matrix.csv`、`phase19_backbone_transfer.csv`

## 主结果（holdout capability，1.5B / 7B）

| 配置 | GSM8K 1.5B | GSM8K 7B | PubMedQA 1.5B | PubMedQA 7B |
|---|---|---|---|---|
| A_gsm (Hybrid+Verify+Truncated) | 0.5431 | 0.6965 | 0.5375 | 0.6775 |
| A_pubmed (Recency+Verify+Full) | 0.5316 | 0.6817 | 0.5375 | 0.7025 |
| 最强固定基线 | 0.2289 (recency) | 0.5488 (mamba2) | 0.5725 (retrieval) | 0.6025 (recency) |
| no_memory | 0.4487 | 0.5849 | 0.5100 | 0.6475 |
| pareto_gsm_cot | 0.5365 | **0.7408** | 0.3900 | 0.2850 |
| pareto_pub_planner | 0.4487 | 0.6940 | 0.5475 | 0.6150 |
| pareto_pub_mamba2 | 0.0878 | 0.1247 | **0.6175** | 0.4925 |

## 统计判定（配对 bootstrap 10000 次 + McNemar 精确检验）

### C1（自动发现 vs 固定基线）
- GSM8K：A_gsm vs fixed_mamba2 +33.8pp（1.5B）/ +14.8pp（7B），p≈0 —— **大幅成立**
- PubMedQA：1.5B 上 A_pubmed vs fixed_retrieval −3.5pp（n.s.，固定基线更高）；
  7B 上 +10.0pp（p≈0）——**任务/规模依赖，采用精确措辞，不得声称普遍能力优势**
- 补充：pareto_pub_mamba2 在 PubMedQA 1.5B holdout 达 0.6175（最高），
  佐证 landscape Pareto 前沿的多样性价值

### C2（任务条件化偏好）—— **partially supported（降级措辞）**
- 4/4 自有任务 vs 交叉任务比较方向一致为正，但效应小且个体不显著：
  GSM8K +1.15pp（p=0.46）/ +1.48pp（7B, p=0.25）；PubMedQA 0.00pp（1.5B 平局）/ +2.50pp（7B, p=0.22）
- **能力-成本权衡维度成立**：GSM8K holdout 上 A_gsm 以 41% 更少的 token
  （485k vs 823k）取得更高 capability（0.5431 vs 0.5316）——自有任务配置在
  Pareto 前沿上占优；PubMedQA 上同 capability 下 A_pubmed 省 8% token
- 按 Phase-19 stop rule：C2 不作"显著能力优势"头条；保留为
  "任务偏好不同的架构基因分布（Phase-18 稳定复现）+ 自有任务配置的
  capability-cost 权衡占优"的谨慎表述

### C4（情景记忆贡献）—— **supported（holdout 存活）**
- GSM8K：+9.43pp（1.5B, p≈0）/ +11.16pp（7B, p≈0）
- PubMedQA：+2.75pp（1.5B, n.s.）/ +5.50pp（7B, p=0.017）
- 结论：记忆消融的退化在 holdout 上持续存在，且随骨干增大而增强

### C7（上下文策略权衡）—— supported
- 真实 token 计数确认 full > truncated > answer_only 的成本递减与
  相应能力变化（holdout CSV + landscape 表）

### 跨骨干转移（Task 4）
- 两配置在 7B 上分别 +15.3pp（GSM8K）/ +16.5pp（PubMedQA），任务偏好方向
  （GSM8K: A_gsm>A_pubmed；PubMedQA: A_pubmed≥A_gsm）在双骨干间保持一致
- 无排名反转 → 结果表述为"方向性任务偏好可转移到更大骨干"

## 门禁对照

- [x] 架构在 holdout 评估前锁定
- [x] GSM8K holdout 排除前 100 题；PubMedQA holdout 与校准不相交（有测试）
- [x] 跨任务冻结矩阵完成（2×2 + 基线 × 双骨干）
- [x] 1.5B/7B 转移完成
- [x] 逐题预测持久化（32380 行）
- [x] bootstrap CI + McNemar 已产出
- [x] 无观察 holdout 后的方法/架构改动（协议锁定后只修了一个 import bug，
  属正确性修复且在任何 mamba2 配置完成前修复）
- [ ] 论文迁移（Phase-19c 进行）

## 中途事故（如实记录）

phase19_holdout.py 缺 `adapt_substrate` import，四路运行在第 5 个配置
（首个 mamba2）处崩溃；修复后依靠 done-skip + 缓存续跑，无数据损失。
该修复发生在任何受影响配置完成之前，不影响结果完整性。
