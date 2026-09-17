#!/bin/bash
# Phase-19 holdout run: one benchmark x one backbone on one pinned GPU.
# Usage: p19_holdout.sh <GPU> <benchmark> <model>
set -e
cd /202532803004/NeuroEvoScientist
export HF_ENDPOINT=https://hf-mirror.com HF_HOME=/202532803004/datasets/hf HF_HUB_OFFLINE=1
export CUDA_VISIBLE_DEVICES=${1:?need gpu}
BENCH=${2:?need benchmark}
MODEL=${3:?need model}
PY=/202532803004/conda_envs/amber/bin/python
DATA=/202532803004/NeuroEvoScientist/data/$BENCH
if [ "$BENCH" = "pubmedqa" ]; then DATAFILE=$DATA/pqal.jsonl; CALIB=$DATA/pqal.jsonl; else DATAFILE=$DATA/test.jsonl; CALIB=$DATA/train.jsonl; fi
echo "holdout: bench=$BENCH model=$MODEL gpu=$CUDA_VISIBLE_DEVICES"
$PY src/scripts/phase19_holdout.py --benchmark $BENCH --model $MODEL \
    --device 0 --batch-size 32 --data-path $DATAFILE --calibration-path $CALIB
echo "P19_DONE $BENCH $MODEL"
