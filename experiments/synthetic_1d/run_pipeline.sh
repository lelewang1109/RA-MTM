#!/bin/sh
set -eu
cd "$(dirname "$0")/../.."
PYTHON_INITIAL="${PYTHON_INITIAL:-python3}"
"$PYTHON_INITIAL" experiments/synthetic_1d/run_experiments.py
"$PYTHON_INITIAL" experiments/synthetic_1d/verify.py
"$PYTHON_INITIAL" experiments/synthetic_1d/sensitivity.py
"$PYTHON_INITIAL" experiments/synthetic_1d/ablation.py
"$PYTHON_INITIAL" experiments/synthetic_1d/finalize.py
