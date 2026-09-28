**The core mathematics holds up. The current paper does not yet hold up.** My recommendation is **GO for a five-week PacificVis submission effort; NO-GO for submitting the present claims unchanged.** My current review vote would be **weak reject**, principally because the implemented frontier is not a certified continuous lower bound, the relaxation is substantially weaker than advertised, and the reader claims exceed the evaluation.

I read the brief and primary artifacts, including the updated v0.2 draft that appeared during this review. I independently tested 300 random instances, recomputed unrestricted optima across all **376 frames**, reproduced the unlimited-relaxation results on all five datasets, and reran the 1,024-leaf experiment. I did not edit files.

1. **Publishability and innovation**

   **Innovation: 7/10 for the certificate–algorithm–topological-bound contribution.** Much less for the layout heuristic alone.

   The strongest contribution is the combination of:

   - A precise, conditional answer to “how much positional error is unavoidable?”
   - An exact feasibility DP that makes the certificate practical for large binary hierarchies.
   - A filling-independent obstruction connecting broken contiguity to merge-level distortion.

   None requires profound mathematics individually. Together they could make a good visualization technique-and-analysis paper. Visualization research does not require a new complexity class or a huge benchmark to be worthwhile.

   The weaker components are the automatic reference direction, the greedy relaxation, and the elementary optimization propositions presented as numerous separate contributions. The labeled-interleaving equivalence is an application of existing theory, not a new distance theorem.

   **“A small problem in a small field” is too pessimistic, but the current presentation invites that reaction.** The general question—when grouping constraints force a spatially misleading layout—is consequential. The paper must demonstrate what a visualization designer or analyst can do differently because the certificate exists. At present, the certificate predicts optimization difficulty much more convincingly than reader difficulty.

   Also, remove claims that existing methods do not measure or report spatial distortion. ST-MTM reports spatial-quality metrics and discusses distortion explicitly. The defensible distinction is **certifying unavoidable maximum deviation from a specified positional reference**. Its width model also optimizes deviations from target widths; it does not simply fix every width to the target proportional allocation. See §§4.1 and 5–7 of :codex-file-citation{path="/Users/yudong/Research/RA-MTM/references/pdf/ssrn-6604235.pdf" purpose="source"}.

2. **Generality and framing**

   I would frame the paper around:

   > Given a hierarchy, item widths, and meaningful reference coordinates, how much positional displacement is unavoidable—and what hierarchy information must be sacrificed to reduce it?

   Keep three scopes distinct:

   | Scope | What transfers |
   |---|---|
   | Hierarchy-constrained interval layouts | The positional model, certificate, witness, and DP |
   | Merge-tree scalar maps | The filling-independent merge-level bound and conditional interleaving interpretation |
   | Other applications | Only the parts whose assumptions and visual semantics actually match |

   Clustered heatmaps and dendrogram-ordered pixel displays are convincing extensions **when the reference has a defensible meaning**, such as geographic position or collection time. An ordinary clustered heatmap does not promise that row position represents geography. A large geographic certificate alone does not establish that its visualization is misleading.

   Geophylogenies are plausible. Storylines need qualification: overlapping groups and temporal constraints need not form a single laminar hierarchy. Your per-frame bound may remain useful, but the entire method does not transfer automatically.

   **The 1,024-leaf experiment is useful and numerically credible.** My rerun reproduced approximately:

   - Time-series hierarchies: \(H=46.7\%–48.2\%\).
   - Geographic Ward hierarchy: \(H=1.45\%\).
   - Geographic single linkage: \(H=32.4\%\).

   The last result matters: “spatial hierarchy means low conflict” is false. The rank-reference result also helps show that the phenomenon is not merely geographic density versus uniform row spacing. [Generality implementation and results](/Users/yudong/Research/RA-MTM/prototypes/generality.py:38).

   But this is currently **a computational transfer experiment, not a demonstrated visualization application**. Add:

   - An actual dense-pixel/heatmap figure with reference, hierarchy, certificate, and a highlighted conflicting triple.
   - OLO, geographic ordering, and your minimax ordering on the same hierarchy.
   - One independent example with a meaningful external coordinate.
   - Error distributions or affected-item counts alongside the maximum.

   Be precise about \(H\): it is the **difference between two optimal worst-case errors**. It is not the fraction of rows displaced, nor a per-item displacement attributable to hierarchy.

   The broader literature already studies group continuity and spatial quality, and tree ordering against external orders. Position the work against [GroupRugs](https://research.tue.nl/en/publications/grouprugs-visual-summaries-for-groups-in-collective-movement-data/), [external-order tree rearrangement](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.CPM.2022.24), and [displacement-optimized tanglegrams](https://doi.org/10.1093/molbev/msag066), rather than claiming to discover the conflict itself.

3. **Theory and implementation audit**

   My conclusions on [the proofs](/Users/yudong/Research/RA-MTM/paper/proofs_zh.md):

   | Result | Verdict | Substance and qualifications |
   |---|---|---|
   | Proposition 1 | **Correct** | The four window inequalities yield the stated formula, including canvas terms. Useful algebra, not a deep theorem. |
   | Theorem 1 | **Correct recurrence and optimal substructure** | Earlier completion dominates later completion because subsequent constraints depend only on the next starting bound. This is the strongest algorithmic contribution. |
   | Proposition 5 | **Correct under its stated integer-width/gap model** | Also requires the grid-aligned canvas from the discrete model. It does not cover changing widths and gaps through rounding. |
   | Theorem 2 | **Correct** | The interval-inclusion argument proves the bound for any filling. Short proof, worthwhile insight. |
   | Proposition 6 | **Correct with explicit conventions** | Same bijective leaf labels, preserved leaf heights, and no additional birth extrema; use the standard upward root extension. |
   | Corollary 1 | **Correct as a necessary lower bound** | It is not an attainable Pareto frontier, and it gives no approximation guarantee for the greedy algorithm. |
   | Propositions 2–3 | **Correct but elementary** | Attainment over finitely many feasible LPs; monotonicity under removing constraints. |
   | Proposition 4 | **Correct** | A useful explanatory witness. It bounds \(\tau^*\), not directly \(H\). |

   **Independent numerical checks:** across 300 fresh random instances, closed form versus LP differed by at most \(3.6\times10^{-15}\); the discrete–continuous gap ranged from zero to **0.496905 pixels**; exhaustive order-based feasibility checks found **zero DP disagreements**.

   The Munch–Stefanou concern is resolvable: Definition 3.7 uses a **bijection onto leaves**, and Corollary 4.3 includes diagonal leaf-height entries. Equal leaf heights make those diagonal differences zero, giving your off-diagonal expression. This is their labeled phylogenetic-tree interleaving distance, not an unrestricted unlabeled distance. [Original paper](https://arxiv.org/pdf/1803.07609).

   I also checked the regenerated relaxed maps: under the repository’s numerical tolerance, all five datasets retained the expected extrema values, and the labeled anchors were extrema with the correct heights. This supports Proposition 6’s application more broadly than the cited ERA5-only check.

   **The important failures are downstream of the proofs:**

   **The plotted frontier is not currently certified.** `Disc` rounds widths and gaps and recomputes eccentricity, thereby changing the optimization problem. `frontier.py` then uses the resulting discrete optimum as a continuous lower bound. Proposition 5 does not justify that. [Discretization](/Users/yudong/Research/RA-MTM/prototypes/theory.py:22).

   This is observable in the saved artifacts. At zero topology distortion, the exact continuous mean certificate for ERA5 is **8.77209%** of the axis; the plotted value is **8.78001%**. All five datasets have this upward discrepancy. Small numerically, but a claim of a *provable lower bound* cannot tolerate the wrong inequality direction.

   There is a second, separate error: the code selects the **preceding** distortion-grid point and calls that conservative. Since \(\Phi\) is nonincreasing, the preceding value can overestimate \(\Phi(D)\). Use actual breakpoints/exact evaluations, or a conservative envelope in the correct direction. [Frontier lookup and plotting](/Users/yudong/Research/RA-MTM/prototypes/frontier.py:53).

   **The factor-two characterization is false as a general method claim.** The JSON reports maximum
   \[
   d_{\mathrm{top}}/\max_{v\text{ broken}}\gamma_v
   \]
   of approximately **1.985, 1.985, 2.361, and 2.260** for the two ERA5 datasets, wildfire, and Ring. Wildfire therefore reaches about **4.72 times the theorem’s lower bound**, not twice. A median ratio of one does not establish an approximation guarantee. [Recorded checks](/Users/yudong/Research/RA-MTM/prototypes/output/frontier.json).

   **The greedy relaxation gets stuck on actual data.** ERA5 frame 9 has \(\tau^*=5.696596934\), \(\tau_{\rm free}=0\), and \(\theta=2.098708471\). Flattening node 1403 alone or node 121 alone changes nothing; flattening both gives **zero**. The algorithm refuses both individual steps. Unlimited relaxation leaves **19 ERA5 frames**, **22 ERA5-2014 frames**, **5 wildfire frames**, and **6 Ring frames** above the hierarchy-cost threshold. [Acceptance rule](/Users/yudong/Research/RA-MTM/prototypes/relax_hierarchy.py:102), [saved frame 9](/Users/yudong/Research/RA-MTM/prototypes/output/relax_metrics.json:141).

   **Complexity and assumptions need tightening:**

   - The binary-tree algorithm is pseudo-polynomial in resolution. Arbitrary-degree nodes retain exponential dependence on degree. Do not advertise a general polynomial algorithm without that qualification.
   - Bisection returns an optimum to tolerance, not symbolic exactness.
   - `dp_tau` assumes an upper search bound of \(N\), although the formal model permits arbitrary \(q_i\). A one-leaf test with canvas 10, width 1, and reference 100 returns infinity despite a finite optimum of 90.5. Existing dataset references are in bounds; fix the contract or bracket.
   - The scalable DP computes the certificate. The actual layout/relaxation pipeline still enumerates orders. “Scales to thousands” currently applies to the certificate, not the complete method.
   - Ties and plateaus require a canonical convention. Contract zero-height structure rather than arbitrarily resolving a multi-saddle into additional mandatory binary clades. Unary suppression is appropriate; split trees work by sign reversal. Define the singleton \(d_{\mathrm{top}}\) as zero.
   - Use an explicitly translation-equivariant rounding rule in Proposition 5’s proof. “Round” should not silently mean ties-to-even.
   - Theorem 2 needs no extremum assumption for its interval-max discrepancy. Calling that discrepancy an interleaving distance does need Proposition 6’s assumptions.
   - The adjacent merge-height gap is not automatically persistence in the usual birth–death sense.

   One favorable finding deserves emphasis: `tau_free` is heuristic above six leaves, but my independent continuous subset-feasibility solver matched its stored values on **every current frame**. The reported conflict counts survive. The implementation still needs to expose or eliminate that heuristic status. [Current unrestricted solver](/Users/yudong/Research/RA-MTM/prototypes/general_method.py:102).

4. **Reader-proxy analysis**

   **Convincing as a geometric diagnostic; unconvincing as evidence of human misreading.**

   The proxy knows feature identities and exact anchor coordinates. Readers must locate, identify, and track features through a scalar image. They may use color, shape, context, or linked views. No evidence establishes that they apply this thresholded distance rule.

   Specific concerns:

   - **Dependence remains.** Resampling starting frames handles within-frame pair dependence, but not overlapping windows, serial correlation, or recurring tracks. Use paired method comparisons with temporal blocks or defensible event-level clusters.
   - **“Chance” is overstated.** Shuffling predicted categories preserves method-specific response frequencies, including abstention. It is a permutation null, not a universal human chance level.
   - **Reversal alone rewards abstention.** At the headline wildfire setting, relaxed reversal falls from ST-MTM’s **21.4% to 5.4%**, but missed changes rise from **14.3% to 26.8%**. That remains potentially useful, but is a different claim from simply “readers become more accurate.”
   - **Truth is operational, not meteorological.** Tracked extrema of smoothed fields are legitimate representation-level targets. They are not independently validated storm trajectories. ST-MTM optimizes relationships between support centroids, which adds a target mismatch.
   - **Thresholds are not perceptually validated.** Baselines use global occupied anchor range for normalization; your methods use the specified canvas. Baselines are evaluated through rasterized anchors, yours through continuous coordinates. Harmonize the displayed measurement model. [Proxy implementation](/Users/yudong/Research/RA-MTM/prototypes/misreading.py:31).
   - **The headline time-window label is wrong.** The reported 33.7%, 24.9%, etc. correspond to **\(k=2\)**: 24 hours for ERA5 and four days for wildfire. The summary and current table call this \(k=1\). At actual ERA5 \(k=1\), TMTM and ST-MTM reversal rates are **26.3% and 18.7%**.
   - **The certificate does not establish the claimed causal explanation.** Large worst-case positional error need not reverse a pair’s temporal distance change. Corollary 1 does not prove that correctly reading approach/separation requires topology relaxation.

   The last point is central. For reference-space pair distance \(d_q\), positional error bounds imply
   \[
   |\Delta d_u-\Delta d_q|
   \le \epsilon_{i,t}+\epsilon_{j,t}+\epsilon_{i,t+k}+\epsilon_{j,t+k}.
   \]
   That directly relates positional accuracy to the task. A frame’s minimum unavoidable maximum error does not itself identify which pair or temporal judgment is unsafe.

   **Would I demand a user study?** If you retain “readers misread,” “one in three judgments,” or “disclosure helps readers,” yes. A focused study should compare the same visualization with and without certificate disclosure, and measure accuracy, abstention, and confidence.

   A technique-and-analysis paper can be publishable without that study if it consistently claims **proxy sign disagreement**, provides convincing visual cases, and demonstrates a concrete design use for the certificate. Another task—absolute reference-position estimation or an explicitly defined along-axis approach task—would connect better to your actual objective.

5. **Missing comparisons and experiments, in priority order**

   **First: establish fair model and baseline comparisons.** Compute certificates under the baselines’ actual width and anchor conventions, or explicitly report a relaxed model that contains their feasible layouts. Your fixed widths, \(\rho=.5\), and prescribed gaps do not automatically cover TMTM and ST-MTM.

   TMTM preserves the complete sample allocation and augmented-tree traversal, which imposes structure beyond your leaf-interval model. Inspecting its Algorithm 1 confirms that distinction: :codex-file-citation{path="/Users/yudong/Research/RA-MTM/references/pdf/koepp22.pdf" purpose="source"}.

   Moreover, most ST-MTM runs use adapted defaults—uniform weights, \(r=.95\), \(\lambda=.5\), Start 0—rather than the paper’s reported Storms settings. Ring receives a preset; the other datasets generally do not. This is not necessarily an invalid controlled variant, but it is insufficient for broad superiority claims without parameter sensitivity and explicit labeling. [Baseline dispatch](/Users/yudong/Research/RA-MTM/experiments/era5.py:168).

   **Second: measure relaxation quality against a small-instance optimum.** The observed plateau failure makes this essential. Separate:

   - Which constraints are removed.
   - Which admissible order/layout is selected.
   - Which scalar filling is used.

   Otherwise, distance from the lower bound is attributed to filling when search failure also contributes.

   **Third: implement a midpoint filling baseline on controlled examples.** The three-leaf tightness construction is straightforward when leaf heights lie below the proposed midpoint. Compare it with LCA filling. Do not claim that every tree or fixed leaf-arc filling can attain every local half-gap bound simultaneously.

   **Fourth: make \(\tau_{\rm free}\) exact for the current experimental sizes.** You do not need a five-week detour implementing a general Li–Wang extension. A small-instance exact subset solver suffices here. Li–Wang’s published problem does not automatically include your canvas and leaf-dependent anchor slack. [Original interval-separation problem](https://jocg.org/index.php/jocg/article/view/3077).

   **Fifth: complete the meaningful generality comparison.** OLO, reference sorting, and minimax ordering; actual visual output; one independent reference-bearing dataset.

   **Sixth: test the choices that determine the phenomenon.** The new direction sweep is useful. Remaining priorities are width allocation, eccentricity, smoothing/feature extraction, and temporal sampling—not a large indiscriminate parameter grid.

   Two artifact-specific corrections:

   - The new draft says changing \(\theta\) from 1% to 5% reduces prevalence by only 3–20 percentage points. Wildfire at 157.5° drops from **80% to 33.3%**, a **46.7-point** drop. [Robustness results](/Users/yudong/Research/RA-MTM/prototypes/output/robustness.json:189).
   - ARCO and archived CDS-derived features have identical IDs, tracks, hierarchy, dates, and extrema, but not identical supports/centroids: I found maximum area and centroid-coordinate differences of about **2.99752** and **0.21244** layout units, respectively. Qualify “identical features”; rerun the final selected protocol on the intended source. [Archived features](/Users/yudong/Research/RA-MTM/results/era5/shared_features.json).

   Finally, a per-step merge-gap cap is not a final distortion budget. ERA5’s 20% cap produces **32.6%** maximum merge distortion. Either expose it honestly as a heuristic control or enforce a bound on the final measured quantity.

6. **GO/NO-GO, five-week plan, and claims**

   **GO**, because I failed to break the central formula, recurrence, or topological obstruction, and the principal numerical phenomenon reproduced. **NO-GO on the current manuscript**, because the remaining problems affect its central advertised guarantees and interpretation.

   | Week | Highest-value work | Required outcome |
   |---|---|---|
   | 1 | Correct the frontier computation/plot, theorem qualifications, factor-two language, and reporting errors; preserve small counterexamples | Every guarantee matches the evaluated model |
   | 2 | Native-model baseline certificates, justified ST-MTM variants, exact small-instance relaxation and unrestricted optima | Separate unavoidable error from baseline settings and heuristic failure |
   | 3 | Finish one usable certificate display and the dendrogram/heatmap demonstration; add OLO comparison | Show a concrete decision enabled by the certificate |
   | 4 | Full confusion analysis, paired temporal-block uncertainty, preprocessing sensitivity; focused reader study if retaining human claims | Task evidence matches the claims |
   | 5 | Rewrite around three contributions, finalize visual cases, move technical proofs to supplement, rerun final protocol and reconcile every number | A coherent, reviewable nine-page paper |

   Prepare any reader-study recruitment during week 1. If that study cannot be completed, remove human-performance claims rather than presenting the proxy as a substitute.

   The results-to-claims boundary should be:

   | Claim | Allowed now? | Needed qualification or evidence |
   |---|---|---|
   | Exact fixed-order positional optimum | **Yes** | Stated interval model and feasibility assumptions |
   | Exact discrete hierarchy feasibility DP | **Yes** | Binary/bounded-degree complexity; numerical tolerance for optimum search |
   | Approximately 58–63% conflict prevalence under the automatic reference | **Yes, for these processed datasets** | Exact unrestricted implementation and preprocessing disclosure |
   | Broken contiguity costs at least half the parent–child merge gap | **Yes** | Defined interval merge-level discrepancy |
   | That discrepancy equals labeled interleaving distance | **Conditionally** | Bijective labels, preserved leaf heights, canonical extrema/root conventions |
   | Analytical position–topology lower bound | **Yes** | Common layout assumptions; necessary, not generally attainable |
   | Current black curve is a certified continuous lower bound | **No** | Fix discretization and distortion-grid evaluation |
   | Relaxation reduces reference error on these datasets | **Yes** | Report actual final topology cost and unresolved frames |
   | Relaxation is near-optimal or within a factor of two | **No** | Optimal comparisons or a valid guarantee; current artifacts contradict the general wording |
   | Relaxation reduces proxy reversals | **Yes, conditionally** | Correct windows, full confusion results, fair thresholds and uncertainty |
   | Readers make fewer mistakes or benefit from disclosure | **No** | Human evaluation |
   | Certificate computation transfers to large dendrograms | **Yes** | Reproduced; distinguish certificate from full layout pipeline |
   | Broad usefulness across heatmaps, geophylogenies, and storylines | **Not yet** | Explicit mappings of assumptions and demonstrated visual tasks |

   **The acceptance opportunity is real.** The strongest paper here explains and certifies a structural limitation of visualization, then demonstrates how to use that knowledge. The current draft weakens that contribution by turning conditional mathematical guarantees into universal plotting claims and geometric proxy results into statements about readers.

- :codex-followup[Prioritize corrections]{prompt="Turn this review into a concise, artifact-linked correction checklist, ordered by acceptance impact."}
- :codex-followup[Design exact comparisons]{prompt="Design the smallest decisive experiments comparing greedy relaxation, optimal relaxation, LCA filling, and midpoint filling."}
- :codex-followup[Rewrite defensible claims]{prompt="Rewrite the abstract and contribution statements so every claim stays within the verified evidence from this review."}