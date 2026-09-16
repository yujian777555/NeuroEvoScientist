#!/bin/bash
# Phase-18 Task 4: paired inheritance study (20 pairs).
set -e
cd /202532803004/NeuroEvoScientist
export HF_ENDPOINT=https://hf-mirror.com HF_HOME=/202532803004/datasets/hf HF_HUB_OFFLINE=1
export CUDA_VISIBLE_DEVICES=${1:?need gpu}
PY=/202532803004/conda_envs/amber/bin/python
$PY src/scripts/inheritance_study.py --pairs 20 --limit 100 \
    --model Qwen/Qwen2.5-1.5B-Instruct --device 0 --batch-size 32 \
    --data-path /202532803004/NeuroEvoScientist/data/gsm8k/test.jsonl \
    --calibration-path /202532803004/NeuroEvoScientist/data/gsm8k/train.jsonl
echo "INHERITANCE_STUDY_DONE"
