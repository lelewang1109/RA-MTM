# R4: Devil's Advocate Review

**Role and identity.** A skeptical senior visualization researcher whose job is to find the strongest reason to reject.
**Focus.** I checked whether the core argument holds up, whether the evaluation is circular or cherry-picked, and whether each headline number in the abstract can be traced to the body and to `prototypes/output/*.json`. I read the PDF (v1), the newer `main.tex`, `proofs.tex`, and the outputs and scripts that produce the numbers (`replicate_*.json`, `attainable_*.json`, `pointcert.json`, `quality.json`, `generality.json`, `robustness.json`, `misreading.py`, `relax_hierarchy.py`, `generality.py`, `pointcert.py`, `theory.py`).

---

## Strongest Counter-Argument

The theory is correct and tidy. The paper's value, though, rests on a practical claim: the certificate changes what practitioners do, because it tells readers when positions can be trusted and it drives a relaxation that fixes motion readings. Two of the paper's own outputs undercut that claim.

**The frame-level certificate does not locate the errors of existing maps.** Over k = 2 windows, the conflict flag (H > θ at t or t+k) covers 85–92% of all clear cases on the real datasets. Its lift on TMTM/ST-MTM reversals is 0.81 and 1.00 on ERA5: reversal rates in flagged and unflagged windows are 32.6% vs 40.4% (TMTM) and 24.9% vs 25.0% (ST-MTM) (`replicate_era5.json`, `T2D_frame_flag_lift`). A flag that fires almost everywhere and does not predict error amounts to "never trust position on these maps". Nobody needs a pseudo-polynomial DP to say that.

**The reported relaxation gain is close to tautological.** The "R" column of Table 2 is produced at κ = ∞: `misreading.py` calls `relax_frame_threshold(...)` with the default `value_cap=np.inf`. At that setting R reproduces the reference projection exactly (its "claim" reversal rate against its own axis is 0.0% on every dataset). The worst-frame merge-level distortion is 55–57 hPa with the optimal filling and about 58 hPa with LCA, out of a value range of 85–113 hPa. So Table 2 shows that a 1-D projection onto the principal-motion direction, which was computed from the same tracks the proxy scores, reproduces motion better than maps that were never asked to encode that direction. A Hovmöller-style plot of the tracked extrema along d would probably do the same, and it has no merge tree to distort.

Meanwhile, the abstract pairs this κ = ∞ gain with a "98% on the exact frontier" figure taken at κ = 2%. That figure is identical (368/376) when no relaxation is applied at all. On the one dataset where ST-MTM runs with its published parameters (Ring), ST-MTM beats R (7.3% vs 10.5%).

Put together: the theory is a solid, incremental result about a niche display family, and the evaluation does not yet show that it changes any practice.

---

## Issue List

### CRITICAL

**C1. The abstract mixes three operating points of κ, and the operating point behind the reader proxy is undisclosed.** *Dimensions: claims / evidence. Locations: Abstract; Table 2; Sec. 7.3; Sec. 7.4; Fig. 1 caption.*
- The 4–15% reversal figure (Table 2, "R") uses κ = ∞: `misreading.py` line 60 calls `relax_frame_threshold` without `value_cap`, and the default is `np.inf`.
- At κ = ∞, the worst-frame merge distortion (optimal filling) is 0.650 × 85.4 ≈ 55.5 hPa on ERA5 and 0.506 × 112.8 ≈ 57 hPa on ERA5-14 (`attainable_*.json`, `D_opt_share`). With LCA it is about 58 hPa (`replicate_*.json`, `merge_err_max`: 58.1 and 58.5). All 68 and 74 conflict frames are relaxed.
- "Lies on the exact frontier in 98%" is the κ = 2% figure (368/376), and the teaser uses κ = 20%.
- Neither the paper nor Table 2 states which κ produced R, so a reader will pair "4–15%" with the "1.4–2.1 hPa" cost quoted in Sec. 7.4. That pairing is wrong by more than an order of magnitude.
- *Minimal fix:* state κ in the Table 2 caption and in the abstract. Report proxy reversal and miss rates for R at κ ∈ {2%, 20%, ∞} next to the corresponding δ\*. Rewrite the abstract so that every number comes from one stated operating point, or give the trade-off explicitly (e.g., "at κ = X, reversals fall to Y% at a maximum merge distortion of Z hPa").

### MAJOR

**M1. The "98% on the exact frontier" statistic does not discriminate.** *Dimensions: logic / claims. Locations: Abstract; Sec. 7.4 "Optimality".*
- With no relaxation at all (κ = 0), `frames_pareto_optimal` sums to 117+120+28+39+64 = **368/376**. That is exactly the κ = 2% figure, because F_T(0) = τ\* and layout A picks a τ\*-optimal legal order.
- At κ = 2%, only 54 of 376 frames are relaxed at all (15/19/14/6/0; `replicate_*.json`, `frames_relaxed`). The 64 Gaussian frames are never relaxed at κ = 2%.
- If all 8 off-frontier frames are relaxed ones, the rate among relaxed frames could be as low as 46/54 = 85%.
- *Minimal fix:* report frontier membership over relaxed frames only, per κ (per-frame data are already computed in `attainable.py`), and drop the pooled 98% from the abstract. Also note that frontier membership at large δ\* is easy, because F flattens toward τ_free.

**M2. Circular evaluation in RQ2.** *Dimension: logic. Locations: Secs. 6 "Reference", 7.3; Table 2.*
- The reference direction d is the principal direction of tracked extremum displacements, estimated from the same tracks whose 2-D distance changes define the proxy's ground truth.
- R is additionally fitted with a motion-residual term toward that reference.
- TMTM and ST-MTM never see d.
- The comparison therefore measures, in part, which method was told the answer direction. The sentence "only relaxation helps, as Corollary 1 predicts" is also a non-sequitur: Corollary 1 bounds maximum positional error, not sign agreement of pairwise distance changes.
- *Minimal fix:* (a) add a no-hierarchy baseline that plots extrema at q along d (a track Hovmöller). R at κ = ∞ should be near this ceiling, and the gap between them is the real cost of keeping topology. (b) Estimate d on held-out time (first half / second half) or use a fixed a-priori direction for everyone. (c) Remove the "as Corollary 1 predicts" clause.

**M3. The windows k are cherry-picked, and the baseline's parameterization is confounded.** *Dimension: evidence. Locations: Sec. 7.3 "stable for ... windows of 1, 2, and 4 steps"; Sec. 8.*
- `misreading.py` computes k ∈ {1, 2, 4, 8}, but the paper reports only 1/2/4.
- At k = 8, R is worse than ST-MTM on ERA5-14 at ε = 2% (28.9% vs 24.4%) and ε = 5% (21.6% vs 13.5%); it is better only at ε = 1% (31.1% vs 37.8%). R is also worse on ERA5 at ε = 5% (13.4% vs 9.0%) (`replicate_*.json`).
- On Ring, the only dataset where ST-MTM runs with its published parameters, ST-MTM beats R at ε = 2% for every k: 8.5 vs 12.8, 7.3 vs 10.5, 5.7 vs 8.6, and 0.0 vs 12.5 for k = 1, 2, 4, 8. R wins at ε = 1% and 5% for k ≤ 4, so the ranking on Ring depends on the threshold. ST-MTM also beats A by about 3× (7.3% vs 24.2%).
- On the real data, ST-MTM uses "adapted defaults", and its parameter sensitivity is explicitly not studied.
- *Minimal fix:* report all k, including k = 8 with its n. Tune ST-MTM on the real datasets under a documented protocol, or at least give an ST-MTM sweep. Soften "significantly less often ... on all three real datasets" accordingly.

**M4. The wildfire bootstrap is underpowered.** *Dimension: evidence. Location: Sec. 7.3 "paired 95% intervals exclude zero".*
- Wildfire has 30 frames, and `paired_differences` uses blocks of 8. That gives 4 blocks, whose resamples take at most 35 distinct compositions, so percentile CIs are coarse. The missed-rate CI [0.04, 0.40] shows the instability.
- There are no multiplicity corrections across 3 datasets × 3 comparisons × 4 k × 3 ε.
- *Minimal fix:* use smaller blocks (e.g., 2–3 frames) with a stated rationale, or a pair-level permutation test. Report fire as indicative. Apply a correction such as Holm, or pre-register the single primary comparison (k = 2, ε = 2%, R vs ST-MTM).

**M5. R's own disclosure strip is silent on most of its remaining reversals.** *Dimensions: claims / framing. Locations: Sec. 6 "Rendering and disclosure"; Sec. 8 "Implications".*
- R's feature flag (|u−q| > θ) catches only 26% (ERA5) and 13% (ERA5-14) of R's reversals. For layout A the same flag catches 96% and 91%.
- The unwarned reversal rate is 9.6% for R vs 0.85% for A on ERA5, and 13.0% vs 1.9% on ERA5-14 (`T2D_feature_flag_recall`, `T2D_unwarned_reversal_rate`).
- R's residual errors come from projection loss, which a reference-relative certificate cannot see by construction. The strips therefore show "max error ≈ 0" while about 1 in 8 clear motion readings is reversed, which is false reassurance.
- *Minimal fix:* report unwarned reversal rates for A and R. State in Sec. 6/8 that the strips certify faithfulness to q, not to 2-D motion. Consider the alternative path below (A plus feature-level disclosure).

**M6. The frame-level disclosure claim is not supported for existing maps.** *Dimensions: claims / evidence. Locations: Sec. 8 "Implications" ("disclose the certified deviation, so that readers know when positions can be trusted"); Sec. 3.2.*
- On TMTM/ST-MTM, the frame conflict flag has lift 0.81 and 1.00 (ERA5) and 1.65 and 1.08 (ERA5-14). It covers 85–92% of clear cases.
- *Minimal fix:* report flag share and lift. Restrict the "readers know when to trust" claim to layouts that target q, since A has lift 1.2–1.3 and feature recall above 90%.

**M7. "Hierarchy cost" is partly a projection artefact, and "space cost ≤ 5%" is close to tautological.** *Dimensions: logic / framing. Locations: Sec. 7.2 ("it is the hierarchy that prevents it"); Fig. 4 caption; Intro, the "third low lies geographically between them" example.*
- τ_free minimizes over all permutations, so sorting by q attains near-zero error apart from width packing. Against any 1-D reference, almost all deviation is therefore attributed to the hierarchy by construction.
- A 2-D-adjacent merged pair can straddle a third low only in projection, so the conflict can be between the hierarchy and the projection rather than between the hierarchy and space.
- Two pieces of the paper's own evidence support this. A purely spatial single-linkage dendrogram still has H = 32.5% (RQ4). And the conflict share ranges from 23% to 77% across eight directions; on ERA5 at 90° it is 26% (`robustness.json`).
- *Minimal fix:* rename "space cost" to "packing cost". Qualify "58–63%" as "under the principal-motion reference" in the abstract. Add a statistic that separates projection-induced from hierarchy-induced conflict, e.g., the share of witness triples whose 2-D geometry is also inverted (k lies inside the convex hull or on the geodesic between i and j).

**M8. The "single global constant" claim contradicts the method.** *Dimension: claims. Locations: Contribution bullet 3 ("it has a single global constant"); Sec. 6; Alg. 2 header ("budget κ").*
- κ selects the entire trade-off: at κ = 2%, 11–13% error reduction on pressure; at κ = ∞, 84–87%. It is also set differently in different parts of the paper (the teaser uses 20%, RQ2 uses ∞).
- *Minimal fix:* call κ a user-facing trade-off parameter, say how a practitioner picks it, and use one default consistently.

**M9. "and Beyond" and the dendrogram transfer are overgeneralized, and the RQ4 wording does not match the computation.** *Dimensions: claims / framing. Locations: Title; Abstract; Sec. 7.5; Fig. 6.*
- There is a single demo on one dataset.
- The text says "geographic rank-scaled position", but the reported 67%, 47–48%, 1.4% and 32.5% come from the **linearly scaled** reference (`generality.py` line 41; `generality.json` "hierarchies"). With the rank reference, τ\* is 78–82% (`generality.json` "rank_reference"). The figure itself shows that sorting by geography deviates by up to 21% under the linear reference.
- The "design question" is close to self-evident: a dendrogram of fire time series has no reason to be spatially ordered.
- If the hierarchy of Franke et al. is spatial, the realistic case is the spatial Ward dendrogram, where H = 1.4% and the certificate finds no problem.
- *Minimal fix:* drop "and Beyond" or add a second, non-trivial transfer case (e.g., geophylogeny or clustered heatmap against an external order). Fix the reference wording and report both references. Check what hierarchy Franke et al. actually use.

**M10. Scope and scalability are hidden in the pipeline.** *Dimension: evidence. Locations: Alg. 2 line 3; Sec. 7.1 datasets; Sec. 7.6.*
- The gate computes τ_free by enumerating n! orders, and layout selection enumerates Π(T′). The exact frontier needs n!.
- Every real dataset was smoothed until n ≤ 11–12 (fire: "the smallest smoothing that yields at most 12 maxima"), so the method and the frontier results cover only heavily simplified trees.
- The open NP-hardness question (Sec. 8) looks closely related to single-machine sequencing with release times and deadlines (1|r_j, d_j|·, strongly NP-complete for arbitrary slacks). The star tree gives τ\* = τ_free.
- *Minimal fix:* state the n! components in Alg. 2 and Sec. 6, justify the smoothing rule as a scope decision, and investigate or remove the "open" claim in light of the sequencing literature.

**M11. The optimal "barrier filling" changes displayed data values, and this is never measured.** *Dimensions: presentation / claims. Locations: Sec. 5.3; Sec. 6 "Rendering".*
- Clipping segments to b_k and raising peaks to b_k displays pressure or FRP values that are not in the field. "No new extrema" does not make the displayed column faithful in value.
- *Minimal fix:* report the maximum and mean |g − original column| per frame and mark modified pixels, or else show the LCA filling with δ\* disclosed.

### MINOR

- **m1.** *Presentation. PDF p. 5 and p. 7.* The PDF contains red "[TODO: rerun on the CDS ERA5 file]" and "[TODO: anonymized archive link]" markers, and "Online Submission ID: 0". Remove them.
- **m2.** *Presentation. PDF Prop. 3, Alg. 2.* δ is used for both pixel size and distortion, and Δ for the budget. The tex fixes this (λ, β); recompile.
- **m3.** *Presentation. Alg. 1 lines 3–4.* The canvas clipping (lo_i ≥ 0, hi_i ≤ N − W_i) that `theory._leaf_E` applies is omitted. Add it.
- **m4.** *Evidence. Sec. 4.1.* "The best witness explains a median of 92–94% of τ\*" has no saved output in `prototypes/output/`. Add it to a JSON.
- **m5.** *Evidence. Sec. 7.2 / Fig. 1a.* The "avoidable 17–23%" for TMTM and ST-MTM allows only non-decreasing calibration (`pointcert.py` uses `argsort(u)` without flipping). Their axes have no orientation tied to d, so also allow non-increasing calibration (global or per frame) before calling the remainder "avoidable".
- **m6.** *Presentation. Sec. 7.4 vs Fig. 5.* The "Cost" paragraph uses mean per-feature reference error (`ref_err_mean`), while Fig. 5 plots mean-over-frames of max error against max-over-frames d_top. Use one metric, or say which is which.
- **m7.** *Logic. Sec. 5.2.* "It holds for TMTM, ST-MTM" is vacuous, because both keep contiguity. Rephrase as "any method that breaks contiguity".
- **m8.** *Framing. Sec. 6 "Constants".* θ = 2% ("legibility constant") is justified only as 5× the gap. Either cite a perceptual basis or call it a reporting threshold (the sensitivity at 1% and 5% is already given).
- **m9.** *Claims. Sec. 7.4.* "Theorem 2 holds in all 924 rendered frames" is a sanity check of a proved statement, not evidence. Shorten it.
- **m10.** *Presentation. Table 2.* Omitting TMTM misses "for space" invites suspicion; they are 18.7 / 24.8 / 17.9 / 41.9. Include them.

---

## Ignored Alternative Explanations / Paths

1. **A projection-only baseline (track Hovmöller along d).** If it matches R's reversal rates, then RQ2 measures "encode the principal-motion projection" and says nothing about the certificate. R and this baseline differ only in the topology they distort.
2. **Linked views.** A 2-D map with tracks plus a TMTM column keeps both T1 and T2/T3 exact, with no distortion. The paper never argues why a single hybrid column beats coordinated views for practitioners.
3. **A plus feature-level disclosure, rather than R.** The paper's own outputs show that A's per-feature flags catch 91–96% of its reversals and leave only 0.85–1.9% of clear readings reversed unwarned, with zero topological distortion. That looks like a better practitioner outcome than R, which leaves 9.6–13% unwarned at up to 58 hPa distortion. Sec. 8 dismisses this path ("per-feature disclosure ticks were illegible on ERA5") without data.
4. **Projection loss vs hierarchy conflict.** See M7. The high H may largely reflect that a 1-D reference cannot represent 2-D adjacency. The single spatial-linkage dendrogram (H = 32.5%) points this way.
5. **Baseline tuning.** ST-MTM's poorer real-data showing may reflect "adapted defaults" rather than an intrinsic limitation. The Ring result points this way.
6. **Stability instead of faithfulness.** R's big win in `quality.json` is temporal stability: a spurious flip rate of 0.4% vs 7–12% for ST-MTM. Part of the reversal reduction may come from temporal smoothness induced by the motion-residual term, not from positional faithfulness. An ablation without the motion residual would separate the two.

## Missing Stakeholder Perspectives

- **Domain scientists (synoptic meteorologists, fire analysts).** Nobody checks whether a 1-D projection along the principal-motion direction is a view they would use, whether a 55 hPa merge-level error in some columns is acceptable, or whether barrier-filled pressure values would mislead them. Even one short expert feedback session would help.
- **Human readers.** The "reader" is a geometric proxy with known identities and exact anchors. The disclosure strips add visual load, and whether humans read them is untested. This is disclosed, but the implications section still recommends practices on that basis.
- **The designers of TMTM and ST-MTM.** Their goal is T1 and relative distances. `quality.json` (computed but not reported) shows ST-MTM clearly ahead of R on the metrics it targets: Spearman 0.72 vs 0.46 and NN preservation 0.78 vs 0.45 on ERA5, and similarly on ERA5-14 and Ring. Reporting only reference-relative and motion-sign metrics puts the baselines at a systematic disadvantage. Report `quality.json` in full.
- **Reproducers.** The ERA5 fields come from a non-byte-identical mirror (TODO in the PDF). There is no archive link yet.

## Observations (Non-Defects)

- **The theory is correct as far as I can check it.** Thm. 2 (proof in 3 lines, and the ½ is tight), Prop. 5 (the barrier argument reduces the problem to C_k correctly), Cor. 1 (the flattening argument is valid, including the case of a non-contiguous child under a contiguous parent), Thm. 3 (positions and filling decouple because of g > 0), and Prop. 4 (the width-free bound follows from the inverted-pair argument). The earliest-completion DP (Thm. 1) is sound given Lemma "Earliest placement".
- **The certificate framing is well chosen.** "What no merge-tree-preserving layout can avoid" (Sec. 4.1, Prop. 4, Fig. 1a) is a useful, method-agnostic lens, and the width-free variant fairly addresses width-model differences.
- **The headline numbers I checked all match the outputs:** 58/60/63% conflicts; H maxima 31/38/19%; medians 14/13/7%; Table 2 entries; paired differences of 11.9/13.0/17.9 pp; κ = 2% costs of 1.4–2.1 hPa (optimal) and 2.5–2.7 (LCA); κ = 20% costs of 28–32 hPa and 59–74% reduction; 6–8% unavoidable of the 24–29% for existing maps; 368/376; dendrogram 67%/88%. The discrepancies are about *which configuration* a number belongs to, not arithmetic errors.
- **The limitations are unusually candid** (Sec. 8): proxy ≠ humans, ST-MTM sensitivity not studied, single direction, negative results reported.
- **R does improve temporal stability substantially** (`quality.json`: spurious flips 0.4–0.5% vs 7–12% for ST-MTM; motion residual 4–5× lower). This is a real, currently unreported strength.

## Recommendation

- **Recommendation:** Major Revision
- **PacificVis score:** 2 / 5 (weak reject in current form)
- **Confidence:** 4 / 5

Reasoning: the theoretical core would be publishable. As written, though, the abstract's empirical claims are assembled from incompatible operating points (C1), one headline statistic does not discriminate (M1), and the main applied result is partly circular (M2), with selective window reporting (M3). Each of these can be fixed with data the authors already have, but the fixes will noticeably weaken the story. The revision should re-center the paper on the certificate and the exact trade-off, and present the relaxation as one disclosed operating choice rather than a win over ST-MTM.
