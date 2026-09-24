> 已停止的探索分支，不属于当前 XY 方法。失败结论及所有结果保留。

# JOLT-MTM small-tree pilot

Working name: **Joint Ordering and Layout over Time Merge Tree Maps**.
This is an exploratory oracle/pilot, not a validated replacement method.

Run from the repository root:

```sh
.venv/bin/python experiments/history/jolt_mtm/run_pilot.py
.venv/bin/python experiments/history/jolt_mtm/verify_pilot.py
```

Outputs live only in `results/exploratory/jolt_mtm/`. Existing methods, inputs,
formal results and the production runner are not modified.

## Protocol fixed before the first pilot run

- Unchanged author-generated Ring, 40 frames, shared existing trees and matching.
- Enumerate **all** legal binary leaf orders, including reflections.
- Branch A: retain paper 1's sample allocation; enumerate every subtree flip.
  Test per-frame geometry headroom and exact candidate-path minimization of
  paper 1's original full-subtree overlap objective.
- Branch B: for each order solve uniform raw stress with the paper Ring minimum
  gap, without temporal anchoring. Nonnegative least squares on adjacent gaps
  solves this convex problem. Also solve the zero-gap relaxation: exhaustively
  enumerating its cones gives the SNS infimum, not a TW optimum or a valid map
  with distinct anchors. Check primal/dual KKT residuals.
- Causal control: enumerate orders with the **same previous ST baseline frame**
  and its temporal objective. This isolates order choice from removing temporal
  anchoring; it is not a recursively executed new method.
- For temporal path search, include the original ST baseline at every frame.
  Candidates comprise all Branch B layouts and all causal-control layouts.
  Screen each frame by SNS <= ST, TW(k=1,3) >= ST wherever defined, and fixed-unit
  distance SSE <= ST. No per-frame fitted scale is used for distance dynamics.
  Minimize summed squared errors in changes of matched pairwise distances by DP.
  The original baseline path guarantees nonempty candidate sets. This is exact
  only within these fixed candidates, not joint continuous/discrete optimality.
- Report SNS over all 40 frames and separately frames with >=2 leaves;
  TW coverage, fixed-unit distance error, pair-distance-change error, TD, and
  actual render validation at **196 samples**. SNS uses its definition's fitted
  scale; temporal distances do not. Dynamic matching is estimated, not truth.
- Re-render selected candidates with the unchanged ST allocation/filling rules.
  Report post-raster metrics and topology separately; no resolution fallback.
  Branch B inherits ST's relative widths, not TMTM's absolute-count guarantee.

## Decision rules (exploratory, not statistical significance)

Continue a geometry-focused follow-up only if a realizable candidate sequence
reduces mean SNS by at least 5% vs ST, does not lower either reported TW, and does
not increase pair-distance-change error, with all 196-sample topology checks
passing. Continuous gains alone do not establish display-quality gains.

If this fails but guarded DP reduces distance-change RMSE by >=10%, retain a
**temporal-only lead**, not a claim of spatial superiority. If even exhaustive
orders yield <5% SNS headroom, stop expanding the ordering-only geometry route
on this dataset. Failure to find joint SNS/TW improvements among fitted layouts
is not proof that all continuous layouts are infeasible.

No claim of significance, multi-dataset generalization, absolute position
improvement, or guaranteed strict superiority is made from this one pilot.

## Explicit secondary diagnostic (added after first results)

The first pilot's JOLT-Guarded path improved distance-change error but increased
TD. Its pair-distance objective is blind to translation/reflection. Therefore
`JOLT-TD-Guarded` additionally rejects each transition whose summed matched TD
exceeds the corresponding ST baseline transition. The baseline path remains
feasible. This diagnostic is reported separately and is excluded from the
original geometry acceptance gate; it does not replace the failed first result.
