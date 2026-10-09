#!/bin/bash
# F1 cell runner on one pinned GPU.
# Usage: f1_cell.sh <GPU> <model> <cells-csv>
set -e
cd /202532803004/NeuroEvoScientist
export HF_ENDPOINT=https://hf-mirror.com HF_HOME=/202532803004/datasets/hf HF_HUB_OFFLINE=1
export CUDA_VISIBLE_DEVICES=${1:?need gpu}
MODEL=${2:?need model}
CELLS=${3:?need cells}
PY=/202532803004/conda_envs/amber/bin/python
echo "f1: gpu=$CUDA_VISIBLE_DEVICES model=$MODEL cells=$CELLS"
$PY src/scripts/f1_run.py --model $MODEL --device 0 --batch-size 32 --cells $CELLS
echo "F1_CELLS_DONE $CELLS"
