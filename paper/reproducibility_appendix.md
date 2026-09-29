# Reproducibility Appendix（提交版）

## 代码与数据

- 仓库：github.com/yujian777555/NeuroEvoScientist（提交时公开）
- 权威证据锚点 commit：`57d2465`（Phase-21 锁定）+ Planner 提交侧
  `5ad4b50`（submission freeze）
- 数据：GSM8K（openai/grade-school-math 官方 JSONL）、PubMedQA pqa_labeled
  （官方 ori_pqal.json）、QASPER（THUDM/LongBench data.zip）
- 模型：Qwen/Qwen2.5-1.5B-Instruct、Qwen/Qwen2.5-7B-Instruct（HF Hub 快照，
  sha 见 VM HF_HOME 缓存；`HF_HUB_OFFLINE=1` 可完全离线复现）

## 环境

- GPU：1–6 × NVIDIA A800 80GB（单卡即可复现全部实验）
- python 3.10+，torch 2.5.1+cu121，transformers 5.7.0，PyYAML，pytest
- 安装：`pip install -r requirements-a800.txt`

## 关键协议参数

| 项 | 值 | 出处 |
|---|---|---|
| 搜索空间 | 结构化基因组（memory×reasoning×context_policy×input_context×adaptation 条件子基因） | `configs/phase20_structured_search_space.yaml` |
| 种群/代际 | 16 / 10，seeds {0,1,2} | 各 run 配置 |
| 适应预算 | 48 校准样本、30 AdamW 步、lr 1e-3、冻结主干 | `configs/phase17_adaptation.yaml` |
| 评估区间 | GSM8K test[0:100] dev / test[100:1319] holdout；PubMedQA [0:100]/[100:500]（校准 [500:]）；QASPER [0:50]/[50:150]（校准 [150:]） | `configs/phase20_protocol.yaml` |
| 解码 | greedy、max_new_tokens=256、batch=32、FP16 | `configs/phase19_protocol.yaml` |
| 选择锁定 | holdout 评估前冻结 | `results/phase19_selection_lock.json`、`results/phase20_selection_lock.json` |

## 复现路径

1. 单测与语义门禁：`python -m pytest tests/ -q`（79+ 项，含稳定嵌入、
   表型去重、泄漏、规范化 F1）
2. 真实链路冒烟：`python src/scripts/run_experiment.py --method enss
   --benchmark gsm8k --model Qwen/Qwen2.5-1.5B-Instruct --limit 20`
3. 主实验矩阵：`scripts_vm/` 下各队列脚本（dev 搜索、holdout、消融、诊断）
4. 聚合：`aggregate_phase*.py`、`phase*_statistics.py`
5. 图表：`python src/scripts/render_figures.py`（全部终版图直接由
   `results/` 与 `experiments/` 聚合产物生成）

## 缓存与确定性

- 评估缓存：原子写（tmp+fsync+os.replace），键含 genome+model+区间+管线版本
  （phase20-v4），可断点续跑
- 确定性：贪心解码 + 逐基因组 hash 播种初始化 + SHA-256 稳定嵌入
- 已知环境差异：transformers 内核 lazy-load 失败时强制 naive Mamba2 路径
  （与历史执行路径一致，`src/models/mamba_memory.py`）

## 结果-证据映射

每条论文 claim 在 `docs/claim_audit.md` 与 `docs/phase21_final_audit.md`
中有 supported/partially/unsupported 状态与精确产物指针。
