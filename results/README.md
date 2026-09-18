# Result layout

Results are grouped by experiment and then by artifact role:

```text
results/
  synthetic_1d/
    figures/   main and diagnostic figures
    tables/    metrics, trajectories, sensitivity, and ablation CSV files
    records/   certificates, parameters, validation, and intermediate JSON files
    arrays/    large reproducible NPZ arrays, excluded from Git
  gaussian_2d/
    figures/   comparison figures, intermediate visualizations, and animation
    tables/    metrics, trajectories, topology checks, and raster errors
    records/   parameters, validation, and method intermediates
    arrays/    large reproducible NPZ arrays, excluded from Git
```

Each experiment root contains a SHA-256 `manifest.json`. The paper-facing entry points are `figures/` and `tables/`; `records/` and `arrays/` provide audit and reproduction detail.
