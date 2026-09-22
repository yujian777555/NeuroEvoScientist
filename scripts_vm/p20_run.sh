#!/bin/bash
# Phase-20 structured search run: one method x benchmark on one pinned GPU.
# Usage: p20_run.sh <GPU> <method> <benchmark> [pop] [gen] [seed] [model]
set -e
cd /202532803004/NeuroEvoScientist
export HF_ENDPOINT=https://hf-mirror.com HF_HOME=/202532803004/datasets/hf HF_HUB_OFFLINE=1
export CUDA_VISIBLE_DEVICES=${1:?need gpu}
METHOD=${2:-enss}
BENCH=${3:-gsm8k}
POP=${4:-16}
GEN=${5:-10}
SEED=${6:-0}
MODEL=${7:-Qwen/Qwen2.5-1.5B-Instruct}
PY=/202532803004/conda_envs/amber/bin/python
DATA=/202532803004/NeuroEvoScientist/data
case $BENCH in
  gsm8k) DATAFILE=$DATA/gsm8k/test.jsonl ;;
  pubmedqa) DATAFILE=$DATA/pubmedqa/pqal.jsonl ;;
  qasper) DATAFILE=$DATA/qasper/qasper.jsonl ;;
esac
echo "p20: method=$METHOD bench=$BENCH pop=$POP gen=$GEN seed=$SEED gpu=$CUDA_VISIBLE_DEVICES"
$PY src/scripts/run_structured_search.py --method $METHOD --benchmark $BENCH \
    --model $MODEL --device 0 --batch-size 32 \
    --population $POP --generations $GEN --seed $SEED \
    --data-path $DATAFILE
echo "P20_QUEUE_DONE $METHOD $BENCH $SEED"
