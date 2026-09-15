#!/bin/bash
# Phase-14 real GSM8K experiment, one method on one pinned GPU.
# Usage: bash scripts_vm/run_method.sh <CUDA_VISIBLE_DEVICES> <method> [limit] [pop] [gen] [batch]
set -e
cd /202532803004/NeuroEvoScientist
export HF_ENDPOINT=https://hf-mirror.com HF_HOME=/202532803004/datasets/hf
export CUDA_VISIBLE_DEVICES=${1:?need cuda index}
METHOD=${2:?need method}
LIMIT=${3:-100}
POP=${4:-16}
GEN=${5:-10}
BATCH=${6:-32}
PY=/202532803004/conda_envs/amber/bin/python
echo "run: method=$METHOD gpu=$CUDA_VISIBLE_DEVICES limit=$LIMIT pop=$POP gen=$GEN batch=$BATCH"
$PY src/scripts/run_experiment.py --method $METHOD --benchmark gsm8k \
    --model Qwen/Qwen2.5-1.5B-Instruct --device 0 --batch-size $BATCH \
    --limit $LIMIT --population $POP --generations $GEN \
    --data-path /202532803004/NeuroEvoScientist/data/gsm8k/test.jsonl
echo "DONE method=$METHOD"
