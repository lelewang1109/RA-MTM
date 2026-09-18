# MergeTreeMaps / RA-MTM

Reference-Anchored Merge Tree Maps (RA-MTM) is a research prototype for preserving fixed spatial reference, absolute feature size, and true motion in temporal merge-tree maps. The repository also contains audited Python reproductions of TMTM and ST-MTM used as baselines.

The current evidence is a controlled mechanism study rather than a production system or a comprehensive real-world benchmark. The full Chinese experiment report is in [EXPERIMENT_INITIAL_REPORT.md](EXPERIMENT_INITIAL_REPORT.md).

## Repository layout

```text
methods/                 RA-MTM layout, error budget, and rendering
baselines/               TMTM and ST-MTM Python reproductions
experiments/initial/     1-D / polyline controlled experiments and checks
experiments/gaussian2d/  2-D Gaussian-field experiments
results/                 Curated figures, metrics, and validation records
data/                    Local/generated inputs (not committed)
papers/                  Provenance metadata; local PDFs are not committed
archive/                 Local historical snapshots (not committed)
```

## Setup

Python 3.9 or newer is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Reproduce the experiments

Run the initial controlled suite:

```bash
./experiments/initial/run_all.sh
```

Run the 2-D Gaussian study:

```bash
python experiments/gaussian2d/run.py
```

Both suites generate their constructed inputs under `data/constructed/` and write outputs under `results/`. No external dataset is downloaded by these commands.

## Data and result policy

Input and generated datasets are intentionally excluded from Git. See [data/README.md](data/README.md) for the expected local layout. Large numerical result arrays (`.npz`) are also excluded; compact metrics, validation records, figures, and animations are versioned so the reported outcomes can be inspected without downloading the datasets.

## Main entry points

- `methods/reference_anchored_merge_tree_maps.py`: RA-MTM sequence solver and full-map renderer.
- `methods/error_budget.py`: hierarchy-compatible position-error budget solver.
- `baselines/temporal_merge_tree_maps.py`: TMTM reproduction.
- `baselines/spatiotemporal_merge_tree_maps.py`: ST-MTM reproduction.
- `experiments/initial/verify.py`: analytic and regression verification.

## Status

The checked-in results correspond to the experiment report dated 2026-09-18. Method assumptions, baseline reproduction details, limitations, and metric definitions are documented in the report.

