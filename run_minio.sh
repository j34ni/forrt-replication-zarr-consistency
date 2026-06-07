#!/usr/bin/env bash
# Launcher: sources ~/.bashrc to pick up MINIO_* env vars, then runs the matrix.
# Usage: bash run_minio.sh [--trials N] [--minio-trials N]
set -euo pipefail
# shellcheck source=/dev/null
source ~/.bashrc
exec pixi run python -m harness.run_matrix \
    --trials 1000 \
    --minio-trials 100 \
    --out data/results/results.parquet \
    "$@"
