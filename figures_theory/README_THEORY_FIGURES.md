> 历史单轴概念图；当前XY方法以 [方法流程](../docs/XY_METHOD.md) 为准。

# RA-MTM Theory Figures

All geometry and numerical values in these figures are schematic and are not experimental results. Regenerate every file with `python figures_theory/draw_theory_figures.py`.

## Theory-1 — Merge Tree Map basic pipeline

- Explains the background pipeline from a spatial scalar field to a static temporal map.
- Panels show the 2D field, augmented merge tree, tree-guided 1D linearization, and stacked time steps.
- Corresponds to the shared tree/linearization context used by the baseline and RA-MTM renderers; it is not an RA-MTM contribution claim.

## Theory-2 — Information missing from existing encodings

- Motivates RA-MTM through common translation, common growth, and hierarchy conflict.
- Panels contrast invariant pairwise distances, fixed-total-width normalization, and an illegal direct reference layout.
- Corresponds to `q_i`, absolute `A_i`, `w_i`, legal leaf orders, and interval feasibility in `error_budget.py`.

## Theory-3 — RA-MTM variables and constraints

- Shows how `C_i` and `A_i` become `q_i`, `w_i`, layout variables `x_i`/`z_i`, and a fixed-world raster slice.
- Panels separate reference projection, absolute width, joint constraints, and rasterization.
- Corresponds to `solve_frame()` in `error_budget.py` and `render_sequence()` in `reference_anchored.py`.

## Theory-4 — Minimum feasible deviation and error budget

- Explains why `τ*` is the first tolerance that admits a hierarchy-valid, non-overlapping layout.
- Panels progress from `τ=0`, through infeasible `τ<τ*`, to `τ=τ*` and the expanded `τ*+Δ` feasible region.
- Corresponds to the LP lower bound and budget-constrained QP in `error_budget.solve_frame()`.
