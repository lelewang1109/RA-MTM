# RA-MTM

Reference-Anchored Merge Tree Maps (RA-MTM) is a research prototype for preserving fixed spatial reference, absolute feature size, and true motion in temporal merge-tree maps. The repository includes audited Python reproductions of TMTM and ST-MTM for controlled comparison.

This repository is organized as a paper-reproduction project: method code, experiment logic, generated data, results, and documentation have separate responsibilities. Start with the [project structure and workflow](docs/PROJECT_STRUCTURE.md), then read the [full experiment report](docs/EXPERIMENT_REPORT.md).

## Repository layout

```text
src/ramtm/            RA-MTM method and baseline implementations
experiments/          Independent, reproducible experiment suites
data/generated/       Generated experiment inputs; not committed
data/real/            Optional local real-world data; not committed
results/              Figures, tables, records, and local numerical arrays
docs/                 Experiment report and paper workflow
references/           Reference provenance; PDFs remain local
```

Local-only material such as `archive/`, paper PDFs, datasets, environments, caches, and large numerical arrays is excluded from Git.

## Setup

Python 3.9 or newer is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Reproduce all controlled experiments

```bash
./scripts/run_all.sh
```

Individual suites:

```bash
./experiments/synthetic_1d/run_pipeline.sh
python experiments/gaussian_2d/run_experiment.py
```

No external dataset is downloaded. The scripts create controlled inputs under `data/generated/<experiment>/` and write matching outputs under `results/<experiment>/`.

## Result organization

Each experiment result directory uses the same layout:

```text
figures/   paper figures, diagnostics, and animations
tables/    metrics, trajectories, ablations, and validation tables
records/   parameters, certificates, intermediate records, and summaries
arrays/    large reproducible NPZ arrays; kept local and excluded from Git
```

## Main code entry points

- `src/ramtm/error_budget.py`: hierarchy-compatible RA-MTM layout and error-budget solver.
- `src/ramtm/reference_anchored.py`: fixed-reference full-map renderer.
- `src/ramtm/baselines/tmtm.py`: TMTM reproduction.
- `src/ramtm/baselines/stmtm.py`: ST-MTM reproduction.
- `experiments/synthetic_1d/verify.py`: analytic and regression verification.

The checked-in results correspond to the controlled study documented on 2026-09-18. They support a mechanism study, not a comprehensive production-system or real-world benchmark claim.
