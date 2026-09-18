# Synthetic 1-D / polyline study

The pipeline runs in this order:

1. `run_experiments.py` generates controlled inputs and runs TMTM, ST-MTM, and RA-MTM.
2. `verify.py` performs analytic, regression, and scalar-topology checks.
3. `sensitivity.py` runs the parameter and centroid-perturbation study.
4. `ablation.py` evaluates width and temporal-objective ablations.
5. `finalize.py` validates required artifacts and writes the manifest.

Run all five stages with:

```bash
./experiments/synthetic_1d/run_pipeline.sh
```

