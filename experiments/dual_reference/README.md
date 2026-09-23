# Dual-Reference RA-MTM

Additive evidence for feature-centroid X/Y references. The original 1D, Gaussian,
ERA5, Ring and exploratory JOLT studies remain in place. This package reruns all
18 original Gaussian sequences and seven new complete scalar-field cases; it
does not relabel historical ERA5/Ring results as dual-reference evidence.

```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python experiments/dual_reference/run_experiment.py
.venv/bin/python experiments/dual_reference/exact_mechanisms.py
.venv/bin/python experiments/dual_reference/verify.py
.venv/bin/python experiments/dual_reference/figures.py
.venv/bin/python experiments/dual_reference/finalize.py
.venv/bin/python experiments/dual_reference/manifest.py
.venv/bin/python experiments/dual_reference/manifest.py --verify
```

The protocol is saved before solving. Every declared case is retained. Parameters
match the existing Gaussian suite: beta=4, gamma=1, lambda=.5, eta=.1, rho=.5,
Delta=1, gap=.5, canvas=[0,120], c=.012. Baseline source/adapters are unchanged.
`baseline_snapshot.json` captures the working-tree baseline at the start of this
upgrade (including previous uncommitted fixes), not an older Git revision.

Mechanisms: pure X, pure Y, diagonal translation; same-X and same-Y crowding;
hierarchy conflict; simultaneous X/Y motion and growth/shrinkage. Grid centroids
are extracted, not generator means. Consequently nominal pure translations have
small quantization fluctuations off-axis. `exact_mechanisms.py` separately tests
exact feature-level translations and identical-axis coordinates; its summary
controls are not full scalar fields and cannot support TMTM comparisons.

Single-view methods do not provide native 2-D positions. Primary comparison gives
all three an explicitly favorable decoder `(x(t), true_y(0))`, with each feature's
initial Y held fixed. X calibration is the unchanged first-frame reflection and
translation with fixed native scale. A secondary decoder fits both coordinates
to the scalar anchor at t=0 and freezes that affine map. Neither uses future
truth; neither is a new baseline algorithm. All native 1-D geometry errors remain
reported. Dual uses `(anchor_X, anchor_Y)` directly, without fitted calibration.
Do not describe these oracle/affine readouts as native baseline 2-D capabilities.

Output: `results/dual_reference/{tables,records,figures,arrays}`. Numerical arrays
are local/reproducible; compact evidence, figures and certificates are tracked.
The independent manifest scopes this package only. It does not re-certify old
ERA5/Ring results against new shared source. See `docs/DUAL_REFERENCE_REPORT.md`
for formulas, all results, counterexamples, captions and claim boundaries.
