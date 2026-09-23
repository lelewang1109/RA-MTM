# Formal evidence package

One complete run only. `run_status.json` must say `complete`; verify with
`python scripts/manifest.py --verify`. Full reproduction: `./scripts/run_all.sh`.

- `main/`: canonical fields, 18-sequence stability, calibration boundaries and crowding tradeoff.
- `auxiliary/`: static/scope sanity checks; not baseline superiority evidence.
- `ablation/`: five core variants and independent temporal-term evidence.
- `sensitivity/`: parameter, centroid perturbation, baseline settings and first-frame calibration.
- `validity/`: topology, feasibility, lower bounds and raster metric checks.
- `supplementary/`: every declared replicate/resolution, paired differences, and complete raw suite artifacts.

Raw suite tables duplicate the same current run for traceability; no historical
versions are retained here. Previous runs are local-only under `archive/`.
The sole experiment report is `docs/EXPERIMENT_REPORT.md`.



<!-- ERA5 -->
ERA5 full-period evidence: `main/era5_metrics.csv`, `main/era5_metrics.tex`, `main/figures/era5_evidence.png`, and `main/figures/era5_tracks.png`. Ablation, sensitivity, auxiliary and validity files use the `era5_` prefix; all protocols, source hash, matching and solver records are in `supplementary/era5/`. See report §9 for boundaries and raster budgets.

## Dual-reference evidence (2026-09-23)

The additive `dual_reference/` package preserves all historical tables and adds
25 scalar sequences, paired X/Y layouts, exact controls, seven publication plates
(six main plus one supplement), and full certificates. See
[upgrade report](../docs/DUAL_REFERENCE_REPORT.md). Its independent manifest is
verified with `python experiments/dual_reference/manifest.py --verify`. The old
root and ERA5/Ring manifests are not re-certified against changed shared source.
