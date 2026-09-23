# Experiments

Run `./scripts/run_all.sh` from the repository root for the complete clean-run,
validation and publication workflow. See `docs/PROJECT_STRUCTURE.md` and
`docs/EXPERIMENT_REPORT.md`. Individual scripts are intermediate development
stages and do not publish a complete manifest.

Ring uses the same three-method runner as ERA5/Storms. See
[Ring reproduction and comparison protocol](ring/README.md); its independent
verification writes a Ring-scoped manifest without re-certifying older runs.
