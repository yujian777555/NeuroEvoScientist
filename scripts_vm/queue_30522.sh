#!/bin/bash
# Phase-14 fixed baselines + no_mamba queue for container 30522 GPU3.
# Fixed baselines are 3 single evaluations (fast); no_mamba runs after.
set -e
cd /202532803004/NeuroEvoScientist
for M in fixed_attention fixed_mamba fixed_hybrid; do
  bash scripts_vm/run_method.sh 3 $M "${1:-100}" 16 10 "${2:-32}"
done
bash scripts_vm/run_method.sh 3 no_mamba "${1:-100}" 16 10 "${2:-32}"
echo "ALL_DONE container30522"
