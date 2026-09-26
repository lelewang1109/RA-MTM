# R0 — EIC / Papers Chair report

**Paper:** "How Faithful Can a Hierarchy-Constrained 1-D Layout Be? Certified Position–Topology Trade-offs for Merge Tree Maps and Beyond" (PacificVis 2027, Conference Paper Track, review version)

**Materials read:** compiled PDF `paper_v1.pdf` (all 8 pages), the uncommitted diff of `main.tex` (new Sec. 3.2 "Tasks and the role of the reference", λ/β notation fix, θ sensitivity, NP-hardness remark), `refs.bib`, and spot checks of `prototypes/misreading.py` and `prototypes/relax_hierarchy.py` to confirm which configuration Table 2 reports.

## Reviewer role and identity

EIC / Papers Chair (Reviewer 0). PacificVis papers co-chair; I work on scientific visualization of time-varying fields and topology-based visualization, and I have served on IEEE VIS and EuroVis PCs.

**Review focus.** Venue fit (is this a visualization paper or a computational-geometry paper?), originality and significance to the vis community, positioning against TMTM / ST-MTM and hierarchy-constrained ordering work, coherence of the story from teaser to conclusion, and presentation: VGTC compliance, anonymity, page use, figure legibility, captions, and references.

## Recommendation

- **Recommendation:** Major Revision. For a conference track this means: accept only if the presentation and claim issues below are fixed. I would argue for it in discussion if they are.
- **PacificVis score:** 3 / 5 (borderline, leaning positive)
- **Confidence:** 4 / 5

## Summary assessment

The paper asks a clean, well-posed question that the community has not asked before: when a 1-D space–time display must keep a hierarchy contiguous (merge tree maps, dendrogram-ordered pixel displays), what is the smallest positional error that *any* admissible layout must accept, and what does it cost in topology to reduce it? The answer has three parts. The first is a closed-form, exactly computable certificate τ\* that splits into a hierarchy cost and a space cost and names witness triples. The second is a filling-independent lower bound on merge-level distortion when contiguity is broken, plus an optimal filling in closed form. The third is an exact position–topology frontier. These are original, correct as far as I checked, and useful as a lens for evaluating layouts. The empirical characterization is careful and unusually honest: negative results are listed, the proxy is labelled as a proxy, and consistency checks are listed.

My concerns are about how the paper is positioned and presented, not its correctness. (1) The visualization contribution, meaning the map a reader actually sees and the disclosure strips, gets less space and less evaluation than the theory. Meanwhile about 2.5 of the 9 body pages are unused. (2) The headline numbers combine different operating points. The reversal reduction "to 4–15%" is at unbounded relaxation, while "98% on the frontier" is at κ = 2%. The fire miss-rate penalty is left out of the abstract. (3) The comparison with TMTM and ST-MTM on a positional task needs more careful framing. The ST-MTM reference is an author-less, unpublished preprint that was reimplemented, and this is not disclosed. (4) The PDF has submission-blocking format issues: visible TODOs, figure text of about 4–5 pt, and a clipped axis label.

## Strengths

- **S1 — Novel, well-posed question with a "what can any layout achieve" framing (Sec. 1, p. 1–2; contributions list).** The shift from "measure the produced layout" to "certify the unavoidable error over all admissible layouts" is a real contribution to how the vis community evaluates layouts. The Related Work paragraph "Faithfulness, distortion, and trade-offs" (p. 2) states this difference precisely.
- **S2 — The theory is compact and its components connect (Sec. 4–5, pp. 3–4).** The closed form for a fixed order (Prop. 1), the hierarchy/space decomposition with witness triples (Prop. 2), the width-free certificate that applies to TMTM/ST-MTM whatever their width model (Prop. 4), the topological price of non-contiguity (Thm. 2) tied to the labelled interleaving distance, and the exact frontier (Thm. 3) that follows from combining the two closed forms. The link to the ℓ∞-cophenetic / interleaving distance (Sec. 5.1) is a nice bridge to the TDA-in-vis literature.
- **S3 — Toy example and pipeline figure make the idea graspable (Fig. 3, Fig. 2, p. 3).** The three-leaf conflict in Fig. 3 shows the whole phenomenon in one line. The ① to ⑥ pipeline in Fig. 2 traces a real ERA5 frame from certificate to relaxed map, and the numbers in the "Case" paragraph (Sec. 7.4, p. 6) match it.
- **S4 — Evaluation discipline and honesty (Sec. 7.1 "Checks", Sec. 7.2 robustness, Sec. 8 "Negative results", p. 5–7).** The paper checks every rendered frame against the theorems, tests sensitivity to direction, width model, and (new in the source) θ, uses paired block-bootstrap intervals, reports a permutation null, and states that the proxy is not a human study. Listing negative results (radial references, stability-priority policy, illegible per-feature strips) is good practice and helps credibility.
- **S5 — Transfer beyond merge trees (Sec. 7.5, Fig. 6, p. 6–7).** The dendrogram demonstration turns the certificate into a practical design verdict ("row position approximates location is untenable here"). This is the kind of actionable use that vis readers value, and it partly supports "and Beyond" in the title.

## Weaknesses (ranked by impact on acceptance)

### W1 — MAJOR: The visualization contribution is under-shown and under-evaluated, and about 2.5 pages are unused (venue fit)
**Where:** whole paper. Body ends near the top of p. 7's right column, so roughly 6.1 of 9 body pages are used. The only full views of the proposed map are the three small teaser panels (Fig. 1, about 1.8 in tall each) and panel ⑥ of Fig. 2 (about 1 in). The disclosure design ("Rendering and disclosure", Sec. 6, p. 5) is one paragraph.
**What is wrong:** As it stands, the paper reads as an algorithms/geometry paper that happens to use vis data: 3 theorems, 5 propositions, 1 corollary, 2 algorithms. The part a PacificVis reader will use, the certificate-driven map with its strips, is never shown large enough to read. It is never walked through with a domain question, and its encoding choices are not justified. The teaser panels (a)/(b)/(c) look alike at print size, so the reader cannot see the reversal the paper is about. Sec. 8 reports that per-feature disclosure strips were "illegible on ERA5", yet the remaining per-frame strip design is not evaluated either.
**Minimal fix (uses the free pages, no new experiments needed):**
1. Add a full-width case-study figure. Show an ERA5 window rendered by ST-MTM and by the relaxed method. Annotate one pair of lows whose 24 h approach is reversed on ST-MTM and correct on the relaxed map. Put the 2-D ground truth (small map snapshots) beside it.
2. Expand "Rendering and disclosure" into a short design subsection. Explain why bars vs. dots, why a dual axis (% axis vs. hPa), how the relaxed nodes are marked in the map itself (dashed merges as in Fig. 2 ④?), and how a reader should use the strips.
3. Add a short worked walkthrough ("an analyst asks X; the strip shows Y; therefore Z"), which also supports the new task section (Sec. 3.2 in the source).
4. Optional but helpful for fit: informal feedback from one or two meteorology users on whether T2/T3 are real tasks on merge tree maps.

### W2 — MAJOR: Headline numbers combine operating points; the trade-off is under-reported in the abstract and Table 2
**Where:** Abstract; Sec. 1 contributions; Table 2 (p. 6); Sec. 7.3.
**What is wrong:**
- The abstract says the relaxation "lowers this to 4–15%, lies on the exact frontier in 98% of time steps, and reports its topological cost exactly." The 98% (368/376 frames) is at **κ = 2%** (Sec. 7.4). The reader-proxy "R" column in Table 2 comes from `relax_frame_threshold(...)` called with the default `value_cap = inf` in `prototypes/misreading.py:60`, that is, **κ = ∞** (flatten all, then prune). The two claims describe different maps, and the abstract implies they describe one.
- Neither the Table 2 caption nor Sec. 7.3 states κ for R, or the topological cost δ\* that R pays. At κ = 20%, pressure already pays 28–32 hPa (Sec. 7.4). At κ = ∞ it may pay more. The comparison of reversal rates between tree-preserving maps (TMTM, ST-MTM, A) and a map that gives up tree fidelity is fair only if that price appears next to it.
- On fire, R's miss rate is 29.5% vs 14.3% for ST-MTM (+15.2 pts, Sec. 7.3). The abstract mentions only the reversal reduction. With n = 112, R's 3.6% is 4 cases.
- The abstract's "existing merge tree maps … 21–34%" is correct only for the real datasets (ST-MTM on Ring is 7.3%). This is fine, but the abstract should say "on real data".
**Minimal fix:** State κ in the Table 2 caption. Add a column (or a sentence) with the mean/max δ\* of R at that κ. Either report the proxy at κ = 2% as well, or rewrite the abstract so each number carries its operating point, for example "at unrestricted relaxation, reversals drop to 4–15% at a disclosed merge-level cost of X hPa; at κ = 2% the relaxation lies on the exact frontier in 98% of frames". Add "while misses rise on fire" to the abstract or intro.

### W3 — MAJOR: Positioning against TMTM / ST-MTM needs care; ST-MTM reference and reimplementation
**Where:** Sec. 1 ¶4 (p. 1), Sec. 2 "Static summaries", Sec. 3.4 last ¶, Sec. 7.1 "Methods", Table 2, Ref. [1].
**What is wrong:**
- The intro's motivating number ("opposite sign … in 33.7% of clear cases" on TMTM) scores TMTM on a task it was not designed for. TMTM orders by temporal overlap, and its 33.7% sits close to the permutation null (36–40%). Much of the effect is expected by design. The new Sec. 3.2 in the source ("The certificate therefore does not claim that TMTM or ST-MTM are wrong") helps a lot. The intro, though, still leads with the TMTM number as "the consequence is concrete", which invites a straw-man objection from TMTM-aware reviewers.
- Ref. [1] (ST-MTM) has **no authors** and is an SSRN preprint "submitted to Computers & Graphics". It is the main baseline, and reviewers can neither verify it nor tell whether it is a self-citation. If it is the authors' own work, VGTC double-blind practice is to cite it in the third person with authors listed, and to put an anonymized copy in the supplement. Removing author names is not the accepted practice and draws attention.
- ST-MTM has no public code and was **reimplemented** (per the project's provenance notes). The paper says only "published parameters for Ring, adapted defaults elsewhere" (Sec. 7.1). A reimplemented main baseline must be disclosed, together with how it was validated (e.g., reproducing the paper's Ring/Gaussian figures).
- Related work misses three strands a PacificVis PC will expect. First, **storyline layouts** (e.g., StoryFlow, Liu et al., TVCG 2013, which orders lines under hierarchical location constraints over time: a hierarchy-constrained 1-D layout stacked over time). Second, **faithfulness** in the vis sense (Nguyen, Eades, Hong, "On the faithfulness of graph visualizations", PacificVis 2013), which is directly relevant given the title word "Faithful". Third, the projection-distortion survey of Nonato & Aupetit (TVCG 2019).
**Minimal fix:** In the intro, lead with ST-MTM, which does target geometry, and the reference-anchored layout A (22.4%). Mention TMTM with a clause saying it optimizes temporal overlap, not position. Complete Ref. [1] with authors (third person) and supply an anonymized copy in the supplement. Add one sentence in Sec. 7.1 stating that ST-MTM is a reimplementation from its §4.1–4.3 and how it was checked. Add the three related-work strands (about 4 lines).

### W4 — MAJOR (format; must be fixed before submission): visible TODOs, legibility, anonymity details
**Where / what:**
- Red "[TODO: rerun on the CDS ERA5 file]" (p. 5, Sec. 7.1) and "[TODO: anonymized archive link]" (p. 7, Supplemental Materials) are visible in the PDF. "Online Submission ID: 0" appears in the header.
- **Figure text is far below legibility at print size.** In Fig. 1 (teaser) axis labels, tick labels, and legends are about 4–5 pt; the strip legends in panel (c) cannot be read. Fig. 2's panel titles and tick labels are about 4 pt. Fig. 3's panel titles are about 3–4 pt. Fig. 6's tick labels are about 5 pt, and the right panel's x-label is clipped ("|row − reference| (% row"). The figure title in Fig. 6 duplicates the caption. VGTC guidance and PC expectations are that figure text be no smaller than about 7 pt, close to caption size.
- All figures are raster PNG (150–220 dpi). The resolution is adequate, but vector PDF would fix the small-text blur for free, since the figures come from matplotlib.
- Fig. 1(c) and Fig. 2 ⑥ use a dual y-axis (% axis vs. hPa) with bars and dots. It is readable only after reading the caption.
**Minimal fix:** Remove the TODOs (or complete them). Regenerate the figures from `prototypes/paper_figs.py` at the final print width with font size ≥ 7 pt and export PDF. In Fig. 1, drop the in-figure axis titles that the caption already explains, to free space. Fix the clipped label in Fig. 6 and drop its in-figure title. Set `\onlineid` at submission time.

### W5 — MINOR: Reference-list quality
**Where:** References (p. 7–8).
**What is wrong:** [1] has no authors. [11] "H. Hersbach et al." and [29] "J. Rauscher et al." use "et al." in the bibliography. Many entries lack volume, pages, or DOIs (e.g., [10], [16], [17], [19], [21], [36], [38], [39]) even though the abbrv-doi style is loaded. [23] (Meulemans, arXiv:2607.29360) is quoted as the methodological motivation ("quality must be defined before it can be measured and guaranteed"). It must be checked to exist and to say that, since a fabricated or misattributed motivating citation would be fatal. [13] Huson 2026 and [28] Rauscher 2026 are very recent and should likewise be verified.
**Minimal fix:** Run the planned citation audit (the `% TODO` at main.tex:5). Complete all author lists, volumes, pages, and DOIs.

### W6 — MINOR: Density and notation for a vis readership
**Where:** Sec. 4.2 / Theorem 1 / Algorithm 1 (p. 3–4); separate counters for Proposition / Theorem / Corollary; the PDF uses δ for both the pixel size (Prop. 3) and topological distortion (Cor. 1, δ\*).
**What is wrong:** A vis reader will not follow E_S composition (∘) and window arithmetic without a picture. The mixed numbering (Prop. 1, 2, Thm. 1, Prop. 3, 4, Thm. 2, Prop. 5, Cor. 1, Thm. 3) makes cross-references harder to find. The δ collision is already fixed in the source (λ, β).
**Minimal fix:** Use one shared counter for all statements. Add a four-line intuition before Theorem 1 ("sweep the canvas; for each subtree record the earliest position where it can end; combine children in the best order"), perhaps with a tiny inset in Fig. 3. Consider moving the details of Theorem 1's correctness sketch to the supplement.

### W7 — MINOR: Overreach in a few linking sentences
**Where:** Sec. 7.3 (p. 6): "Keeping the hierarchy (A) performs like ST-MTM; only relaxation helps, as Corollary 1 predicts." Title: "… and Beyond".
**What is wrong:** Corollary 1 bounds the maximum positional error. It does not predict reversal rates, which depend on pairwise distance changes. "And Beyond" rests on one dendrogram demonstration (Sec. 7.5), which covers the certificate only, not the relaxation or the frontier.
**Minimal fix:** Rephrase to "consistent with Corollary 1, which bounds how far any tree-preserving map can bring features to their reference". Either keep "and Beyond" and add a sentence in Sec. 8 stating that only the certificate was shown to transfer, or shorten the title.

### W8 — MINOR: Scalability of the method vs. the certificate
**Where:** Algorithm 2 line 12; Sec. 4.2 last ¶; Sec. 8.
**What is wrong:** The certificate scales (4096 leaves in 3.6 s), but layout selection enumerates candidate orders, and the exact frontier enumerates n! (n ≤ 11 in all data). The limitation is stated, which I appreciate. The contributions list, however, presents the method without this qualifier.
**Minimal fix:** Add "for merge trees of up to about a dozen leaves per frame" to the method contribution bullet.

## Detailed comments by section (within my focus)

- **Teaser (Fig. 1).** The story from the teaser is "(a) the existing map's error, mostly avoidable; (b) the best tree-preserving map; (c) relaxation at a disclosed cost". That is the right story, but it must be visible without the caption. Add one annotated pair of tracks across (a) and (c), plus a tiny 2-D inset of the true positions. The caption is 8 lines. Shorten it once the figure speaks for itself.
- **Sec. 1.** The research question in bold is excellent. The "Following the argument that visualization quality must be defined…" sentence rests on [23]; verify it (W5).
- **Sec. 3 (source version).** The new Sec. 3.2 ("Tasks and the role of the reference" with T1–T3, "What the reference is, and is not", "Why the maximum deviation") is the most important addition for venue fit and positioning. Keep it. Consider pointing to it from the intro, e.g., "we make the task explicit in Sec. 3.2".
- **Sec. 3.4 Model.** The final paragraph comparing what TMTM/ST-MTM/A preserve (position/size/topology) would work better as a small 3×3 table. It is the clearest positioning statement in the paper.
- **Sec. 6.** The "Constants" paragraph in the source now justifies θ (8 px at 400 px height) and reports θ = 1%/5%. Good. Also state κ's default for the teaser and for Table 2 (W2).
- **Sec. 7.1.** Table 1's "range" column mixes hPa and log(1+FRP) units without units for fire. Add "(unitless)".
- **Table 2.** Define A and R in the caption. "TMTM misses are omitted for space", but space is not scarce; include them. The slash format "reversal / miss" plus bold is hard to scan. Consider separate reversal and miss sub-columns.
- **Fig. 4.** Legible and informative. The θ line is hard to see; use a darker dash.
- **Fig. 5.** Informative. The x-label unit "% of value range" differs from the hPa units used in the text; mention the conversion in the caption.
- **Sec. 8.** The "Implications" paragraph (three practices) is the right close for a vis audience. Expand it by a few sentences using the free space, e.g., what a tool builder should put in the UI.
- **Supplemental / Figure credits.** Fine. The ERA5 license acknowledgment (Copernicus) should follow the C3S wording ("Contains modified Copernicus Climate Change Service information 2026").
- **Anonymity.** No author names appear in the PDF metadata or text, and the figure credits are neutral. Only Ref. [1] (W3) and the future archive link (W4) need attention.

## Questions to authors

1. Which κ does the "R" column of Table 2 use, and what mean/max δ\* (hPa, FRP) does it pay? What are the reversal/miss rates at κ = 2%?
2. Is ST-MTM your own prior work? If not, how did you validate your reimplementation against the published figures (Ring, three-Gaussian scene)?
3. Have domain users (meteorologists, fire analysts) confirmed that T2/T3 (locate / follow motion) are performed on merge tree maps? Any anecdotal evidence would strengthen Sec. 3.2.
4. How are relaxed (flattened) merges marked in the map image itself, not only in the strip? Can a reader tell which features were affected?
5. Does the width-free certificate (Prop. 4) exceed θ for TMTM's native one-pixel-per-sample model in the same fraction of frames as reported for the width-free variant in Sec. 7.2?

## What would raise my score by one point (3 → 4)

Use the unused ~2.5 pages for **one annotated full-width case-study figure** (ST-MTM vs. relaxed map with a highlighted reversal and 2-D ground truth) and a **short disclosure-design subsection**. **Tie every headline number to its κ and report δ\* next to the reader-proxy rates** (including the fire miss trade-off in the abstract). **Fix the format blockers**: TODOs, figure fonts ≥ 7 pt, a complete and verified ST-MTM citation with a disclosed reimplementation, and a completed bibliography. None of this needs new theory. It turns a strong algorithmic contribution into a convincing visualization paper.
