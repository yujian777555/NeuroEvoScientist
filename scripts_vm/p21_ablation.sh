#!/bin/bash
# Phase-21 Task 2: controlled memory ablation (same frozen genome +/- memory).
# Usage: p21_ablation.sh <GPU> <benchmark>
set -e
cd /202532803004/NeuroEvoScientist
export HF_ENDPOINT=https://hf-mirror.com HF_HOME=/202532803004/datasets/hf HF_HUB_OFFLINE=1
export CUDA_VISIBLE_DEVICES=${1:?need gpu}
BENCH=${2:?need benchmark}
PY=/202532803004/conda_envs/amber/bin/python
DATA=/202532803004/NeuroEvoScientist/data
case $BENCH in
  pubmedqa) DATAFILE=$DATA/pubmedqa/pqal.jsonl ;;
  qasper) DATAFILE=$DATA/qasper/qasper.jsonl ;;
esac
for MODEL in Qwen/Qwen2.5-1.5B-Instruct Qwen/Qwen2.5-7B-Instruct; do
  $PY src/scripts/phase20_holdout.py --benchmark $BENCH --model $MODEL \
      --device 0 --batch-size 32 --data-path $DATAFILE \
      --calibration-path $DATAFILE \
      --lock results/phase21_ablation_lock.json
done
echo "ABLATION_DONE $BENCH"
