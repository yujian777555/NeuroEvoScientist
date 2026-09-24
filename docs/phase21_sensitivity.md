# Phase-21 Task 1 Sensitivity Audit（任务感知去重后的 dev 重跑）

日期：2026-09-24。目的：验证任务感知表型规范化（Phase-21 Task 1）是否改变
C2a（搜索侧任务条件化偏好）结论。仅 dev 区间重跑（seeds 0/1/2，同 Phase-20
预算）；**不**触碰 Phase-20 holdout 结果。

## 修正后 dev 最优（vs Phase-20 原最优）

### GSM8K
| seed | memory | reasoning | context | exemplars | cap |
|---|---|---|---|---|---|
| s0 | none | cot (d2) | answer_only | 0 | 0.55 |
| s1 | recency(k2) | cot (d2) | full | 1 | 0.59 |
| s2 | retrieval(k1) | cot (d3) | full | 3 | 0.62 |

Phase-20 原：s2 = recency(k3)+cot(d3)+full+1。**同一架构族**：CoT 主导（3/3），
轻记忆/少 exemplar，depth 2-3。族级结论不变。

### PubMedQA
| seed | memory | reasoning | cap |
|---|---|---|---|
| s0 | none | direct | 0.44 |
| s1 | none | direct | 0.44 |
| s2 | none | direct | 0.44 |

Phase-20 原：3/3 seed none+direct。**完全一致**。

## 表型多样性与重复率

- GSM8K：480 次评估，180 个唯一任务感知表型（代内重复率 62.5%）
- PubMedQA：480 次评估，202 个唯一任务感知表型（重复率 57.9%）

## 结论

**C2a 稳健**：任务感知去重修正没有改变任何任务的收敛架构族
（PubMedQA 逐基因一致；GSM8K 族内变化仅在记忆子类型，与 Phase-20 各 seed
已有的族内波动一致）。C2a 维持 supported。
