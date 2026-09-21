#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
PYTHON_RUNNER="${PYTHON_RUNNER:-python3}"
exec "$PYTHON_RUNNER" scripts/run_all.py
