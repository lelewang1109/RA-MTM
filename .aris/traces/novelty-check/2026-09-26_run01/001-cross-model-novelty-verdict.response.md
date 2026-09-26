**Verdict: PROCEED. Novelty score: 7/10 for the combined research concept.**

The idea clears this early novelty check. I did **not** identify a specific published paper containing the complete combination of merge-tree-consistent layout, an externally specified coordinate with physical units, an optimal reference-deviation bound, and its visual communication.

The strongest contribution is **C1 and C2 together**. C3 has substantial prior art, C4 is principally a benefit to establish experimentally, and C5 remains an unproved algorithmic proposal. The score assesses novelty, not submission readiness.

I read the dossier, solver documentation, and implementation, and searched beyond the candidate list across visualization, interval separation, tree ordering, scheduling, and geographic reference transformations. Full-text access was uneven: in particular, I could verify ST-MTM’s SSRN record but could not retrieve its complete manuscript. Its detailed formulation below therefore follows the supplied dossier and repository documentation. This is a broad novelty assessment, not proof that no unindexed predecessor exists.

**1. Per-claim closest prior work and delta**

**C1 — Merge-tree-based space–time maps with task-defined, unit-bearing reference coordinates.**

**Closest:** ST-MTM is the closest overall method; TMTM supplies the underlying feature-preserving linearization. TMTM already represents scalar-field evolution through augmented merge trees and establishes merge-tree identity for its construction. ST-MTM explicitly adds geometry-aware layout to this family. Neither should be characterized as merely an arbitrary ordering baseline. [TMTM](https://www.csc.kth.se/~weinkauf/publications/abskoepp22.html), [ST-MTM](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6604235).

Task-selected spatial references themselves are established. Longitude–time diagrams originate with Hovmöller; radius–time diagrams are established meteorological practice. Moving reference frames also appear in Andrienko et al.’s *Space Transformation for Understanding Group Movement*, which expresses positions relative to a moving group center and direction. [Hovmöller, 1949](https://doi.org/10.1111/j.2153-3490.1949.tb01260.x), [radius–time example](https://journals.ametsoc.org/view/journals/atsc/65/5/2007jas2528.1.xml), [Andrienko et al., 2013](https://geoanalytics.net/and/papers/vast13.pdf).

**Verifiable delta:** An externally specified coordinate determines where merge-tree features should appear, while hierarchy and width constraints explicitly govern—and quantify—departures from those coordinates.

That is meaningfully different from choosing a projection to preserve neighborhoods or fitting an axis from pairwise distances. It also introduces a concrete conflict: the coordinate ordering may interleave leaves belonging to different subtrees.

**Already contained?** I found no complete instance of C1 in the reviewed literature. Its ingredients are known; their integration under the proposed constraints appears novel.

**Qualification:** “Arbitrary \(\phi\)” is not, by itself, a strong algorithmic contribution. The current frame solver already accepts an explicit scalar `reference` array. Replacing \(q_i\) with radial or focus-relative distances largely changes the input semantics. The contribution must explain the resulting analytical tasks, guarantees, and failure cases.

**Assessment:** Strongest conceptual claim, provided “topology-preserving” is proved for the constructed scalar representation.

---

**C2 — Minimum reference deviation followed by optimization within an explicit budget.**

**Closest newly identified mathematical precedent:** Shimin Li and Haitao Wang, *Separating Overlapped Intervals on a Line*, **Journal of Computational Geometry 10(1):281–321, 2019**. It minimizes the maximum movement needed to make intervals non-overlapping, including selection of their order, and provides an \(O(n\log n)\) algorithm. This is substantially closer to the placement objective than the dossier’s treelike scheduling reference. [Published paper](https://jocg.org/index.php/jocg/article/view/3077).

The relationship is precise: remove hierarchy restrictions and canvas boundaries, set \(g=0\) and \(\rho=0\), and your first-stage problem becomes minimum-maximum displacement of intervals initially centered at \(q_i\).

The visualization-side precedent is MoReVis: it scales marks by region area and optimizes their positions, including penalties for displacement from an initial projection. Its projection coordinates are normalized, and its constraints concern region intersections rather than merge-tree contiguity. [MoReVis, §§4.1–4.4](https://arxiv.org/pdf/2302.13199).

**Verifiable delta:** Solve minimum-maximum displacement over the layouts permitted by a supplied merge-tree hierarchy, with fixed measure-to-width conversion and canvas constraints, then use that optimum to constrain subsequent layout preferences.

The important distinction is the explicit guarantee

\[
\max_i |u_i-q_i|\leq \tau^*+\Delta,
\]

rather than the mere presence of a reference-error term in a weighted objective.

**Already contained?** Minimum-maximum interval displacement is already published. Position-preserving constrained optimization is already published. I found no paper containing the complete hierarchy-constrained formulation and its use as the governing error budget for merge tree maps.

**Qualification:** LP, convex QP, and staged optimization are established tools. Present the formulation, guarantee, and visualization consequences as the contribution.

**Assessment:** Strongest technical support for C1; moderate standalone novelty.

---

**C3 — Showing the certificate and feature displacement inside the visualization.**

**Closest:** Wood and Dykes’ *Spatially Ordered Treemaps* already measures locational consistency and displays displacement-vector overlays within hierarchical layouts. Rauscher et al.’s *Visual Boosting Techniques for Spatiotemporal Dense Pixel Visualizations* explicitly embeds indications of linearization artifacts into space–time displays. [Wood and Dykes, 2008](https://openaccess.city.ac.uk/id/eprint/536/), [Rauscher et al., 2026](https://arxiv.org/html/2604.25298).

**Verifiable delta:** Communicate an optimization-derived minimum achievable deviation alongside the displacement actually incurred by the displayed layout, both in the task coordinate’s units.

The distinction among these quantities matters:

\[
\tau_t^* \quad\text{minimum achievable framewise maximum error},
\]

\[
B_t=\tau_t^*+\Delta \quad\text{allowed budget},
\]

\[
e_{i,t}=u_{i,t}-q_{i,t} \quad\text{actual signed feature displacement}.
\]

**Already contained?** The broad claim “visualize projection or displacement error inside the map” is already contained in published work. The specific communication of your constrained optimum together with actual residuals was not found.

**Qualification:** A new scalar feeding familiar hatching or arrows is a limited independent contribution. Its value should come from showing that readers make more accurate coordinate judgments or recognize when a judgment is unsupported.

**Assessment:** Supporting contribution; insufficient as the headline.

---

**C4 — Cross-map comparability through a common absolute axis.**

**Closest:** Common physical coordinate systems already support comparison in conventional space–time diagrams. More specifically, Beketayev et al.’s *Geometry-Preserving Topological Landscapes* explicitly constructs comparable topological representations by projecting multiple datasets together. This is an omitted precedent worth adding. [Published author manuscript, §3.2](https://web.cs.ucdavis.edu/~hamann/BeketayevWeberMorozovAbzhanovHamann2012SIGGRAPH_ASIA_WASA_PaperFinal10082012.pdf).

**Verifiable delta:** Separately generated merge tree maps can use a declared common reference, origin, units, and width scale, while exposing the displacement that remains necessary for each map.

**Already contained?** Comparability through shared coordinates is established. I found no complete prior realization of your particular comparison protocol for reference-constrained merge tree maps.

**Qualification:** Units alone do not establish comparability. Maps must share, or explicitly reconcile:

- The definition of \(\phi\), its origin, orientation, and distance metric.
- The feature measurement and landmark conventions.
- The conversion \(c\) from feature measure to display width.
- Axis scaling, time alignment, and relevant simplification settings.
- The interpretation of layout residuals.

A common coordinate system also does not guarantee identical displayed positions for identical features under different surrounding constraints.

**Assessment:** Important practical benefit and evaluation objective; weak independent novelty claim.

---

**C5 — Polynomial tree feasibility and temporal Viterbi optimization.**

These should be judged separately.

**Tree feasibility.** Bar-Joseph, Gifford, and Jaakkola’s *Fast Optimal Leaf Ordering for Hierarchical Clustering* already uses dynamic programming over tree-consistent orders. Its objective concerns adjacent-leaf similarity, not target-window interval placement. Li and Wang address the unrestricted interval-displacement problem. Brucker, Garey, and Johnson address equal-length jobs with tree-shaped **precedence**, which is different from requiring descendant leaves to remain contiguous. [Optimal leaf ordering](https://people.csail.mit.edu/tommi/papers/BarGifJaa-ismb01.pdf), [treelike scheduling](https://doi.org/10.1287/moor.2.3.275).

**Potential delta:** A proved efficient algorithm for the actual target-window problem under merge-tree contiguity, including variable widths and permitted idle gaps.

**Already contained?** I did not find that exact result. However, “binary search plus tree DP” is currently an approach to investigate, not an established contribution.

**Temporal optimization.** Whole-sequence optimization of hierarchical layouts predates this proposal. *Temporal Treemaps* optimizes across the entire time span, and Dobler and Nöllenburg provide exact crossing-minimization formulations for temporal treemaps. [Temporal Treemaps, 2019](https://tinoweinkauf.net/publications/abskoepp19a.html), [Improving Temporal Treemaps, 2024](https://diglib.eg.org/items/f831b477-bb4b-4b0e-95cf-31479b0905af).

**Potential delta:** A useful temporal objective and candidate construction specifically for reference-constrained merge tree maps.

**Already contained?** I found no exact matching application, but applying Viterbi to a finite sequence of candidates is an established technique. Application-specific usefulness must carry this claim.

**Assessment:** The tree algorithm could become a substantial contribution after proof. Viterbi should initially be treated as an implementation mechanism.

**2. Closest-prior-work table**

“Missing” entries were absent from the dossier. They are closer to particular subclaims, not evidence that the whole proposal is already taken.

| Work | Main overlap | Delta that remains |
|---|---|---|
| **P2: Diaz et al., ST-MTM**, verified SSRN preprint, 2026 | Geometry-aware merge-tree space–time layout. | External coordinate targets and a minimum-deviation budget under fixed widths. [Source](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6604235) |
| **P1: Köpp & Weinkauf, TMTM**, TVCG 2023 / VIS 2022 | Augmented-tree linearization, sample context, merge-tree identity. | Task-coordinate placement and its distortion guarantee. [Source](https://www.csc.kth.se/~weinkauf/publications/abskoepp22.html) |
| **Missing: Li & Wang, Separating Overlapped Intervals on a Line**, JoCG 2019 | Exact minimum-maximum displacement of non-overlapping intervals. | Supplied hierarchy, anchor eccentricity, and the complete visualization formulation. [Source](https://jocg.org/index.php/jocg/article/view/3077) |
| **P7: Valdrighi, Ferreira & Poco, MoReVis**, online 2023; TVCG 30(4), 2024 | Area-scaled ribbons and optimized displacement from projected positions. | Merge-tree constraints, externally specified coordinates, and an optimal reference-error budget. [Source](https://arxiv.org/pdf/2302.13199) |
| **P10: Wood & Dykes, Spatially Ordered Treemaps**, TVCG 2008 | Geographic organization of hierarchy; displayed displacement vectors. | Temporal scalar-field maps and the specific minimax guarantee. [Source](https://openaccess.city.ac.uk/id/eprint/536/) |
| **P8: Rauscher et al., Visual Boosting Techniques…**, EuroVA 2026 | In-view disclosure of linearization artifacts. | Certified reference-coordinate deviation rather than ordering-quality indicators. [Proceedings record](https://diglib.eg.org/collections/32d9960e-7612-4cd8-b15c-89f5de1334f6) |
| **P9: Rauscher et al., Visually Assessing 1-D Orderings…**, CGF 2025 | Local and global assessment of spatial ordering errors. | Target-coordinate placement and an optimization-derived error floor. [Source](https://doi.org/10.1111/cgf.70100) |
| **Missing: Beketayev et al., Geometry-Preserving Topological Landscapes**, WASA 2012 | Geometry-aware topological displays and comparison across datasets. | A task-defined 1D coordinate and explicit placement-deviation budget. [Source](https://mrzv.org/publications/geometry-preserving-topological-landscapes/) |
| **Missing: Huson, Displacement-Optimized Tanglegrams for Trees and Networks**, MBE 2026 | Tree-constrained leaf displacement relative to another ordering. | Metric targets, finite-width intervals, a minimax objective, and scalar-field visualization. [Source](https://doi.org/10.1093/molbev/msag066) |
| **Missing: Bulteau, Gambette & Seminck, Reordering a Tree According to an Order on Its Leaves**, CPM 2022 | Reconciling a hierarchy with an external leaf order. | Continuous target positions and width-constrained placement; their inversion/deletion results do not settle your complexity. [Source](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.CPM.2022.24) |
| **Missing: Andrienko et al., Space Transformation for Understanding Group Movement**, TVCG 2013 | Moving, task-relevant spatial reference frames. | Merge-tree representation and guaranteed layout displacement. [Source](https://geoanalytics.net/and/papers/vast13.pdf) |
| **P11/P13: Temporal Treemaps; Improving Temporal Treemaps by Minimizing Crossings**, 2019/2024 | Optimization of evolving hierarchical layouts across time. | Your coordinate-error objective and constraints. [2019](https://tinoweinkauf.net/publications/abskoepp19a.html), [2024](https://diglib.eg.org/items/f831b477-bb4b-4b0e-95cf-31479b0905af) |
| **P20/P21: Treelike scheduling; Fast Optimal Leaf Ordering**, 1977/2001 | Relevant algorithmic techniques and structured ordering problems. | Neither source establishes the proposed target-window tree DP. [1977](https://doi.org/10.1287/moor.2.3.275), [2001](https://people.csail.mit.edu/tommi/papers/BarGifJaa-ismb01.pdf) |

The remaining candidates are relevant background, but I found no stronger full-method overlap:

- **P3–P6:** Franke et al.’s projection-selection framework, MotionRugs, Stable Visual Summaries—including metric-position MotionLines—and SpatialRugs establish much of the projection, temporal-summary, and spatial-context territory. [Franke et al.](https://doi.org/10.1111/cgf.14311), [MotionRugs](https://bib.dbvis.de/uploadedFiles/MotionRugsPreprint.pdf), [Stable Visual Summaries](https://arxiv.org/abs/1912.00719), [SpatialRugs](https://bib.dbvis.de/uploadedFiles/cgsprpreprint.pdf).
- **P12, P16–P18:** Nested Tracking Graphs, Data-Driven Space-Filling Curves, Geometry-Aware Merge Tree Comparisons, and cyclone feature tracking cover hierarchical evolution, linearization, comparison, and domain feature definitions. They do not establish the proposed coordinate-placement guarantee. [P12](https://doi.org/10.1111/cgf.13164), [P16](https://arxiv.org/abs/2009.06309), [P17](https://arxiv.org/abs/2107.14373), [P18](https://arxiv.org/abs/2011.08676).
- **P14–P15:** Stratiline and Geo-Storylines prevent a broad claim of introducing location semantics to storylines. Stratiline’s accessible description uses a narrative “Actor Migration Distance” to order locations; this is not evidence of a calibrated physical-distance axis. [Stratiline](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4835629), [Geo-Storylines](https://ilda.saclay.inria.fr/geo-storylines/).
- **Additional contemporary neighbor:** *GroupRugs* explicitly emphasizes evolving groups while retaining spatial relationships. It deserves discussion if your motivation includes keeping groups visually intact, although those groups are not scalar-field merge-tree features. [Stolk, Wulms & Verbeek, PacificVis 2025](https://research.tue.nl/en/publications/grouprugs-visual-summaries-for-groups-in-collective-movement-data/).

**Bibliographic corrections:** P8 now has a EuroVA 2026 proceedings record, so it should not be treated only as an arXiv competitor. ST-MTM’s SSRN posting is verified; its claimed C&G publication status was not independently established in this search. These status distinctions affect citation accuracy, not whether the work deserves substantive comparison.

**3. Is the combination novel?**

**Yes, provisionally, and the surviving combination is substantive.**

Its components address a coupled problem:

1. The task coordinate specifies a desired location.
2. The hierarchy restricts which features may appear between which others.
3. Fixed widths consume space and can force displacement.
4. The first-stage optimum quantifies the conflict.
5. The budget limits the sacrifice made for secondary objectives.
6. The visualization communicates the remaining displacement.

The strongest novelty statement is therefore:

> The method makes reference-coordinate fidelity an explicitly constrained quantity in merge-tree space–time layouts and computes the minimum deviation required by the selected representation.

That is a reviewer-verifiable delta. It does not depend on claiming that physical axes, optimization, or error overlays are individually new.

I found no named published paper containing this full result. Under the dossier’s decision rules, **ABANDON is not justified**.

**4. Technical qualifications that materially affect the claims**

**The current implementation establishes a layout model, not the entire advertised preservation result.** The module explicitly states that it produces leaf intervals and does not claim full scalar-field reconstruction. The documentation also warns against transferring TMTM’s identity proof directly to RA’s filling procedure. [Implementation](/Users/yudong/Research/RA-MTM/src/ramtm/error_budget.py:1), [documentation](/Users/yudong/Research/RA-MTM/docs/solver.md:174).

Three guarantees must be distinguished:

- The input tree is unchanged.
- Descendant leaf sets remain contiguous in the layout.
- The constructed 1D scalar function has the required merge tree and sample representation.

The first two do not establish the third. A proof must address filling, interpolation, extrema and saddle values, and any simplification or rasterization. “All samples” also needs a precise distinction between the underlying representation and its finite-resolution image.

This is a tractable-looking proof obligation, not evidence that the concept is impossible.

**The coordinate guarantee applies to anchors.** The solver bounds \(u_i-q_i\). It does not establish that every pixel inside a feature interval is located at that sample’s true \(\phi\)-coordinate. Moreover, \(w_i=cA_i\) encodes a feature measure; it generally does not equal that feature’s physical extent along \(\phi\).

The display must make both semantics clear. Otherwise readers may interpret the width as kilometers of spatial support while it actually encodes area or volume through a conversion factor.

**“Absolute” needs a more precise definition.** A distance to a moving cyclone has physical units and a defined origin, but is relative to that cyclone. I recommend **“externally specified, unit-bearing reference coordinate.”**

Specify whether \(\phi(R_i,t)\) uses an extremum, a centroid, minimum distance between supports, or another statistic. The dossier and older documentation differ here: the solver defaults to centroid projection but accepts explicit references, and the sequence interface supports supplied landmark points. [Reference handling](/Users/yudong/Research/RA-MTM/src/ramtm/error_budget.py:100), [sequence interface](/Users/yudong/Research/RA-MTM/src/ramtm/error_budget.py:257).

**The certificate has a limited, valuable meaning.** For an exactly solved feasible model,

\[
\tau_t^*
\leq \max_i|e_{i,t}|
\leq \tau_t^*+\Delta.
\]

This certifies the best achievable **maximum anchor deviation under the specified constraints**. It does not certify:

- A minimum error for each individual feature.
- Error caused exclusively by topology.
- Original multidimensional geometry or feature-tracking correctness.
- Statistical uncertainty.

Width scale, gap, canvas, and eccentricity all influence \(\tau^*\). If total widths and gaps exceed canvas capacity, increasing \(\tau\) cannot repair the model.

The code enumerates legal orders and records their LP optima, which supports a small-instance numerical oracle. Its QP optimality-gap fields concern the secondary objective; they are not substitutes for verifying the first-stage optimum. [Solver stages](/Users/yudong/Research/RA-MTM/src/ramtm/error_budget.py:135).

**Comparability is error-aware, not exact registration.** For corresponding features in maps \(A\) and \(B\),

\[
\left|(u_i^A-u_i^B)-(q_i^A-q_i^B)\right|
\leq |e_i^A|+|e_i^B|.
\]

This gives C4 a useful quantitative interpretation. Shared units permit a meaningful comparison, while the residuals tell readers how much of the apparent difference may come from layout.

**The Hovmöller comparison needs narrower wording.** Hovmöller-style diagrams also use transects and fixed-azimuth slices; averaging is not their universal defining operation. Published range–time examples explicitly sample along a fixed azimuth. [Example](https://doi.org/10.1175/1520-0450%282003%29042%3C1697%3ATDWROO%3E2.0.CO%3B2).

Use “avoids collapsing distinct merge-tree features through the chosen aggregation” rather than claiming that all conventional Hovmöller diagrams average features away. Also explain that your displaced, feature-based representation has different spatial sampling semantics.

**5. Algorithmic feasibility: what C5 still needs**

For a fixed trial value \(\tau\), eliminate the anchor variables. Let the canvas be \([a,a+L]\) and \(h_i=\rho w_i/2\). Feasible interval centers must satisfy

\[
z_i\in[\ell_i,r_i],
\]

where

\[
\ell_i=\max\!\left(a+\frac{w_i}{2},q_i-\tau-h_i\right),
\qquad
r_i=\min\!\left(a+L-\frac{w_i}{2},q_i+\tau+h_i\right).
\]

For a **fixed leaf order**, feasibility follows from placing each center as early as possible:

\[
z_{\pi(k)}
=
\max\!\left(
\ell_{\pi(k)},
z_{\pi(k-1)}
+\frac{w_{\pi(k-1)}+w_{\pi(k)}}2+g
\right),
\]

and checking all upper bounds. This is a direct derivation from your constraints.

The unresolved part is choosing a hierarchy-consistent order efficiently. A polynomial-time claim requires:

- A state representation retaining all information needed to combine subtrees.
- A proof that the number of states or breakpoints stays polynomial.
- Treatment of variable widths, internal slack, and tree degree.
- A stated numerical accuracy if binary search is used.

A subtree’s total width and one earliest feasible position are not obviously sufficient statistics. Conversely, hardness results for other tree-ordering problems do not prove this problem hard. **Its complexity remains open in this review.**

For temporal optimization, ordinary Viterbi is exact for an objective with fixed state and transition costs:

\[
D_t(k)=a_t(k)+\min_j\{D_{t-1}(j)+b_t(j,k)\}.
\]

Your current motion term depends on continuous positions:

\[
[(u_t-u_{t-1})-(q_t-q_{t-1})]^2.
\]

Consequently, an order alone is generally insufficient as the state for an exact joint optimization. Optimizing each adjacent pair separately can assign incompatible positions to their shared middle frame.

Defensible alternatives are:

- Viterbi over **fixed candidate layouts**, with optimality restricted to that candidate set.
- Joint continuous optimization for a fixed order sequence.
- A richer method that carries continuous-state information and proves its guarantees.

A fast first-stage feasibility algorithm also would not automatically make the second-stage search over orders scalable.

**6. Strongest likely reviewer objection and positioning that survives**

My anticipated strongest objection is:

> TMTM already provides the feature-preserving representation; ST-MTM adds geometry; MoReVis adjusts projected positions and sizes; interval separation already minimizes worst-case displacement; and existing visualization methods display distortion. How much remains beyond combining these mechanisms and supplying a different target coordinate?

That is a credible incrementalism objection. It is **not** a demonstrated containment result.

The positioning that survives focuses on a specific analytical requirement: **reading task-coordinate positions and changes while retaining the merge-tree organization of distinct scalar-field features**. The contribution is the explicit reconciliation of those requirements, including a computable limit on coordinate fidelity.

To make that case carry, the evaluation should include:

- **A soft-reference baseline:** ST-MTM-style layout with a reference penalty. Demonstrate what the hard budget guarantees that weight tuning does not.
- **A coordinate-faithful baseline:** Features plotted directly at \(q_i\), with a reasonable overlap treatment. Show what hierarchy preservation adds.
- **Appropriate Hovmöller variants:** Compare against suitable averages, slices, or transects for the task.
- **Controlled conflicts:** Translation, feature growth, incompatible subtree ordering, and radial crowding. Separate changes in the data from changes introduced by layout.
- **Reader tasks:** Position or threshold judgments, relative motion, and recognizing when apparent differences fall within layout displacement.
- **Exact small-instance validation:** Verify scalable approximations against enumeration and distinguish feasible upper bounds from proved minima.

A particularly useful ablation is to relax hierarchy while holding other constraints fixed. The difference between the two optima isolates the additional cost of contiguity under that model; \(\tau^*\) alone does not.

**7. Headline, demotions, and research risk**

**Headline:** Combine C1 and C2:

> **Task-referenced merge tree maps with explicit bounds on coordinate distortion.**

Use “topology-preserving” prominently once the construction’s preservation theorem is established. “Generalized Hovmöller” is a useful explanatory analogy, but should not carry the novelty argument alone.

**Contribution hierarchy:**

1. **Primary:** Task-reference semantics coupled to hierarchy-constrained, bounded-deviation placement.
2. **Supporting:** Visual communication of actual displacement and the achievable error floor.
3. **Demonstrated benefit:** Comparison under a common reference protocol.
4. **Potential additional contribution:** A proved scalable tree-placement algorithm.
5. **Implementation detail unless stronger evidence emerges:** Candidate-based Viterbi optimization and the use of LP/QP.

**Key differentiator:** The representation gives a physically interpretable target coordinate and computes how far satisfying its hierarchy and width requirements forces the layout to depart from that target.

**Main novelty risk:** If the work amounts to supplying new \(q_i\) values, adding familiar displacement overlays, and presenting examples, reviewers can reasonably regard the delta as thin. The formulation’s guarantee and demonstrated analytical consequences must carry the paper.

**Main technical risk:** Claiming full topology/sample preservation, globally unavoidable error, or temporal global optimality beyond what the implemented construction and search establish.

**Main usefulness risk:** Non-injective references—especially radial and focus-relative distances—may create enough crowding that required displacements undermine the coordinate judgments the method is intended to support. This is an empirical question to test, not a reason to reject the idea in advance.

**One-sentence positioning:** *Task-referenced merge tree maps organize scalar-field features along an externally specified coordinate with physical units, preserve their hierarchical contiguity and fixed measure encoding, and compute and display the minimum reference deviation required by those layout constraints.*