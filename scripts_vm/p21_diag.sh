#!/bin/bash
# Phase-21 Task 3: QASPER-7B diagnostic on both backbones.
set -e
cd /202532803004/NeuroEvoScientist
export HF_ENDPOINT=https://hf-mirror.com HF_HOME=/202532803004/datasets/hf HF_HUB_OFFLINE=1
export CUDA_VISIBLE_DEVICES=${1:?need gpu}
PY=/202532803004/conda_envs/amber/bin/python
$PY src/scripts/phase21_qasper_diagnostic.py --model Qwen/Qwen2.5-1.5B-Instruct \
    --device 0 --batch-size 16 \
    --data-path /202532803004/NeuroEvoScientist/data/qasper/qasper.jsonl
cp results/phase21_qasper7b_diagnostic.json results/phase21_qasper_diag_15b.json
$PY src/scripts/phase21_qasper_diagnostic.py --model Qwen/Qwen2.5-7B-Instruct \
    --device 0 --batch-size 16 \
    --data-path /202532803004/NeuroEvoScientist/data/qasper/qasper.jsonl
cp results/phase21_qasper7b_diagnostic.json results/phase21_qasper_diag_7b.json
echo "DIAG_QUEUE_DONE"
