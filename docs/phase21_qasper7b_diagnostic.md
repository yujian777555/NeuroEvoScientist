# Phase-21 Task 3: QASPER-7B Collapse Diagnosis

日期：2026-09-24。诊断协议：冻结 12 个 QASPER holdout 题（items[50:62]），
4 配置 × 双骨干，禁止任何 prompt 调整。产物：`results/phase21_qasper_diag_15b.json`、
`phase21_qasper_diag_7b.json`（含逐题 raw output 与提取答案）。

## 诊断结果

| Config | Backbone | failure_mode | F1(extracted) | F1(whole) | marker 合规 | 平均输出词数 |
|---|---|---|---|---|---|---|
| A_qasper | 1.5B | answer_extraction_mismatch | 0.115 | 0.108 | 0.25 | 36 |
| A_gsm | 1.5B | mostly_functional | 0.169 | 0.047 | 1.00 | 110 |
| no_memory | 1.5B | mostly_functional | 0.098 | 0.054 | 0.83 | 114 |
| fixed_retrieval | 1.5B | mostly_functional | 0.136 | 0.120 | 0.58 | 46 |
| A_qasper | 7B | extraction/formatting（分类见下） | **0.000** | 0.107 | **1.00** | 36 |
| A_gsm | 7B | mostly_functional | 0.118 | 0.079 | 1.00 | 74 |
| no_memory | 7B | mostly_functional | 0.187 | 0.094 | 1.00 | 76 |
| fixed_retrieval | 7B | extraction/formatting | **0.000** | 0.172 | **1.00** | 34 |

## 结论：不是能力崩溃，是答案提取/格式失配

决定性证据（7B、Direct 类配置）：
- **marker 合规率 1.00**（7B 严格输出 `####` 标记）
- 但 **F1(extracted)=0.000 而 F1(whole)=0.107/0.172** —— 答案内容在正文中，
  `####` 之后为空或不含答案。7B 在 Direct 指令下倾向把答案放在标记**之前**
  或以"####"结尾不写内容；我们的提取规则取最后一个 `####` 之后的文本，
  因此得到空答案。
- A_gsm/no_memory（CoT 类 prompt）在 7B 上正常工作（F1 0.118/0.187），
  因为逐步推理的文本结构使答案落入标记之后。

**失效分类**：answer-extraction / formatting mismatch（不是生成退化，
不是 exemplar 过载，不是真实能力退化）。按 Phase-21 规则，主结果不据此改
prompt；Phase-20 的"7B 崩溃"表述修正为 **"backbone–prompt/extraction
interaction"**，并在论文中明确：该现象主要影响 Direct 类配置的指标，
而非 7B 的真实任务能力。

## 附带发现（诊断用全续写 F1，非主指标）

7B whole-continuation F1：A_qasper 0.107、fixed_retrieval 0.172 —— 7B 其实
掌握了部分答案内容，支持"提取失配"而非"能力缺失"的解释。
