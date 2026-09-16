#!/bin/bash
# Phase-18 Task 2: exhaustive 48-point landscape for one benchmark.
# Usage: p18_landscape.sh <GPU> <benchmark>
set -e
cd /202532803004/NeuroEvoScientist
export HF_ENDPOINT=https://hf-mirror.com HF_HOME=/202532803004/datasets/hf HF_HUB_OFFLINE=1
export CUDA_VISIBLE_DEVICES=${1:?need gpu}
BENCH=${2:?need benchmark}
PY=/202532803004/conda_envs/amber/bin/python
DATA=/202532803004/NeuroEvoScientist/data/$BENCH
if [ "$BENCH" = "pubmedqa" ]; then DATAFILE=$DATA/pqal.jsonl; else DATAFILE=$DATA/test.jsonl; fi
echo "landscape: bench=$BENCH gpu=$CUDA_VISIBLE_DEVICES"
$PY src/scripts/run_experiment.py --landscape --benchmark $BENCH \
    --model Qwen/Qwen2.5-1.5B-Instruct --device 0 --batch-size 32 \
    --limit 100 --data-path $DATAFILE
echo "LANDSCAPE_QUEUE_DONE $BENCH"
