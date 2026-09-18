#!/bin/sh
set -eu
cd "$(dirname "$0")/../.."
PYTHON_INITIAL="${PYTHON_INITIAL:-python3}"
"$PYTHON_INITIAL" experiments/initial/run_initial.py
"$PYTHON_INITIAL" experiments/initial/verify.py
"$PYTHON_INITIAL" experiments/initial/sensitivity.py
"$PYTHON_INITIAL" experiments/initial/ablation.py
"$PYTHON_INITIAL" experiments/initial/finalize.py
