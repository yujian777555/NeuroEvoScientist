#!/bin/bash
# Phase-20 mechanism case capture: small no-cache runs with model outputs.
# Usage: p20_mechanism.sh <GPU>
set -e
cd /202532803004/NeuroEvoScientist
export HF_ENDPOINT=https://hf-mirror.com HF_HOME=/202532803004/datasets/hf HF_HUB_OFFLINE=1
export CUDA_VISIBLE_DEVICES=${1:?need gpu}
PY=/202532803004/conda_envs/amber/bin/python
DATA=/202532803004/NeuroEvoScientist/data
for BENCH in gsm8k pubmedqa qasper; do
  case $BENCH in
    gsm8k) DATAFILE=$DATA/gsm8k/test.jsonl; CALIB=$DATA/gsm8k/train.jsonl ;;
    pubmedqa) DATAFILE=$DATA/pubmedqa/pqal.jsonl; CALIB=$DATA/pubmedqa/pqal.jsonl ;;
    qasper) DATAFILE=$DATA/qasper/qasper.jsonl; CALIB=$DATA/qasper/qasper.jsonl ;;
  esac
  $PY src/scripts/phase20_holdout.py --benchmark $BENCH \
      --model Qwen/Qwen2.5-1.5B-Instruct --device 0 --batch-size 32 \
      --data-path $DATAFILE --calibration-path $CALIB \
      --configs A_gsm,A_pubmed,A_qasper,fixed_recency \
      --limit 12 --no-cache \
      --out-results results/phase20_mechanism_runs.csv \
      --out-predictions results/phase20_predictions_with_outputs.jsonl
done
echo "MECHANISM_RUNS_DONE"
