#!/bin/bash
# Phase-15 real experiment, one method on one pinned GPU.
# Usage: bash scripts_vm/run_method.sh <CUDA_VISIBLE_DEVICES> <method> [benchmark] [limit] [pop] [gen] [batch]
set -e
cd /202532803004/NeuroEvoScientist
export HF_ENDPOINT=https://hf-mirror.com HF_HOME=/202532803004/datasets/hf
export CUDA_VISIBLE_DEVICES=${1:?need cuda index}
METHOD=${2:?need method}
BENCH=${3:-gsm8k}
LIMIT=${4:-100}
POP=${5:-16}
GEN=${6:-10}
BATCH=${7:-32}
PY=/202532803004/conda_envs/amber/bin/python
DATA=/202532803004/NeuroEvoScientist/data/$BENCH
if [ "$BENCH" = "pubmedqa" ]; then DATAFILE=$DATA/pqal.jsonl; else DATAFILE=$DATA/test.jsonl; fi
echo "run: method=$METHOD bench=$BENCH gpu=$CUDA_VISIBLE_DEVICES limit=$LIMIT pop=$POP gen=$GEN batch=$BATCH"
$PY src/scripts/run_experiment.py --method $METHOD --benchmark $BENCH \
    --model Qwen/Qwen2.5-1.5B-Instruct --device 0 --batch-size $BATCH \
    --limit $LIMIT --population $POP --generations $GEN \
    --data-path $DATAFILE
echo "DONE method=$METHOD bench=$BENCH"
