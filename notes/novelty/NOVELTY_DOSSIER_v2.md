# Novelty Dossier v2 — reframed paper (PacificVis 2027 conference track)

You are an expert reviewer in topology-based scientific visualization, graph drawing / layout algorithms, and information visualization. Judge the novelty of the REFRAMED paper below, search further on your own wherever you can (especially 2024–2026 work and anything citing Temporal Merge Tree Maps), and answer the questions at the end. Earlier review (run01, same repository, `.aris/traces/novelty-check/2026-09-26_run01/`) judged the earlier "task-referenced map" idea PROCEED 7/10; the framing has since changed, and new prototype evidence exists (see `notes/2026-09-26-*.md` and `prototypes/` in this repository — you may read them).

## Reframed paper

Working title: *How Faithful Can a Merge Tree Map Be? Certified Position–Topology Trade-offs in Static Visualizations of Time-Varying Scalar Fields.*

Research question: merge-tree-based static space–time maps (TMTM, ST-MTM) compress each 2-D time step to a 1-D column while preserving the merge tree. How faithful to spatial position can such a map be at all, and can the unfaithful part be proved, located and controlled?

Claims:
1. **Fidelity model.** Merge-tree space–time maps are hierarchy-constrained 1-D interval layouts; three fidelities: topology (merge-tree identity), position along a reference coordinate, absolute size (width ∝ measure). TMTM, ST-MTM and reference-anchored variants occupy different points.
2. **Certificate.** Per frame, τ* = exact minimum of max_i |u_i − q_i| over all layouts that keep every merge-tree subtree's leaves contiguous, use widths w_i = c·A_i, a minimum gap, a fixed canvas and bounded anchor eccentricity. For a fixed leaf order τ* has a closed form (chain with box windows: max of three pairwise/prefix expressions; verified against LP to 1e-14); minimised over hierarchy-consistent orders. Decomposition: hierarchy cost τ_hier − τ_free (τ_free = same problem without contiguity) vs. space cost τ_free.
3. **Controlled trade-off.** Certificate-driven local relaxation: only in frames with hierarchy cost > θ (θ = 2% of axis, one global legibility constant), flatten merge nodes weakest-first (smallest |f(v) − f(parent)|, i.e. persistence order) until hierarchy cost ≤ θ. Topology cost measured on the rendered 1-D map as max over leaf pairs of |1-D merge level − true LCA value| — this equals the ℓ∞-cophenetic distance between the labeled input merge tree and the labeled merge tree of the 1-D map, i.e. the labeled interleaving distance (Munch & Stefanou). Sweeping a cap on this cost gives a position-vs-topology trade-off curve per dataset.
4. **Empirical finding.** ERA5 MSLP over Europe (Nov 1999–Jan 2000, 118 frames): hierarchy cost > θ in 58% of frames (up to 31% of axis); relaxation lowers mean position error 60% but changes merge levels of 10% of leaf pairs (mean 13 hPa, max 58 hPa); within a 2% value cap only −9%; a 42% reduction needs up to 27.8 hPa (halving needs 28–43 hPa). Ring (synthetic): conflicts are cheap (−18% at 2% cap). Consequence for the whole family: on real weather data position fidelity and merge-tree fidelity strongly conflict.
5. **Parameter-free defaults.** Reference direction chosen automatically as the principal direction of tracked extremum motion (captures 0.74 of motion on ERA5 vs 0.69 for fixed x); canvas-relative constants. (Negative results reported: automatic radial centres follow tracking artifacts; a stability-priority conflict policy does not generalise; per-feature disclosure ticks are illegible on ERA5.)

Not claimed: new filling algorithm; superiority over ST-MTM on all metrics; a general impossibility theorem beyond the model; user-study findings.

## Candidate prior work (all existence-verified: 32 via CrossRef title match, 10 via direct arXiv/LIPIcs/publisher pages)

A. Merge-tree / linearization static maps
- Köpp & Weinkauf, Temporal Merge Tree Maps, TVCG 29(1) 2023.
- Spatiotemporal Merge Tree Maps (ST-MTM), C&G 2026 submission, SSRN 6604235 (preprint).
- Franke et al., Visual Analysis of Spatio-temporal Phenomena with 1D Projections, CGF 2021.
- Zhou, Johnson, Weiskopf, Data-driven space-filling curves, TVCG 2021.
- Hovmöller diagrams (1949) and radius–time diagrams (meteorology).
B. 1-D movement summaries
- Buchmüller et al., MotionRugs, TVCG 2019; SpatialRugs (arXiv 2003.12282); Wulms et al., Stable Visual Summaries for Trajectory Collections, PacificVis 2021.
- **Stolk, Wulms, Verbeek, GroupRugs: Visual Summaries for Groups in Collective Movement Data, PacificVis 2025** — groups mapped to contiguous pixel strips, orders within groups from DR, spatial quality (neighbourhood-based) / stability / expressiveness metrics, crossing minimisation by IP; no metric reference positions, no lower bound, no merge levels.
- Valdrighi et al., MoReVis, TVCG 2024.
- Rauscher et al., Visually Assessing 1-D Orderings of Contiguous Spatial Polygons, CGF 2025; Rauscher et al., Visual Boosting Techniques for Spatiotemporal Dense Pixel Visualizations, EuroVA 2026 / arXiv 2604.25298.
- Andrienko et al., Space Transformation for Understanding Group Movement, TVCG 2013.
C. Topology-based temporal / tree layouts
- Köpp & Weinkauf, Temporal Treemaps, TVCG 2019; Dobler & Nöllenburg, Improving Temporal Treemaps by Minimizing Crossings, CGF 2024; Lukasczyk et al., Nested Tracking Graphs, CGF 2017.
- Weber, Bremer, Pascucci, Topological Landscapes, TVCG 2007; Beketayev et al., Geometry-Preserving Topological Landscapes, WASA 2012.
- Heine et al., Drawing Contour Trees in the Plane, TVCG 2011; Lohfink et al., Fuzzy Contour Trees, CGF 2020.
- Analyzing Time-Varying Scalar Fields using PL Morse–Cerf Theory, VIS 2025.
D. Merge-tree distances (for the topology-cost metric)
- Morozov, Beketayev, Weber, Interleaving Distance between Merge Trees, 2013.
- Munch & Stefanou, The ℓ∞-Cophenetic Metric for Phylogenetic Trees as an Interleaving Distance, 2019.
- Gasparovic et al., Intrinsic Interleaving Distance for Merge Trees, La Matematica 2024.
- Yan et al., Geometry-Aware Merge Tree Comparisons … Interleaving Distances, TVCG 2022/2023.
- ParkView: Visualizing Monotone Interleavings, PacificVis 2025.
- Locally Correct Interleavings Between Merge Trees, SoCG 2026; A Practical Algorithm for (Geometry-Aware) Interleavings Between Merge Trees, SEA 2026.
E. 1-D placement / ordering algorithms
- Li & Wang, Separating Overlapped Intervals on a Line, JoCG 2019 (min-max displacement, O(n log n), free order).
- Dwyer, Koren, Marriott, IPSep-CoLa (separation-constraint QP), TVCG 2006.
- Bar-Joseph et al., Fast Optimal Leaf Ordering, 2001; Brusco & Stahl, Optimal least-squares unidimensional scaling, Psychometrika 2005 (UDS/seriation NP-hard).
- Bulteau, Gambette, Seminck, Reordering a Tree According to an Order on Its Leaves, CPM 2022.
- Huson, Displacement-Optimized Tanglegrams, MBE 2026.
- Klawitter et al., Visualizing Geophylogenies – Internal and External Labeling with Phylogenetic Tree Constraints, GIScience 2023 / JGAA 2025; Paged Geophylogenies, arXiv 2607.23559 (2026) — tree-constrained leaf order vs. map sites; objectives are leader crossings.
- Versatile Ordering Network, VIS 2025.
F. Trade-offs / guarantees in map-like layouts
- Wood & Dykes, Spatially Ordered Treemaps, TVCG 2008; Treemaps with Bounded Aspect Ratio (CGTA 2014).
- van Beusekom, Meulemans, Speckmann, Wood, Data-Spatial Layouts for Grid Maps, GIScience 2023 (gradual spatial↔data trade-off).
- Nusrat & Kobourov, The State of the Art in Cartograms, CGF 2016 (area vs shape vs topology errors).
G. Distortion visualization and design theory
- Aupetit, Visualizing distortions and recovering topology in continuous projection techniques, 2007; CheckViz (2011).
- Kindlmann & Scheidegger, An Algebraic Process for Visualization Design, TVCG 2014.

## Questions
1. Is the reframed paper novel? For each claim 1–5: closest prior work, delta, and whether any named published paper already contains it.
2. Is there any paper that computes an exact or provable lower bound on positional/geometric distortion for hierarchy- or group-constrained 1-D layouts (in any field: vis, graph drawing, labeling, phylogenetics, seriation)? Name it precisely if so.
3. Is there any paper that quantifies a position-vs-topology (or geometry-vs-hierarchy) trade-off curve for merge/contour-tree layouts or for 1-D spatiotemporal summaries?
4. Is identifying the rendered-map topology cost with the ℓ∞-cophenetic / labeled interleaving distance correct and already used for evaluating layouts/linearizations anywhere?
5. Which prior works are MISSING from this list that a PacificVis reviewer would expect to be cited or compared against? Search broadly (e.g., works citing TMTM; storyline layout with geography; hierarchical clustering display with positions; tanglegrams; labeling; treemap/cartogram trade-offs; persistence simplification).
6. Is the "finding" (claim 4) publishable as a contribution at PacificVis, and what evidence would make it robust (robustness to θ, reference direction, time step, simplification)?
7. Report: per-claim closest/delta; closest-prior-work table; score X/10; PROCEED / PROCEED WITH CAUTION / ABANDON; key differentiator; risk; one-sentence positioning; and a recommended list of must-cite papers grouped by related-work subsection.

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
