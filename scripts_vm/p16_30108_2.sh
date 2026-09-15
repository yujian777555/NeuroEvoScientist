#!/bin/bash
# Phase-16 queue: card 30108:2 — no_memory ablation, seeds 0-2, both benchmarks
set -e
D=/202532803004/NeuroEvoScientist/scripts_vm
for S in 0 1 2; do
  bash $D/run_method.sh 2 no_memory gsm8k 100 16 10 32 $S
  bash $D/run_method.sh 2 no_memory pubmedqa 100 16 10 32 $S
done
echo "QUEUE_DONE card30108_2"
