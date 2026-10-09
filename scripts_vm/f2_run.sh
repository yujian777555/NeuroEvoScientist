#!/bin/bash
# F2 single-shot SVAMP confirmation on one pinned GPU.
# Usage: f2_run.sh <GPU> [git_sha]
set -e
cd /202532803004/NeuroEvoScientist
export HF_ENDPOINT=https://hf-mirror.com HF_HOME=/202532803004/datasets/hf HF_HUB_OFFLINE=1
export CUDA_VISIBLE_DEVICES=${1:?need gpu}
export F2_GIT_SHA=${2:-unknown}
PY=/202532803004/conda_envs/amber/bin/python
echo "f2: gpu=$CUDA_VISIBLE_DEVICES git_sha=$F2_GIT_SHA"
$PY src/scripts/f2_run.py --model Qwen/Qwen2.5-1.5B-Instruct --device 0 --batch-size 32 --gpu-budget-min 55
echo "F2_RUN_DONE"
