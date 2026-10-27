#!/usr/bin/env bash
# Deterministic 40-shard adaptive permutation replay (CPU-only, no GPU).
set -euo pipefail
REPO=${1:-.}
OUT=${2:-phase2/pilot_r1}
WORKERS=${3:-40}
SHARD_SIZE=25
cd "$REPO"
export PYTHONPATH=src
export HF_HOME=/202532803004/datasets/hf
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_OFFLINE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
mkdir -p "$OUT/analysis"
declare -a pids=()
for ((shard=0; shard<WORKERS; shard++)); do
  start=$((shard * SHARD_SIZE + 1))
  end=$((start + SHARD_SIZE - 1))
  /202532803004/conda_envs/amber/bin/python src/scripts/phase2_run.py null-full \
    --repo . --out "$OUT" --start "$start" --end "$end" \
    > "$OUT/analysis/shard_${start}_${end}.log" 2>&1 &
  pids+=("$!")
done
set +e
wait
set -e
for ((shard=0; shard<WORKERS; shard++)); do
  start=$((shard * SHARD_SIZE + 1))
  end=$((start + SHARD_SIZE - 1))
  if [[ ! -s "$OUT/analysis/null_$(printf '%04d' "$start")_$(printf '%04d' "$end").json" ]]; then
    /202532803004/conda_envs/amber/bin/python - <<PY
import json
from phase2 import preflight
preflight.write_json({"status":"INCOMPLETE","reason":"missing shard ${start}_${end}"},
                     "$OUT/analysis/null_sharded_failure.json")
PY
    exit 1
  fi
done
/202532803004/conda_envs/amber/bin/python src/scripts/phase2_run.py null-merge --repo . --out "$OUT"
/202532803004/conda_envs/amber/bin/python src/scripts/phase2_run.py combine --repo . --out "$OUT"
echo "SHARDED_NULL_COMPLETE workers=$WORKERS shard_size=$SHARD_SIZE"
