#!/bin/bash
# Phase-14 smoke: real GSM8K + Qwen2.5-1.5B on one pinned GPU.
# Usage: bash scripts_vm/smoke.sh <CUDA_VISIBLE_DEVICES> [limit] [pop] [gen]
set -e
cd /202532803004/NeuroEvoScientist
export HF_ENDPOINT=https://hf-mirror.com HF_HOME=/202532803004/datasets/hf
export CUDA_VISIBLE_DEVICES=${1:?need cuda index}
LIMIT=${2:-20}
POP=${3:-8}
GEN=${4:-3}
PY=/202532803004/conda_envs/amber/bin/python
echo "smoke: gpu=$CUDA_VISIBLE_DEVICES limit=$LIMIT pop=$POP gen=$GEN"
$PY src/scripts/run_experiment.py --method enss --benchmark gsm8k \
    --model Qwen/Qwen2.5-1.5B-Instruct --device 0 \
    --limit $LIMIT --population $POP --generations $GEN \
    --data-path /202532803004/NeuroEvoScientist/data/gsm8k/test.jsonl
