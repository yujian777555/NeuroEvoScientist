#!/bin/bash
# Phase-15: run one method on BOTH benchmarks (gsm8k then pubmedqa),
# sequentially on one pinned GPU.
# Usage: bash scripts_vm/queue_method.sh <CUDA_VISIBLE_DEVICES> <method> [limit] [pop] [gen] [batch]
set -e
GPU=${1:?need cuda index}
METHOD=${2:?need method}
LIMIT=${3:-100}
POP=${4:-16}
GEN=${5:-10}
BATCH=${6:-32}
bash /202532803004/NeuroEvoScientist/scripts_vm/run_method.sh $GPU $METHOD gsm8k $LIMIT $POP $GEN $BATCH
bash /202532803004/NeuroEvoScientist/scripts_vm/run_method.sh $GPU $METHOD pubmedqa $LIMIT $POP $GEN $BATCH
echo "QUEUE_DONE method=$METHOD"
