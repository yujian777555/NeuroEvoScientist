# Phase-20 Results: Structured Task-Conditioned Cognitive Co-Design

日期：2026-09-23（hotfix 后修正版语义，phase20-v4 缓存隔离）
搜索：结构化基因组（条件子基因），dev 区间，enss × 3 基准 × seeds 0-2 + random 诊断
Holdout：预注册锁定（results/phase20_selection_lock.json，先于 holdout 推理），
GSM8K test[100:1319] / PubMedQA[100:500] / QASPER[50:150]，双骨干，逐题预测 + 配对统计
产物：results/phase20_{holdout_results.csv, item_predictions.jsonl, statistics.json,
task_transfer.csv, backbone_transfer.csv, mechanism_cases.json}

## 任务条件化架构偏好（搜索侧，3 seed 稳定）

| 任务 | 收敛架构 | dev cap |
|---|---|---|
| GSM8K | recency(k=3) + CoT(depth 2-3) + full + 1 exemplar | 0.55–0.60 |
| PubMedQA | **memory=none** + direct（3 seed 完全一致） | 0.44 |
| QASPER | **retrieval(hashed_bow, k=4)** + direct + 8 exemplars + truncated(256w) + input_budget 1024 | 0.22 |

QASPER 预注册预测成立：检索记忆首次成为最优（长上下文任务）。
三任务基因分布确实 distinct —— 这是本阶段最强正面证据。

## Holdout 配对统计（bootstrap 10000 + McNemar；pp = 百分点）

### GSM8K（自有任务大胜）
| 比较 | 1.5B | 7B |
|---|---|---|
| A_gsm vs A_pubmed | +42.2*** | +71.3*** |
| A_gsm vs A_qasper | +31.0*** | +66.4*** |
| A_gsm vs best fixed | +29.0*** | +16.7*** |
| A_gsm vs no_memory | −0.1 (n.s.) | +12.6*** |

### PubMedQA（自有任务落败——如实报告）
| 比较 | 1.5B | 7B |
|---|---|---|
| A_pubmed vs A_gsm | −11.8*** | −16.0*** |
| A_pubmed vs A_qasper | −19.0*** | −9.0** |
| A_pubmed vs best fixed | −22.5*** | −11.5*** |

### QASPER（自有任务落败——如实报告）
| 比较 | 1.5B | 7B |
|---|---|---|
| A_qasper vs A_gsm | −5.0* | −18.2*** |
| A_qasper vs no_memory | −6.4* | −20.8*** |
| A_qasper 7B vs 1.5B | −13.1***（7B 崩溃，骨干依赖） | — |

\* p<0.05, \*\* p<0.01, \*\*\* p<0.001

## 结论（诚实版）

1. **任务条件化"选择"是真实的**：结构化搜索在不同任务上稳定收敛到不同基因
   （PubMedQA 三 seed 完全一致地选 none+direct；QASPER 选 retrieval）。
2. **"自有任务配置在其任务上最优"只在 GSM8K 成立**；
   PubMedQA/QASPER 上 GSM8K 选出的 CoT 配置反而更强——小 dev 区间上的
   搜索偏好不等于 holdout 泛化优势。
3. **记忆的作用随骨干放大**：GSM8K 7B 上 no_memory −12.6pp，1.5B 无差异。
   （Phase-21 澄清：记忆因果主张仅限同基因 ±memory 比较，即 `A_gsm vs
   no_memory` 与 Phase-21 受控消融；`A_pubmed/A_qasper vs no_memory` 的比较
   混杂了 reasoning/context 差异，不作记忆因果证据。）
4. **QASPER 在 7B 上整体崩溃**（A_qasper −13pp，多个配置趋零）——骨干依赖性
   真实存在，如实记录；具体失效模式见 Phase-21 诊断
   （`docs/phase21_qasper7b_diagnostic.md`）。
5. C3/C5 保持关闭（未重开）。

## 产物指针

统计：`results/phase20_statistics.json`；转移矩阵：
`phase20_task_transfer.csv` / `phase20_backbone_transfer.csv`；
机制案例：`phase20_mechanism_cases.json` + `docs/phase20_mechanism_analysis.md`。
