# Phase-14 A800 Runbook

Phase-14 的真实实验需要 GPU 环境（本仓库开发机为 CPU-only，torch 1.10 /
transformers 4.29 无法加载 Qwen2.5）。本手册描述 A800 上的复现步骤。

## 环境

```bash
pip install -r requirements-a800.txt   # torch>=2.1, transformers>=4.40, accelerate
```

硬件：1 x A800 80GB（计划配置）。模型：Qwen/Qwen2.5-1.5B-Instruct（默认，
`src/evaluator/backends.py: QwenBackend`，自动启用 chat template 与
device_map="auto"）。

## 冒烟（先做，验证可复现性）

```bash
python -m pytest tests/ -q                          # 21 项单元/管线测试
python src/scripts/run_experiment.py --method enss --benchmark gsm8k \
    --model Qwen/Qwen2.5-1.5B-Instruct --limit 20 \
    --population 8 --generations 3
```

## 正式实验（计划配置：population=32, generations=20）

```bash
# 完整基线矩阵（Table 1）：3 fixed + random + no_pareto + enss
python src/scripts/run_experiment.py --matrix --benchmark gsm8k \
    --model Qwen/Qwen2.5-1.5B-Instruct --population 32 --generations 20

# 消融（Table 2）
python src/scripts/run_experiment.py --method no_inherit --benchmark gsm8k \
    --model Qwen/Qwen2.5-1.5B-Instruct --population 32 --generations 20
python src/scripts/run_experiment.py --method no_mamba --benchmark gsm8k \
    --model Qwen/Qwen2.5-1.5B-Instruct --population 32 --generations 20
# w/o NSGA Pareto 即 --method no_pareto（矩阵中已含）
# w/o Evolution 即 --method random（矩阵中已含）
```

## 产物

- `experiments/<method>_<benchmark>_seed<N>/history.jsonl` — 每代 best/mean
  fitness、Pareto 前沿、架构分布（Figure 1/2/3 数据）
- `experiments/<run>/results.json` — 最优架构与三目标指标
- `experiments/baseline_matrix_<benchmark>_seed<N>.csv` — Table 1 矩阵表

## 注意事项

- GSM8K 数据首次运行自动下载到 `data/gsm8k/`（需网络或预置 JSONL，
  可用 `--data-path` 指定）。
- mock 评估器仅供 CI；论文结果必须用 `--benchmark gsm8k` + 真实模型。
- 多 seed 重复：对 `--seed 0/1/2` 各跑一遍矩阵。
