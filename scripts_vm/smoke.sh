#!/bin/bash
# Phase-15 smoke: substrate-activated pipeline on one pinned GPU.
# Usage: bash scripts_vm/smoke.sh <CUDA_VISIBLE_DEVICES> [benchmark] [limit] [pop] [gen]
set -e
bash /202532803004/NeuroEvoScientist/scripts_vm/run_method.sh \
    "${1:?need cuda index}" enss "${2:-gsm8k}" "${3:-20}" "${4:-8}" "${5:-3}" 32
