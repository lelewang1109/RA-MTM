# Formal evidence package

One complete run only. `run_status.json` must say `complete`; verify with
`python scripts/manifest.py --verify`. Full reproduction: `./scripts/run_all.sh`.

- `main/`: seven canonical 2-D fields, 1-D mechanisms, paper tables and figures.
- `auxiliary/`: static/scope sanity checks; not baseline superiority evidence.
- `ablation/`: component tests on simple and difficult fields.
- `sensitivity/`: parameter, centroid perturbation, baseline settings and first-frame calibration.
- `validity/`: topology, feasibility, lower bounds and raster metric checks.
- `supplementary/`: every declared replicate/resolution, paired differences, and complete raw suite artifacts.

Raw suite tables duplicate the same current run for traceability; no historical
versions are retained here. Previous runs are local-only under `archive/`.
The sole experiment report is `docs/EXPERIMENT_REPORT.md`.
