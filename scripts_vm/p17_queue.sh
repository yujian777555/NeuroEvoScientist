#!/bin/bash
# Phase-17 focused matrix queue. Usage: p17_queue.sh <GPU> <method> [seeds...]
set -e
GPU=${1:?need gpu}
METHOD=${2:?need method}
shift 2
D=/202532803004/NeuroEvoScientist/scripts_vm
for S in ${@:-0}; do
  bash $D/run_method.sh $GPU $METHOD gsm8k 100 16 10 32 $S
done
echo "QUEUE_DONE $METHOD"
