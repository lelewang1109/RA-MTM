# Novelty Dossier — task-referenced merge tree maps

You are an expert reviewer in scientific visualization (topology-based vis, time-varying scalar fields) and information visualization (1D projections, storylines, treemaps). Judge novelty of the proposed method below against the candidate prior work, then answer the questions at the end. You may search further if you can; flag any additional paper you believe is closer than those listed.

## Context: the existing line of work

- **TMTM** — Köpp & Weinkauf, "Temporal Merge Tree Maps: A Topology-Based Static Visualization for Temporal Scalar Data", IEEE TVCG 29(1) 2023 (VIS 2022). Linearizes each time step of a 2D/3D scalar field via DFS of the augmented merge tree (all samples placed; 1D field has the same merge tree = "Merge Tree Identity"); greedy choice of child order at each saddle to match subtree overlaps between consecutive time steps; time on x-axis. The vertical axis has no geometric meaning.
- **ST-MTM** — "Spatiotemporal Merge Tree Maps: A Topology and Geometry Aware Visualization for Temporal Scalar Data", Computers & Graphics 2026, SSRN preprint 6604235 (not peer reviewed). Leaf order by optimal leaf ordering on centroid distances (+ Kendall-tau concordance with previous order, threshold r); 1D anchors by weighted stress on centroid distances with λ-anchoring to previous positions; interval widths proportional to size^α with fixed total K; global min-max rescale + padding; leaf-interval filling and LCA-based hierarchical gap filling. Vertical axis encodes *relative* distances only; no units.
- **RA-MTM (our current prototype)** — fixed world reference: each leaf's extremum is projected on a fixed world axis (X, and separately Y → two maps). Two-stage solve per frame: (1) over all hierarchy-consistent leaf orders, an LP gives τ* = min max_i |u_i − q_i| subject to non-overlap with gap g, absolute widths w_i = c·A_i (c fixed over time), anchor-eccentricity |u_i − z_i| ≤ ρ w_i/2, fixed canvas; (2) with |u_i − q_i| ≤ τ* + Δ, a QP minimizes reference error + centroid-distance stress + motion residual ((u_t − u_{t−1}) − (q_t − q_{t−1}))² + eccentricity. ST-MTM filling reused. Current leaf-order search = full enumeration (exponential in #internal nodes); per-frame causal.

## Proposed method (to be judged)

**Task-referenced merge tree maps (a "topology-preserving generalized Hovmöller diagram").** A single static space–time map of a time-varying scalar field in which the 1D spatial axis is a *task-defined, unit-bearing reference coordinate* φ evaluated at each merge-tree leaf feature: q_i = φ(R_i, t), where φ can be a direction projection (longitude/latitude → classic Hovmöller-like), **radial distance from a centre**, **distance to a user-selected focus feature** (egocentric; e.g., every low's distance to cyclone Lothar), or **along-path/geodesic distance** (e.g., along a storm track or coastline). Unlike meteorological Hovmöller / radius–time diagrams, which average over the orthogonal dimension(s) and so dissolve features, this keeps every sample, the merge-tree hierarchy (features stay contiguous, nesting preserved), and absolute feature size, and reports a per-frame **certificate τ*** of the minimum reference deviation forced by hierarchy/width/canvas constraints. The deviation (τ*, per-feature |u_i − q_i|) is **drawn in the map** so readers know where the axis can be trusted. Because the axis has absolute units, maps of different ensemble members / time windows / datasets become **directly comparable**, which TMTM/ST-MTM axes are not.

Secondary technical contributions:
- A scalable algorithm replacing enumeration: binary search on τ with a tree-DP feasibility test for "hierarchy-constrained interval placement with target windows" (akin to scheduling with release/deadline windows under tree-shaped contiguity constraints), aiming for polynomial time.
- Temporal global optimization over per-frame candidate leaf orders via Viterbi/DP with switching cost (instead of greedy forward/backward propagation used by TMTM and ST-MTM).

## Core claims

1. C1 — Topology-preserving (merge-tree-based, all samples, hierarchy-contiguous) space–time map whose spatial axis is an arbitrary task-defined *absolute* reference coordinate (radial, focus-relative, along-path, directional). Framed as generalized Hovmöller diagrams that do not average features away.
2. C2 — Two-stage LP (min–max reference deviation over hierarchy-consistent orders) + budgeted QP, yielding a per-frame certificate τ* of unavoidable deviation.
3. C3 — Visualizing that certificate / per-feature deviation inside the map.
4. C4 — Cross-map comparability (ensembles, windows) enabled by the absolute axis.
5. C5 — Tree-DP / binary-search algorithm for the hierarchy-constrained min–max placement, and Viterbi temporal optimization of leaf orders for merge tree maps.

## Candidate prior work found (Phase B)

Status: all found in live web search with publisher/arXiv URLs; automated verify_papers.py hit transient API failures (2/19 resolved, 0 flagged as hallucinated).

| # | Paper | Venue/Year | URL | Why relevant |
|---|---|---|---|---|
| P1 | Köpp & Weinkauf, Temporal Merge Tree Maps | TVCG 2023 | https://ieeexplore.ieee.org/document/9903344/ | Base method; no geometric axis |
| P2 | Spatiotemporal Merge Tree Maps | C&G 2026 preprint (SSRN 6604235) | — | Relative-distance axis; OLO + stress; fixed total width |
| P3 | Franke, Martin, Koch, Kurzhals, Visual Analysis of Spatio-temporal Phenomena with 1D Projections | CGF 40(3) 2021 | https://onlinelibrary.wiley.com/doi/10.1111/cgf.14311 | Selection of 1D projections (Hilbert/Morton, distance-based clustering, hierarchical); no merge-tree features |
| P4 | Buchmüller et al., MotionRugs | TVCG 2019 | https://doi.org/10.1109/tvcg.2018.2865049 | 1D ordering per time step for collective movement |
| P5 | Wulms et al., Stable Visual Summaries for Trajectory Collections | PacificVis 2021 | https://arxiv.org/pdf/1912.00719 | Stable principal components: projection on smoothly varying axis |
| P6 | SpatialRugs | C&G 2021 | https://www.sciencedirect.com/science/article/abs/pii/S0097849321001679 | Encodes 2D location by colour in 1D-ordered time–space view |
| P7 | MoReVis: A Visual Summary for Spatiotemporal Moving Regions | TVCG 2023 | https://arxiv.org/pdf/2302.13199 | 1D summary with layout optimization of mark size/position to resemble original space |
| P8 | Rauscher, Dennig, Schlegel, Keim, Schreck, Visual Boosting Techniques for Spatiotemporal Dense Pixel Visualizations | arXiv 2604.25298 (2026) | https://arxiv.org/html/2604.25298 | Visualizes distortion artifacts of 1D orderings (hatching, halos, glyphs); polygons, no topology |
| P9 | Rauscher et al., Visually Assessing 1-D Orderings of Contiguous Spatial Polygons | CGF 2025 | https://onlinelibrary.wiley.com/doi/10.1111/cgf.70100 | Quality assessment of 1D orderings |
| P10 | Wood & Dykes, Spatially Ordered Treemaps | TVCG 2008 | https://openaccess.city.ac.uk/536/ | Hierarchy-constrained layout that preserves geographic position (2D treemap) |
| P11 | Köpp & Weinkauf, Temporal Treemaps | TVCG 2019 | https://wiebke.github.io/files/koepp18.pdf | Static layout of evolving trees, global optimization (simulated annealing) |
| P12 | Lukasczyk et al., Nested Tracking Graphs | CGF 2017 | https://www.researchgate.net/publication/318201789_Nested_Tracking_Graphs | Hierarchical feature evolution layout |
| P13 | Dobler et al., Improving Temporal Treemaps by Minimizing Crossings | CGF 2024 | https://onlinelibrary.wiley.com/doi/10.1111/cgf.15087 | Exact/engineered optimization for temporal tree layouts |
| P14 | Zhang, Chen, Yong, Stratiline | C&G 2025 | https://www.sciencedirect.com/science/article/abs/pii/S0097849325000056 | Storyline whose y-axis encodes location accurately via 1D location sorting |
| P15 | Geo-Storylines: Integrating Maps Into Storyline Visualizations | 2022 | https://www.researchgate.net/publication/364370141 | Location-aware storylines |
| P16 | Zhou, Johnson, Weiskopf, Data-driven space-filling curves | TVCG 2021 | https://doi.org/10.1109/TVCG.2020.3030473 | Data-aware linearization |
| P17 | Yan et al., Geometry-Aware Merge Tree Comparisons for Time-Varying Data with Interleaving Distances | TVCG 2022 | https://arxiv.org/abs/2107.14373 | Geometry-aware merge tree comparison (not layout) |
| P18 | Topology-Based Feature Design and Tracking for Multi-Center Cyclones | arXiv 2011.08676 | https://arxiv.org/pdf/2011.08676 | Topological cyclone tracking |
| P19 | Hovmöller diagrams incl. radius–time (azimuthal-mean) diagrams for tropical cyclones | meteorology practice since 1949 | https://www.climate.gov/news-features/understanding-climate/hovm%C3%B6ller-diagram-climate-scientist%E2%80%99s-best-friend | Axis-reference × time, but averages over other dimension |
| P20 | Brucker, Garey, Johnson, Scheduling Equal-Length Tasks Under Treelike Precedence Constraints to Minimize Maximum Lateness | Math. OR 1977 | https://pubsonline.informs.org/doi/10.1287/moor.2.3.275 | Algorithmic neighbour for C5 |
| P21 | Bar-Joseph et al., Fast optimal leaf ordering | Bioinformatics 2001 | — | OLO DP over binary tree flips (C5 neighbour) |

## Questions

1. Is this method novel? For each claim C1–C5, what is the closest prior work and what is the delta?
2. Is any of C1–C5 already contained in a specific published paper? Name it precisely.
3. Is the *combination* (topology-preserving + task-defined absolute axis + certificate + comparability) novel even if parts are known?
4. What would a TVCG/EuroVis reviewer cite as the strongest objection, and what positioning survives it?
5. Which claim should be the headline and which should be demoted?
6. Give the report in the format: per-claim closest/delta; closest-prior-work table; score X/10; PROCEED / PROCEED WITH CAUTION / ABANDON; key differentiator; risk; one-sentence positioning.

=== NOVELTY VERDICT LIMITS (these bound how you judge, never how widely you search) ===
Search exhaustively; judge calibrated. Two failures waste months equally:
passing an idea a published paper already contains, and killing a viable idea
because the territory has neighbors.
1. Proximity is information, not a verdict. Someone working nearby goes in the
   report; it is not by itself a reason to reject.
2. ABANDON has exactly one qualification: a specific published paper already
   contains this result — name that paper. No named paper, no ABANDON.
3. Crowded-but-deltaed is PROCEED: state the delta in one sentence a reviewer
   could verify. Thin or contested delta is PROCEED WITH CAUTION — say what
   would make it carry, not why it should die. CAUTION is not a safe middle:
   if you cannot name the specific thing that makes the delta thin, the
   verdict is PROCEED.
4. Concurrent or competing work is not a veto. That is a race — report it and
   let the user decide whether to run it.
5. A direct attack on a central problem is legitimate novelty when nobody has
   executed it well. "This area is hot" does not mean "this area is taken."
6. This check is an early gate, never the last one — more triage, pilots, or
   external review still stand between any idea and a paper, whatever order
   this run uses. A wrongly passed idea dies cheaply at one of them; a wrongly
   killed idea is never seen again. When torn between two verdicts, choose the
   more permissive one.
Say plainly when an idea clears the check. Do not manufacture overlap.
