#!/bin/bash
# Resumable rerun of every ERA5 analysis on the expanded-window / true-minima setting (2026-09-27).
# Each step writes a marker in prototypes/output/.done_expanded/; rerunning this script skips finished steps.
# Log: prototypes/output/run_expanded.log.   Run: bash prototypes/run_expanded.sh
cd "$(dirname "$0")/.." || exit 1
M=prototypes/output/.done_expanded; mkdir -p $M; LOG=prototypes/output/run_expanded.log
PY=".venv/bin/python -W ignore"
step() { name=$1; shift
  if [ -f $M/$name ]; then echo "skip $name" >> $LOG; return; fi
  echo "=== $name $(date '+%F %T')" >> $LOG
  if "$@" >> $LOG 2>&1; then touch $M/$name; echo "ok $name $(date '+%T')" >> $LOG; else echo "FAIL $name" >> $LOG; exit 1; fi; }
step replicate_era5      $PY prototypes/replicate.py era5
step replicate_era5_2014 $PY prototypes/replicate.py era5_2014
step replicate_summary   $PY prototypes/replicate.py --summarize
step robustness          $PY prototypes/robustness.py
step boundary            $PY prototypes/boundary.py
step witness_stats       $PY prototypes/witness_stats.py
step persistence         $PY prototypes/persistence.py
step pointcert           $PY prototypes/pointcert.py
step filling             $PY prototypes/filling.py
step frontier            $PY prototypes/frontier.py
step attainable_era5     $PY prototypes/attainable.py era5
step attainable_era5_2014 $PY prototypes/attainable.py era5_2014
step eval_era5           $PY prototypes/eval_v2.py era5
step eval_era5_2014      $PY prototypes/eval_v2.py era5_2014
step stmtm_grid          $PY prototypes/stmtm_grid.py era5 era5_2014
step sensitivity         $PY prototypes/sensitivity.py era5_s150 era5_s350 era5_2014_s200 era5_2014_s350 era5_crop era5_2014_crop
echo "ALL DONE $(date '+%F %T')" >> $LOG
