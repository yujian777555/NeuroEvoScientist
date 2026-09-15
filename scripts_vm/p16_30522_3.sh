#!/bin/bash
# Phase-16 queue: card 30522:3 — no_inherit, seeds 1-2, both benchmarks
set -e
D=/202532803004/NeuroEvoScientist/scripts_vm
for S in 1 2; do
  bash $D/run_method.sh 3 no_inherit gsm8k 100 16 10 32 $S
  bash $D/run_method.sh 3 no_inherit pubmedqa 100 16 10 32 $S
done
echo "QUEUE_DONE card30522_3"
