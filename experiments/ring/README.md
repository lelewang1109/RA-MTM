# Ring experiment

Run from the project root:

```sh
.venv/bin/python experiments/ring/run_experiment.py
.venv/bin/python experiments/ring/verify.py
```

This dataset adapter uses `scene_from_fields`, `run_method`, and `evaluate` from
the existing ERA5/Storms three-method pipeline. The production `run_all.py`
includes both commands. No Franke projection method is used.

## Data provenance

The initial project search found the Ring generator in the already-local
`archive/paper1_author_reference.zip`. Its audited upstream revision is
`Wiebke/TemporalMergeTreeMaps@2c75a10ed2cd55177a25ff751e0c0a8261200717`.
The original generator and the relevant workspace processor element are retained
under `source/`; generator defaults and workspace time-step count are parsed,
not guessed. These are the TMTM authors' implementation of Franke et al.'s
synthetic expanding Ring. The requested Franke repository was inspected, but
direct downloads failed due to DNS; the data are **not claimed to be a downloaded
Franke data file**.

The formula is `(1+0.3t) exp(-0.5 ((d-1.94t)/(12.16+0.05t))^2)`, where `d` is
distance from `(30.4,40.6)`. Each axis has 14 endpoint-inclusive samples on
`[0,210]`; `t=0,...,39`. Inviwo FloatProperty values and output fields use float32.
`provenance.json` records declared and actual floating-point values, code hashes,
array orientation and SHA256. The adapter removes only Inviwo memory repacking;
it does not interpolate or modify scalar values.

## Shared comparison conditions

- One `(40,14,14)` finite array, one split-tree extraction, one set of leaf-arc
  supports/centroids, and one positive-overlap Hungarian correspondence sequence.
- The existing deterministic Freudenthal grid builder is used for all methods.
  This is the project's paper-based Python reproduction, not an official TTK run.
- `p=.001` is audited against every finite elder-rule persistence pair as a
  fraction of the per-frame scalar range. All pairs exceed the threshold, so
  cancellation is a certified no-op. A future input that requires cancellation
  fails instead of silently proceeding. The paper's threshold normalization is
  not fully specified; this preserves the existing Storms interpretation.
- ST-MTM temporal mode: uniform, K=1, r=.95, lambda=1.5, L=196, Start=0;
  alpha/delta/solver defaults come unchanged from the baseline preset API.
- RA-MTM keeps the Storms dimensionless weights. Canvas, gap and extra reference
  budget are converted by `210/120` to source-coordinate units. The same
  fixed-domain capacity rule allocates half the canvas to the entire domain;
  equal sample measures are `210^2/196`, and width scale is `1/(2*210)`.
  The reference correction described below changes rho from .5 to 1; this is
  an explicit method revision, not a claim of unchanged RA-MTM parameters.
- TMTM output indices are converted by the fixed domain span `210/195`.
  Baselines retain the existing one-time first-frame reflection/translation.
  There is no per-frame scale fitting for TD or task metrics. SNS itself fits
  scale by definition.
- SNS is averaged over 40 frames, with the existing zero convention for a
  single feature. TW uses paper/Storms k=3 and is defined only at t=23,34,39.
  Undefined frames are blank. Supplemental k=1 is recorded separately.
  TD sums all 146 shared matched-pair displacements in common source units.
- Runtime is the median of three cyclic-order wall-clock measurements of layout
  and scalar rendering. Shared extraction, verification, evaluation, plotting
  and disk I/O are excluded. Each recorded timing includes any actual rendering
  fallback, so additional work for RA-MTM is not hidden.

## Raster capacity and interpretation

TMTM and ST-MTM retain 196 samples. ST-MTM has some zero geometric interval
extents (one-pixel intervals) in every frame at this resolution. No ST parameter
or L is changed. RA-MTM's unchanged renderer rejects 196 and 392 samples; the
existing doubling policy first succeeds at 784. All three final maps pass the
leaf/branch scalar topology check. Pixel collapse is recorded separately and is
not called a positive-width success.

Primary metrics evaluate continuous feature anchors in shared physical units;
the figure labels native resolution explicitly. This is **not an equal-raster-
budget visual comparison** or a claim to reproduce the paper's numerical table.
`validity.csv` and method records retain raster attempts and quantization errors.
No output-dependent data changes, parameter sweeps or selected best runs occur.

## Reference correction (2026-09-23)

At t=7→8 the surviving peak remains at the same grid sample, while its leaf-arc
support falls from 195 samples to 2. Treating the support centroid as a physical
position produced an 88.31-unit false displacement. The full-field RA-MTM runner
now uses the extremum's world x coordinate as a separate reference and uses its
displacement in the residual temporal term. Shared centroid geometry is still
used for pairwise distances and all original evaluation metrics.

An extremum can be off-center within its support. The anchor is therefore allowed
anywhere inside its own interval (rho=1), rather than the old central-half
restriction (rho=.5). Absolute widths, reference budget, objective weights and
renderer are unchanged. Shared support IoU weights the temporal penalty, without
renormalizing a weak correspondence to full strength. Shared matching is unchanged;
low IoU alone does not prove an identity is wrong, particularly at a split.

This changes only RA-MTM's use of the shared information; it does not redefine
the inputs or benchmarks in its favor. Legacy centroid reference-error metrics
remain in `all_metrics.csv`; `extremum_reference_nmae` is an additional metric
computed for every method. `verify_reference_fix.py` reproduces the old RA-MTM
path, checks actual before/after artifacts when available, tests stationary and
translated references, checks gradients, and generates `ring_reference_fix.png`.
Coarse-grid extrema switches and hierarchy conflicts remain possible; the fix
does not promise continuous trajectories or improved aggregate TD. Prior ERA5
evidence has not been rerun as a complete study for this method revision.

## Artifacts

- `data/generated/ring/ring.npz`: fields `(time,y,x)`, coordinates and time ids.
- `data/generated/ring/shared_trees.json`: neutral trees used by all methods.
- `results/main/ring_metrics.csv`: requested three-row table.
- `results/main/figures/ring_*.png`: original fields, three maps, feature counts.
- `results/supplementary/ring/`: all metrics, per-frame values, tracking,
  repeated timings, method certificates, native maps, provenance and validity.

The Ring manifest certifies this run's own source/data/output closure. It does
not update provenance of previous ERA5 or synthetic runs after shared-source
changes; the full production runner regenerates those packages when requested.
