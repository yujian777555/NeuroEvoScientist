#!/bin/bash
# Phase-20 holdout run: one benchmark x one backbone on one pinned GPU.
# Usage: p20_holdout.sh <GPU> <benchmark> <model>
set -e
cd /202532803004/NeuroEvoScientist
export HF_ENDPOINT=https://hf-mirror.com HF_HOME=/202532803004/datasets/hf HF_HUB_OFFLINE=1
export CUDA_VISIBLE_DEVICES=${1:?need gpu}
BENCH=${2:?need benchmark}
MODEL=${3:?need model}
PY=/202532803004/conda_envs/amber/bin/python
DATA=/202532803004/NeuroEvoScientist/data
case $BENCH in
  gsm8k) DATAFILE=$DATA/gsm8k/test.jsonl; CALIB=$DATA/gsm8k/train.jsonl ;;
  pubmedqa) DATAFILE=$DATA/pubmedqa/pqal.jsonl; CALIB=$DATA/pubmedqa/pqal.jsonl ;;
  qasper) DATAFILE=$DATA/qasper/qasper.jsonl; CALIB=$DATA/qasper/qasper.jsonl ;;
esac
echo "p20_holdout: bench=$BENCH model=$MODEL gpu=$CUDA_VISIBLE_DEVICES"
$PY src/scripts/phase20_holdout.py --benchmark $BENCH --model $MODEL \
    --device 0 --batch-size 32 --data-path $DATAFILE --calibration-path $CALIB
echo "P20_HOLDOUT_DONE $BENCH $MODEL"
