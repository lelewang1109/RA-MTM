#!/bin/sh
set -eu
cd "$(dirname "$0")/.."

PYTHON_RUNNER="${PYTHON_RUNNER:-python3}"

PYTHON_INITIAL="$PYTHON_RUNNER" ./experiments/synthetic_1d/run_pipeline.sh
"$PYTHON_RUNNER" experiments/gaussian_2d/run_experiment.py
