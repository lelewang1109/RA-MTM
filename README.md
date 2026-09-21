# RA-MTM

**Reference-Anchored Merge Tree Maps** is a research prototype for temporal scalar-field maps with fixed spatial references, absolute feature measures, hierarchy legality, and explicit reference-error budgets. The repository includes paper-based TMTM/ST-MTM reproductions and a controlled evidence suite.

## Start here

- [Method and evidence report](docs/EXPERIMENT_REPORT.md): formulas, evaluation protocol, results, limitations, and claim boundaries.
- [Project structure and reproduction](docs/PROJECT_STRUCTURE.md): directory ownership, clean-run workflow, artifact policy, and update rules.
- [Theory figures](figures_theory/README_THEORY_FIGURES.md): four schematic method figures and their reproducible drawing script.
- [Formal evidence package](results/README.md): the current paper tables, figures, ablations, sensitivity analyses, validity checks, and full supplementary records.

## Reproduce the formal evidence package

Python 3.10 or newer is required. From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
PYTHON_RUNNER=.venv/bin/python ./scripts/run_all.sh
.venv/bin/python scripts/manifest.py --verify
```

The production runner is clean and fail-fast. Before a new run, it moves the previous `results/` and `data/generated/` into a local `archive/before_run_*` snapshot, then regenerates the complete evidence package. A valid published run must have `results/run_status.json` set to `complete` and pass manifest verification.

## Repository map

```text
src/ramtm/          RA-MTM, baseline implementations, and shared evaluation
experiments/        1D/2D studies, validation studies, and publication assembly
scripts/            complete-run orchestration and manifest verification
results/            one categorized formal evidence package
figures_theory/     schematic method figures; not numerical evidence
docs/               the method/evidence report and reproduction guide
data/               policy file; generated and real data stay local
references/         provenance metadata; paper PDFs stay local
archive/            previous runs and historical material; local only
```

`results/` separates `main`, `auxiliary`, `ablation`, `sensitivity`, `validity`, and `supplementary` evidence. Large numerical arrays are reproducible but excluded from Git; compact tables, figures, validation records, and the final manifest are tracked.

## Evidence boundary

The current evidence covers 1D/polyline mechanisms and 2D Gaussian/envelope and analytic advection–diffusion fields, including hierarchy-change and crowding cases. It supports controlled encoding claims; it does not establish universal geometric superiority, large-tree scalability, real-world generalization, or the independent usefulness of every temporal term.
