# RA-MTM

**Reference-Anchored Merge Tree Maps** preserves feature-level absolute spatial references through complementary fixed-axis projections. The dual-reference extension produces aligned X-time and Y-time maps with absolute feature measures, hierarchy legality, and explicit reference-error budgets. The repository includes paper-based TMTM/ST-MTM reproductions and controlled and ERA5 real-field evidence suites.

## Dual-reference upgrade

For a feature centroid $C_i$, each fixed unit direction $a_k$ defines
$q_i^{(k)}=a_k^T C_i$. X and Y use the **same solver**, independently computing
$\tau_x^*$ and $\tau_y^*$ and preserving $w_i=cA_i$ on a fixed world canvas.
The geometry term still measures original 2-D pairwise distances; the temporal
term is displayed motion minus true projected motion. No per-frame normalization.

The two anchors reconstruct $\hat C_i=(x_i^X,x_i^Y)$ for the **same feature ID**.
This is a feature-level 2-D position/trajectory estimate, not reconstruction of
full scalar-field geometry. Relative geometry, absolute projected reference,
and reconstructed feature position are distinct evaluation targets. The views
are complementary; neither 1-D view is a lossless 2-D embedding.

- [Upgrade report and all counterexamples](docs/DUAL_REFERENCE_REPORT.md)
- [Reproduce dual evidence](experiments/dual_reference/README.md)
- [Formal comparison](results/dual_reference/tables/metrics.csv)
- [Six publication figures](results/dual_reference/figures/)

```python
from ramtm.error_budget import Parameters, solve_dual_reference_sequence, solve_frame

# centers[t]: (features, 2); measures[t]: leaf-support area.
# track_ids[t] must identify rows consistently; frame-local vertex IDs are not tracks.
dual = solve_dual_reference_sequence(centers, measures, hierarchies,
    Parameters(width_scale=0.012), feature_ids=track_ids)
positions = dual["positions"]
# Any fixed nonzero direction is normalized; original 2-D geometry is unchanged.
view = solve_frame(centers[0], measures[0], hierarchies[0],
    reference_direction=(3, 4))
```

Default `solve_frame` / `solve_sequence` behavior remains X-only. For signed or
oblique projections, specify a fixed `Parameters(canvas_origin=..., canvas=...)`
from projected domain bounds, not per-frame feature extrema. `render_sequence`
uses that same origin and extent; `render_dual_reference_sequence` accepts both
views' parameters. Existing explicit `reference=` callers remain supported.

The new package contains 25 complete scalar sequences (7 new + all 18 canonical
variants), plus exact feature-level controls. ST-MTM often retains lower 1-D
geometry error; adding Y can introduce additional hierarchy/crowding conflict.
All outcomes, including worse dual-reference cases, are reported. Historical
ERA5 and Ring experiments remain single-reference evidence.

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

The current dual-reference upgrade is certified separately by
`experiments/dual_reference/manifest.py --verify`. Historical root/ERA5/Ring
manifests retain their original provenance and are not re-certified against this
new shared source without a full rerun.

The production runner is clean and fail-fast. Before a new run, it moves the previous `results/` and `data/generated/` into a local `archive/before_run_*` snapshot, then regenerates the complete evidence package. A valid published run must have `results/run_status.json` set to `complete` and pass manifest verification.

ERA5 is included automatically when `data/real/ERA5_MSLP/ERA5_MSLP_19991117_20000114.nc` is present. The source stays local; its SHA-256, metadata and preprocessing are recorded and verified. See the reproduction guide for running ERA5 alone.

The [Ring experiment](experiments/ring/README.md) is included in the production
runner and can also run independently. It reuses the Storms/ERA5 tree extraction,
three-method execution and evaluation pipeline, with the archived author Ring
generator and fixed paper ST-MTM preset. Its table is `results/main/ring_metrics.csv`.

## Repository map

```text
src/ramtm/          RA-MTM, baseline implementations, and shared evaluation
experiments/        1D/2D/ERA5 studies, validation, and publication assembly
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

The evidence covers controlled 1D/2D mechanisms and a full-period ERA5 mean-sea-level-pressure case with dynamic leaf matching. It measures encoding fidelity to extracted features, not independently validated cyclone trajectories. It does not establish universal geometric superiority, large-tree scalability, cross-season generalization, or the independent usefulness of every temporal term.
