#!/bin/bash
# Phase-18 misc queue (30108:1): pubmedqa fixed x3, no_memory pubmedqa s0-2,
# no_memory gsm8k s0-2, fixed_hybrid gsm8k.
set -e
D=/202532803004/NeuroEvoScientist/scripts_vm
for M in fixed_recency fixed_retrieval fixed_mamba2 fixed_hybrid; do
  bash $D/run_method.sh 1 $M pubmedqa 100 16 10 32 0
done
for S in 0 1 2; do
  bash $D/run_method.sh 1 no_memory pubmedqa 100 16 10 32 $S
done
for S in 0 1 2; do
  bash $D/run_method.sh 1 no_memory gsm8k 100 16 10 32 $S
done
bash $D/run_method.sh 1 fixed_hybrid gsm8k 100 16 10 32 0
echo "QUEUE_DONE misc30108"
