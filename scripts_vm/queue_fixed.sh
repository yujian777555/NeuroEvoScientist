#!/bin/bash
# Phase-15: the three fixed baselines on both benchmarks, one pinned GPU.
# Usage: bash scripts_vm/queue_fixed.sh <CUDA_VISIBLE_DEVICES> [limit] [batch]
set -e
GPU=${1:?need cuda index}
LIMIT=${2:-100}
BATCH=${3:-32}
for BENCH in gsm8k pubmedqa; do
  for M in fixed_attention fixed_mamba fixed_hybrid; do
    bash /202532803004/NeuroEvoScientist/scripts_vm/run_method.sh $GPU $M $BENCH $LIMIT 16 10 $BATCH
  done
done
echo "QUEUE_DONE fixed"
