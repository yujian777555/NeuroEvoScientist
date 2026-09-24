# Phase-21 Paper Tables

## Table A: 主结果（holdout capability，锁定配置 × 双骨干）

来源：`results/phase20_holdout_results.csv`

### GSM8K

| Config | 1.5B | 7B |
|---|---|---|
| **A_gsm** (搜索选出) | 0.518 | **0.859** |
| A_pubmed | 0.096 | 0.146 |
| A_qasper | 0.325 | 0.693 |
| best fixed | 0.229 (recency) | 0.549 (mamba2) |
| no_memory | 0.449 | 0.585 |

### PubMedQA

| Config | 1.5B | 7B |
|---|---|---|
| **A_pubmed** (搜索选出) | 0.372 | 0.487 |
| A_gsm | 0.490 | 0.647 |
| A_qasper | 0.562 | 0.553 |
| best fixed | 0.572 (retrieval) | 0.602 (recency) |
| no_memory | 0.510 | 0.648 |

### QASPER（LongBench 兼容规范化 F1）

| Config | 1.5B | 7B |
|---|---|---|
| **A_qasper** (搜索选出) | 0.137 | 0.006† |
| A_gsm | 0.187 | 0.187 |
| A_pubmed | 0.110 | 0.006† |
| best fixed | 0.175 (mamba2) | 0.014 (retrieval) |
| no_memory | 0.201 | 0.187 |

† Phase-21 诊断为答案提取/格式失配（见 `docs/phase21_qasper7b_diagnostic.md`），
非能力崩溃。

## Table B: 受控记忆消融（同基因 ±memory）

来源：`results/phase20_holdout_results.csv`（phase21_ablation_lock）

| 任务 | backbone | memory ON | memory OFF | Δ |
|---|---|---|---|---|
| PubMedQA | 1.5B | 0.5525 | 0.3725 | **+18.0pp** |
| QASPER | 1.5B | 0.1254 | 0.1106 | +1.5pp |
| QASPER | 7B | 0.0076 | 0.0064 | +0.1pp† |

† 受 QASPER-7B 提取失配影响（诊断文档）。

## Table C: QASPER-7B 诊断（失效模式分类）

来源：`results/phase21_qasper_diag_{15b,7b}.json`

| Config | backbone | F1(extracted) | F1(whole) | marker | 失效分类 |
|---|---|---|---|---|---|
| A_qasper | 7B | 0.000 | 0.107 | 1.00 | 提取/格式失配 |
| fixed_retrieval | 7B | 0.000 | 0.172 | 1.00 | 提取/格式失配 |
| A_gsm | 7B | 0.118 | 0.079 | 1.00 | 正常 |
| no_memory | 7B | 0.187 | 0.094 | 1.00 | 正常 |
