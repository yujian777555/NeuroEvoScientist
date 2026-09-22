#!/bin/bash
# Phase-20 queue: one method x benchmark x seeds.
# Usage: p20_queue.sh <GPU> <method> <benchmark> [seeds...]
set -e
GPU=${1:?need gpu}
METHOD=${2:?need method}
BENCH=${3:?need benchmark}
shift 3
D=/202532803004/NeuroEvoScientist/scripts_vm
for S in ${@:-0}; do
  bash $D/p20_run.sh $GPU $METHOD $BENCH 16 10 $S
done
echo "QUEUE_DONE $METHOD $BENCH"
