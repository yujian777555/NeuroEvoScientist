#!/bin/bash
# Phase-20 diagnostic reference: random search on all 3 benchmarks (seed 0).
# Diagnostic only (C3 closed; no superiority comparison).
set -e
D=/202532803004/NeuroEvoScientist/scripts_vm
for BENCH in gsm8k pubmedqa qasper; do
  bash $D/p20_run.sh ${1:?need gpu} random $BENCH 16 10 0
done
echo "QUEUE_DONE random_diagnostic"
