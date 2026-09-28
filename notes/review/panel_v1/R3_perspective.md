# Review R3 — Peer Reviewer 3 (Perspective: information visualization design, layout algorithms, perception)

**Identity.** InfoVis researcher working on dense pixel displays, storyline/ordering layouts and graph drawing algorithms (algorithmic perspective on visualization), with an interest in perception and in how readers actually use static summaries.

**Review focus.** Is the work useful to people who design or read hierarchy-constrained 1-D displays? I concentrate on the task abstraction behind the "reference coordinate", on the disclosure design (certificate strips, witness triples, visibility of relaxation), on the dendrogram transfer (RQ4), on the connection to the algorithms-for-visualization literature, and on figure quality at print size. I reviewed the LaTeX source (newer than the PDF, including the new Sec. 3.2), the compiled PDF, the figure PNGs at full resolution, and the prototype outputs behind RQ2 and RQ4 (`replicate_*.json`, `generality.json`, `dendrogram_demo.json`, `quality.json`, `fig_witness.png`).

## Recommendation

- **Decision:** Major Revision
- **PacificVis score:** 3 / 5 (borderline; leaning accept if the disclosure and figure issues are fixed)
- **Confidence:** 4 / 5 (strong on layout algorithms, pixel displays and figure design; weaker on the merge-tree topology details, which I checked only for consistency)

## Summary assessment

The paper asks a good question for the algorithms-for-visualization community: when a 1-D display must keep every cluster or subtree contiguous, how much positional error is *forced*, and what does it cost to reduce it? The answer is careful and mostly correct. There is a bottleneck certificate with a closed form for fixed orders, an exact pixel-resolution dynamic program, a width-free variant that separates "forced" from "chosen" error in existing maps, a tight topological price for breaking contiguity, and an exact position–topology frontier for small trees. From my perspective the theory is the strongest part. The dendrogram example is the most transferable idea.

The weakest part is the one the title and the Implications section rely on: helping *readers*. The certificate is disclosed only as frame-level strips. The witness triples, which the paper says "name the features responsible", never appear in any figure. The topological change caused by relaxation (including pixel values altered by the barrier filling) is not marked on the map. The authors' own proxy outputs show that the frame-level flag is set for 83–92% of clear pairs and does not predict where reversals occur (lift about 1 for TMTM/ST-MTM). The reader-proxy results ignore known perceptual biases in judging the vertical distance between steep curves, and the steep curves are exactly what the method produces. Several figures have 3–5 pt text at print size. Related work misses storyline and tanglegram crossing minimization, PQ-trees and seriation. These problems can be fixed within one revision cycle, but they need to be fixed.

## Strengths

**S1 — Worst-case framing that fits the reader's situation (Sec. 3.2 "Why the maximum deviation", Def. 1, Prop. 2).** The argument that a reader does not know which feature is misplaced, so a guarantee must hold for every feature, is the right justification for a bottleneck objective, and it is unusual in layout papers. The decomposition H = τ* − τ_free (Prop. 2) gives designers a clear statement: space is not the problem, the hierarchy is. Fig. 4 makes this point in one glance.

**S2 — The width-free certificate as an audit tool for other people's maps (Prop. 4, Fig. 1a, Sec. 7.2 last paragraph).** Bounding *every* hierarchy-consistent map under *any* monotone calibration of its axis is a fair way to discuss TMTM and ST-MTM without claiming that they are "wrong". The split into "unavoidable 6–8%" and "chosen" deviation is the most useful number in the paper for authors of future merge tree maps. It also applies directly to clustered heatmaps.

**S3 — Algorithmic content that visualization readers can reuse (Thm. 1, Alg. 1, Prop. 3).** The earliest-completion DP over tree-consistent orders composes monotone arrays, and it is a clean, implementable pattern (structurally a sibling of the optimal-leaf-ordering DP). The half-pixel certified lower bound is honest about discretization. Checking against brute force on 300 random hierarchies and all ERA5/Ring frames is good practice.

**S4 — The topological price is layout-independent and tight (Thm. 2, Prop. 5).** "Weak merges are cheap to break, strong merges are expensive" is an actionable design rule, and the barrier filling is a real improvement over LCA filling (up to 2× lower δ*). The case study in Sec. 7.4 and the pipeline Fig. 2 (panels 4–5) tie the bound to a concrete 5.4 hPa merge.

**S5 — Honest reporting of limits and negative results (Sec. 8, Table 2 caption, Sec. 7.3 last sentences).** Stating that the proxy "is a diagnostic of what the geometry of a map supports, not a study of human readers", reporting that relaxation *increases* misses on fire (+15.2 points), and listing failed designs (radial centres, stability-priority policy, illegible per-feature ticks) are all to the authors' credit.

## Weaknesses (ranked by impact on acceptance)

**W1 — MAJOR. Disclosure is claimed but not designed or evaluated; the witness triple is never shown to a reader.**
*Where:* Abstract ("names the features responsible" in Sec. 9), contribution bullet 1, Prop. 2, Sec. 6 "Rendering and disclosure", Fig. 1 strips, Sec. 8 "Implications" ("so that readers know when positions can be trusted").
*What is wrong:* (i) The only disclosure in the paper is a per-frame scalar strip. No figure marks *which* features are misplaced, although the paper says the best witness explains 92–94% of τ* and would be the natural unit to disclose. `prototypes/output/fig_witness.png` already contains a legible witness overlay (vertical span plus ring marker per frame, and a bipartite q→u panel) with ▼ marks for relaxed steps, but it is not in the paper. (ii) The strip's value for a reader is untested, and the authors' own RQ2 data argue against it. In `replicate_{era5,era5_2014,wildfire}.json` (k = 2), the frame flag (H > θ at t or t+k) covers 85–92% of clear pairs. Its reversal-rate lift (flagged / unflagged) is 0.81 for TMTM and 1.00 for ST-MTM on ERA5, and 1.08 for ST-MTM on ERA5-14. For those maps the flag is nearly always on and barely discriminates. The feature-level flag (|u−q| > θ) covers 77–93% of clear pairs for the anchored layout. A disclosure that is on almost everywhere tells a reader little. (iii) Sec. 8 reports that per-feature ticks were "illegible on ERA5" but shows neither what was tried nor any alternative.
*Minimal fix:* Add a witness view: a zoomed time window as in `fig_witness.png`, or witness markers on Fig. 1b. Report the flag share and lift numbers in Sec. 7.3, and soften the Implications sentence to what the data show: the certificate tells designers when *no* hierarchy-preserving map can be trusted; it does not tell readers which pairs to distrust. If the claim stays, a small study with 5–8 participants reading the strips would be the right evidence.

**W2 — MAJOR. The relaxation's topological change, and the value changes made by the barrier filling, are invisible on the map.**
*Where:* Sec. 5.3 (barrier filling "clipping each segment to b_k and raising its existing peak"), Sec. 6 "Rendering and disclosure", Fig. 1c, Fig. 2 panels 5–6.
*What is wrong:* After relaxation, a reader performing T1 (Sec. 3.2) reads merge levels and depths from the colormap. The map alters displayed scalar values between anchors by up to δ* and interleaves a flattened subtree with other leaves. Only a frame-level δ* dot (on a secondary axis) records this. Nothing says *which* pair's merge is misreported or *where* the altered pixels are. In Fig. 2 panel 5 even the author-facing diagram does not mark the separated leaves (orange and yellow). A value that was changed for layout reasons and is shown in the same colormap as data is a visual-honesty problem that InfoVis reviewers will raise.
*Minimal fix:* Mark relaxed columns (the ▼ glyph from `fig_witness.png`). Mark separated subtrees with a thin margin bracket or connector between their leaves. Mark clipped or raised barrier segments with hatching or a desaturated band, so every non-data pixel is identifiable. State in Sec. 6 that the barrier filling changes displayed values and bound the change by δ*.

**W3 — MAJOR. The task abstraction is only partly justified, and the proxy ignores how people read vertical distance between curves.**
*Where:* Sec. 3.2 (T2/T3), Sec. 1 paragraph 3 (TMTM 33.7%), Sec. 7.3, Table 2, Fig. 1b/c.
*What is wrong:* (i) T2/T3 are justified by ST-MTM's intent and by Franke et al., which is reasonable for ST-MTM. TMTM, however, optimizes the overlap of consecutive columns, which is temporal coherence, not position. Leading the introduction with "TMTM reverses 33.7%" reads as evaluating a design on a task it never claimed. (ii) The reference axis is never labelled for the reader. Fig. 1's vertical axis says "1-D position" with no ticks, orientation or compass, so a reader cannot perform T2 on the displayed figures. (iii) The proxy judges approach and separation from exact *vertical* distance. Humans judging the gap between two curves are biased toward the *perpendicular* distance when the curves are steep (Cleveland & McGill 1984; VanderPlas & Hofmann 2015, sine illusion). Fig. 1b/c show that the reference-anchored and relaxed maps produce much steeper tracks than ST-MTM, because features now move along the axis, so the proxy's advantage may partly vanish for human readers. (iv) The proxy's truth is 2-D distance, but the map encodes a 1-D projection. The paper never reports the ceiling reached by a map with u = q exactly, so readers cannot tell how much of R's 13–15% reversal rate is hierarchy and how much is projection.
*Minimal fix:* Add an "oracle u = q" row to Table 2. Add a proxy variant that uses perpendicular (aspect-ratio-aware) distance between track segments, or at least discuss the bias in Sec. 8. Draw geographic ticks along the reference direction (km along d, with orientation such as "SW → NE") on Fig. 1b/c. This is a genuine design benefit of the method, because anchors lie within B_t of q, so ticks with a ±B_t error band are legitimate there, unlike on TMTM. Lead the introduction's example with ST-MTM rather than TMTM.

**W4 — MAJOR. Figure legibility at print size.**
*Where:* All figures. Estimated from the generating scripts (figsize → printed width):
- Fig. 3 (toy): 11 in → about 3.4 in column, scale about 0.30. Titles are about 2.9 pt and labels about 3 pt, unreadable in the PDF.
- Fig. 2 (pipeline): 14 in → 7 in. Body 3.5 pt, legend 3 pt, "reference q"/"1-D layout" 3.25 pt. The panel 6 strip has no axis, scale or legend.
- Fig. 1 (teaser): 13 in → 7 in. Strip legends about 3.5 pt, hPa ticks about 3.8 pt. It uses a dual y-axis (% axis vs hPa), which is known to invite false comparisons (Isenberg et al. 2011).
- Fig. 6: 14 in → 7 in. Suptitle about 5 pt and duplicates the caption. The x-label is clipped ("(% row"). The legend overlaps the displacement trace.
- Fig. 5: panel titles are code identifiers (`era5_2014`), and "d_top" / "q_A" appear as plain text instead of math. The shared 0–70% x-range wastes most of the Ring/Gaussians panels.
- Fig. 4: the legend overlaps the ERA5 bars near t ≈ 28.

*Minimal fix:* Re-render every figure at its final printed size (3.4 in or 7 in), with fonts ≥ 7 pt and math labels. Drop suptitles that repeat captions. Replace the dual axis in Fig. 1c with two stacked thin strips. Give each dataset panel a human-readable title.

**W5 — MAJOR. Missing algorithmic related work; the positioning against layout algorithms is thin.**
*Where:* Sec. 2 "Hierarchy-constrained orders" and "1-D placement".
*What is wrong:* The following closely related lines are absent:
- Storyline layout, where 1-D orders per time step are constrained by a location hierarchy and optimized for crossings and wiggles: Tanahashi & Ma 2012; Liu et al. StoryFlow 2013, which uses hierarchical location constraints and is the closest analogue; van Dijk et al. 2016/2017 on block crossings; Gronemann et al. 2016.
- Tanglegram layout with tree-consistent orders: Fernau, Kaufmann & Poths 2010; Buchin et al. 2012.
- PQ-trees and consecutive-ones (Booth & Lueker 1976). Π(T) is exactly the frontier set of a PQ-tree with only P-nodes. Q-nodes would model OLO-fixed or reversal-only children and would matter for RQ4.
- Matrix reordering and seriation surveys (Behrisch et al. 2016), and dendrogram reordering to external weights (Gruvaeus & Wainer 1972).
- Temporal 1-D MDS over time (Jäckle et al. 2016, Temporal MDS Plots), which is the closest non-hierarchical design for T2/T3.
- Stability of hierarchical spatial layouts (e.g., Tak & Cockburn 2013 on Hilbert/Moore treemaps; Vernier et al. 2020 on treemap stability).

On the algorithmic side, feasibility for fixed τ is single-machine scheduling with release times and deadlines, and τ is a symmetric max-lateness/earliness objective. Contiguity of subtrees is the nested "family" (group-technology) constraint of batch scheduling. That literature may settle the open NP-hardness question for unbounded degree stated in Sec. 8, or give a better algorithm than O(2^m mN) per m-ary node.
*Minimal fix:* Add a short paragraph that positions the certificate against storyline/tanglegram crossing minimization (sum-type objectives, different from bottleneck position), PQ-trees and seriation. Mention the scheduling view as a lead for the open complexity question. Re-check that none of these give Thm. 1 for binary trees as a known special case; I do not believe they do, but the paper should say so.

**W6 — MAJOR (for RQ4). The dendrogram transfer is a convincing sketch, not yet a design contribution, and one statement does not match the code.**
*Where:* Sec. 7.5, Fig. 6.
*What is wrong:* (i) The text says cells must be displaced "from its geographic *rank-scaled* position". In `prototypes/generality.py` the 67% uses a *linearly* scaled principal-axis projection (`q = (proj − min)/ptp·(n−1)+.5`). With the rank reference the certificate is 78–82% (`generality.json`, `rank_reference`). (ii) Because the reference is linearly scaled while rows have equal height, even the geography-sorted order in Fig. 6 (right) deviates by 21% (τ_free). The caption does not explain this, and readers will expect 0%. (iii) A bottleneck over 1024 rows can be driven by a handful of cells. OLO's median displacement is 14%, and only 7.7% of rows exceed τ* (`dendrogram_demo.json`). The conclusion that "row position approximates location is untenable" therefore needs a distributional statement, not only a maximum. (iv) A principal-axis projection of 2-D Australian fire cells is itself a weak notion of "location". The design question a pixel-display designer asks is usually against a space-filling-curve order (Hilbert, as in MotionRugs and Franke et al.).
*Minimal fix:* Use the rank reference, or correct the word "rank-scaled". Explain the 21% in the caption. Report τ* after removing the 1% most-displaced cells, or the fraction of rows any dendrogram order must displace by more than x, to show robustness to outliers. Add a Hilbert-order reference. Also confirm that [9]'s "hierarchical orderings" cluster time series rather than locations; as written, the paper attributes the time-series dendrogram to [9].

**W7 — MINOR. Trade-offs the paper does not report.**
*Where:* Sec. 7.3, Table 2.
*What is wrong:* The supplementary script `prototypes/quality.py` (not referenced in the paper) shows two things. First, the relaxed map has far fewer spurious order flips between consecutive steps than any baseline: 0.4–0.5% vs 7–12% for ST-MTM on real data. This is a strength the paper leaves out, and temporal stability is what MotionRugs and stable-summary readers care about. Second, ST-MTM is clearly better on 2-D neighbourhood measures on pressure: NN preservation 0.78 vs 0.45 and Spearman 0.72 vs 0.46 on ERA5. Also, reversal and miss rates are traded off (fire: R 3.6/29.5 vs ST-MTM 21.4/14.3), and TMTM misses are "omitted for space" although the table has room.
*Minimal fix:* Add a stability column and an NN-preservation column (or a sentence each). Report reversal + miss, or a balanced error, next to the two separate rates. Fill in the TMTM misses.

**W8 — MINOR. θ is called a "legibility constant" without perceptual grounding.**
*Where:* Sec. 6 "Gate" and "Constants".
*What is wrong:* 2% of the axis (8 px on 400 px) is a reasonable engineering choice, but "legibility" suggests a perceptual threshold that is not cited or measured. Positional JNDs on a common scale are much smaller than 8 px.
*Minimal fix:* Call θ a "tolerance" or "reporting threshold", keep the 1%/5% sensitivity, and drop the word legibility or cite a basis for it.

**W9 — MINOR. Fig. 1 tries to make three points; (b) and (c) look almost identical at print size.**
*Where:* Fig. 1.
*What is wrong:* The panels use three different strip encodings (avoidable/unavoidable, space/hierarchy, error/δ* on a dual axis), and the visual difference between (b) and (c) is carried only by the strips. The white tracks have low contrast over the light end of magma in (a).
*Minimal fix:* Make the teaser one point. Either show ST-MTM vs relaxed with the same strip encoding and marked relaxed columns, or keep three panels but add a zoomed inset where relaxation visibly changes a track. Use a dark outline or halo on the track lines.

## Detailed comments by section

- **Sec. 1, para 3.** "No existing method certifies the unavoidable deviation" is fair for merge tree maps. Say "to our knowledge" for clustered heatmaps, since tree-constrained seriation against external orders has a long history (see W5).
- **Sec. 3.2.** Good addition. Add a sentence on *who* the reader is (a meteorologist scanning a season? an analyst of fire spread?), and say whether T2/T3 are primary or secondary tasks. The PCA-of-motion direction is a sound default. MotionRugs already offers PCA-based orderings, so cite that as precedent.
- **Sec. 3.4 / Fig. 3.** The toy is excellent didactically. Mark the witness (A,B;C) in the figure itself: bracket the subtree {A,B} and highlight C. Doing so would introduce the witness visual vocabulary early.
- **Sec. 4.2, Thm. 1.** Note the structural similarity to the Bar-Joseph OLO DP, and to PQ-tree frontier enumeration.
- **Sec. 4.3.** The "best monotone calibration" for existing maps is generous, which is good for fairness. State explicitly in the Fig. 1a caption that ST-MTM's axis has been recalibrated, because ST-MTM's own axis has no reference semantics.
- **Sec. 6 "Threshold and prune".** From a reader's view, flattening changes adjacency between frames. Does the relaxed set W flicker between consecutive frames? If it does, the relaxation itself is a source of temporal instability. Report how often W changes between consecutive steps.
- **Sec. 7.4 / Fig. 5.** The y axis aggregates by mean and the x axis by max. That is why the aggregate points lie above F, which the text has to explain. Consider per-frame scatter or a paired per-frame distance-to-frontier histogram, which would make the "98% on the frontier" claim visible.
- **Sec. 7.5.** "The computation takes 0.1 s" is a strong selling point for designers. Consider stating it as a check a pixel-display tool could run on the fly before offering "row ≈ location".
- **Sec. 8 Negative results.** Show the illegible per-feature ticks in the supplement. Negative design results are informative only if one can see them.

## Questions to authors

1. What is the proxy reversal rate for an oracle map with u = q? How much of R's residual reversal is due to projecting 2-D motion onto one direction?
2. With the frame flag covering 85–92% of clear pairs and lift ≈ 1 for ST-MTM, what reader decision does the certificate strip support in practice? Did you test any disclosure design with people, even informally?
3. In relaxed columns, which pixels differ from the LCA-path filling, and by how much in value units? Can a reader tell them apart from data?
4. For RQ4, which reference produced 67%: linear-scaled or rank-scaled? How robust is τ* to removing a few outlier cells?
5. Does the relaxed node set W change between consecutive frames, and if so, how often?
6. Have you considered Q-nodes (fixed or reversal-only child orders), which would model displays where the OLO order within a cluster is to be kept?
7. In Fig. 2 panel 1, several extrema appear on the domain boundary. Are boundary minima filtered, and does the automatic direction depend on them?

## What would raise my score by one point

Show the witness triple and the relaxed or altered pixels on the map (W1, W2): include the existing `fig_witness.png`-style view and mark barrier-modified segments. Report the frame-flag share and lift honestly and temper the "readers know when to trust" claim. Add the oracle row and a perpendicular-distance variant (or discussion) to the proxy (W3). Re-render all figures at print size with ≥ 7 pt fonts and no dual axis (W4). Add the storyline, tanglegram, PQ-tree and seriation references with one paragraph of positioning (W5). Correct the rank-scaled statement in RQ4 (W6). With those changes I would move to 4 (accept).
