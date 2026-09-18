# Experiment suites

Each experiment owns one input directory under `data/generated/` and one output directory under `results/`.

| Suite | Purpose | Entry point | Generated inputs | Results |
|---|---|---|---|---|
| `synthetic_1d` | Controlled 1-D and polyline mechanism study, regression checks, sensitivity, and ablation | `./experiments/synthetic_1d/run_pipeline.sh` | `data/generated/synthetic_1d/` | `results/synthetic_1d/` |
| `gaussian_2d` | 2-D Gaussian fields, extracted trees, full scalar maps, and topology validation | `python experiments/gaussian_2d/run_experiment.py` | `data/generated/gaussian_2d/` | `results/gaussian_2d/` |

Run both suites from the repository root with `./scripts/run_all.sh`.

