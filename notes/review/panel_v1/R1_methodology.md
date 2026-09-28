# Review R1: Methodology / Evaluation

## Reviewer role and identity

Peer Reviewer 1 (Methodology / Evaluation). I work on visualization evaluation, with a background in quantitative layout-quality metrics, projection-quality measures, and statistics (bootstrap, paired comparisons). I pay close attention to reproducibility.

**Review focus.** I checked whether the evaluation in Sec. 7 supports the claims in the abstract and introduction. That covers the construct validity and statistics of the geometric reader proxy (RQ2), baseline fairness, whether the RQ3 optimality claim is well-defined, preprocessing sensitivity, and hidden costs of relaxation, including the not-yet-reported `prototypes/quality.py`. I traced the paper's numbers to code and JSON outputs, and I re-ran parts of the proxy myself. Those re-runs were scratch scripts only; no repository file was changed.

## Recommendation

- **Recommendation:** Major Revision
- **PacificVis score:** 3 / 5 (borderline). The theory is solid, but the evaluation as reported overstates the practical benefit.
- **Confidence:** 4 / 5

## Summary assessment

The paper models hierarchy-constrained 1-D layouts and proves a positional certificate, a filling-independent topological price, an optimal filling, and an exact position–topology frontier for small trees. The verification is unusually careful: the closed form is checked against an LP, the DP against brute force, and Theorem 2 on every rendered frame. Every number I spot-checked matches the saved JSON. RQ1 (conflict prevalence, with sensitivity to θ, direction and width model) is convincing.

My concerns are with RQ2 and with how RQ2 and RQ3 are combined in the abstract.

1. **Operating point.** The relaxed map in Table 2 is the κ = ∞ relaxation. I confirmed this in the code and by re-running it. At κ = ∞, merge levels are distorted by up to 52–68% of the value range on pressure data. At κ = 2%, the budget behind the "98% on the exact frontier" claim, the relaxed map reverses 24.9% of ERA5 readings, exactly the same as ST-MTM. The abstract combines numbers from different operating points without saying so.
2. **Projection floor.** A "map" that simply draws the reference coordinate q, with no hierarchy, reverses 12.7% (ERA5), 14.1%, 5.4% and 9.7% of readings. The relaxed map's 13.0 / 14.9 / 3.6 / 10.5% sits on that floor. RQ2 therefore mostly measures how closely a map follows q, and q's direction is fitted in-sample on the same tracks that define the truth.
3. **Smaller issues.** Table 2 has no CIs. The wildfire bootstrap has only 4 blocks. The "on frontier" rate is dominated by frames that were never relaxed.

All of these are fixable by reporting rather than new theory, and after the fixes the paper would be a strong theory contribution with an honest evaluation.

## Strengths

- **S1: Paired design with shared inputs (Sec. 7.1, 7.3; `misreading.py`).** All methods share merge trees, supports and correspondences. Truth labels are identical across methods, so the paired temporal-block bootstrap of differences (`paired_differences`) is the right design. Seeds are fixed (0, 1). The permutation null is computed per method, and the reader threshold (1/2/5%) and window (1/2/4) are both varied.
- **S2: Numerical verification of the theory (Sec. 4.1, 4.2, 7.1, 7.4).**
  - The closed form matches the LP to 2e-14, and the DP matches brute force on 300 random hierarchies.
  - Theorem 2 has zero violations over 924 broken frames (`frontier.json`: `theorem_violations` = 0).
  - `check_F0_eq_tauhier_max` = 0.0 on all five datasets (`attainable_*.json`).
  - τ_free is exact through n! enumeration, and the old hill-climbed τ_free differs from it by at most 1e-16.
- **S3: The exact frontier is a real yardstick (Thm. 3, Fig. 5).** Enumerating all n! orders with two closed forms gives a ground-truth Pareto front against which any heuristic can be judged. This is rare in layout papers and is the strongest methodological asset.
- **S4: Fairness devices for baselines (Sec. 4.3, 7.2).** The width-free certificate with a best monotone calibration (`pointcert.py`) compares TMTM and ST-MTM in their own width models and separates avoidable from forced deviation. The 2-D-distance truth in RQ2 does not depend on the reference, which is the right choice.
- **S5: Honest limitations and traceability (Sec. 8; `paper_numbers.py`).** The negative results and the limits of the proxy are stated. The following all trace exactly to saved outputs:
  - all 16 cells of Table 2;
  - the paired differences (11.9 / 13.0 / 17.9 pp; fire miss +15.2 pp);
  - the RQ1 shares, maxima and medians;
  - 368/376;
  - the κ = 2% cost figures (−11/−13%, 1.4–2.1 hPa optimal filling, 2.5–2.7 hPa LCA filling);
  - the dendrogram figures (67% / 88% / 14%).

## Weaknesses (ranked by impact on acceptance)

### W1 [CRITICAL]: RQ2 and the abstract report the κ = ∞ relaxation without saying so, and combine it with κ = 2% optimality

**What is wrong.** `misreading.method_positions` calls `rh.relax_frame_threshold(fr, ids, w, q, p, theta, tf)` without `value_cap`, so κ = ∞. `quality.py` inherits this. Every "R" number in Table 2 and in the abstract ("lowers this to 4–15%") is therefore the κ = ∞ map. According to `replicate_*.json` (`merge_err_max`), that map distorts merge levels by up to 68% (ERA5), 52% (ERA5-14) and 53% (fire) of the value range, which in practice means the merge tree is largely given up.

I re-ran the proxy with the same code and only the cap changed (reversal rate; paired difference vs ST-MTM with 95% interval):

| Data | κ | Reversal | Miss | vs ST-MTM |
|---|---|---|---|---|
| ERA5 | 2% | 24.9% | 9.9% | +0.0 pp [−7.4, +6.4] |
| ERA5 | 20% | 14.7% | 9.6% | −10.2 pp [−16.4, −5.0] |
| ERA5 | ∞ | 13.0% | 7.1% | −11.9 pp [−19.3, −6.1] (paper) |
| Fire | 2% | 12.5% | 30.4% | −8.9 pp [−19.6, 0.0] |
| Fire | 20% | 6.2% | 25.0% | −15.2 pp [−26.1, −5.8] |
| Fire | ∞ | 3.6% | 29.5% | −17.9 pp (paper) |

The abstract joins "lowers this to 4–15%" (κ = ∞) with "lies on the exact frontier in 98% of time steps" (the 368/376 figure, which is κ = 2%) and "reports its topological cost exactly". A reader will assume these describe one method at one setting. At κ = 2% there is no reversal benefit on ERA5.

**Where.** Abstract; Sec. 1 (contribution 4); Sec. 7.3 and Table 2; `misreading.py` L55.

**Minimal fix.**
- State κ in Sec. 7.3 and the Table 2 caption.
- Add R columns for κ = 2% and 20% to Table 2, or add a small reversal-vs-δ* plot per dataset. This makes RQ2 a trade-off curve, which is exactly the paper's thesis.
- In the abstract, pair every R number with its κ and its merge distortion, for example "at κ = 20% (≤ 33 hPa, 20–33% of the value range), reversals drop to 6–15%".

### W2 [MAJOR]: The proxy's floor is the 1-D projection itself, the reference is fitted in-sample, and the fixed-X baseline is omitted

**What is wrong.**

1. **Construct.** The truth is the change in 2-D Euclidean distance, but any 1-D map encodes at best a projection. I computed the reversal rate of an *oracle* that places each feature exactly at q (auto direction, no hierarchy, same judging code; k = 2, ε = 2%):

   | Data | Oracle q | Oracle x | Oracle y | Relaxed R (κ = ∞) |
   |---|---|---|---|---|
   | ERA5 | 12.7 | 16.4 | 19.3 | 13.0 |
   | ERA5-14 | 14.1 | 15.3 | 21.0 | 14.9 |
   | Fire | 5.4 | 10.7 | 15.2 | 3.6 |
   | Ring | 9.7 | 11.3 | 8.1 | 10.5 |

   R is at the projection floor, and its own-axis ("claim") reversal rate is 0.000 on every dataset (`paper_numbers.py` output). The proxy thus measures closeness to q plus the quality of the direction. That is useful, but it is not "what conflicts do to motion readings" unless the floor is subtracted. Read the right way, the decomposition supports the paper: on ERA5 the hierarchy-kept map A is at 22.4% against a floor of 12.7%, so about 10 pp are hierarchy-induced. Report it that way.
2. **In-sample direction.** `gm.auto_reference` takes the principal direction of the *same* tracked displacements whose pairwise distance changes are the truth. The baselines never see this direction. Part of R's advantage over TMTM and ST-MTM is therefore the direction, not the relaxation. The oracle-q vs oracle-x gap is 3.7 pp on ERA5 and 5.3 pp on fire.
3. **Omitted baseline.** Sec. 7.1 lists "a reference-anchored layout along a fixed longitude" as a baseline, but Table 2 omits it. It is computed in `replicate_*.json` ("fixed-X anchored": 25.2 / 22.9 / 17.9 / 23.4%) and performs like ST-MTM.

**Where.** Sec. 3.2 (reference), Sec. 6 (Reference), Sec. 7.3, Table 2.

**Minimal fix.**
- Add an "oracle q (no hierarchy)" row and the fixed-X anchored row to Table 2, and report each method's excess over the floor.
- Add R with a fixed direction (x or y), or a cross-fitted direction. For example, fit on ERA5 1999/2000 and apply to 2013/14, which is feasible because 2013/14 has an angle of 4.5° against 19°. This separates the effect of the direction from the effect of relaxation.
- Soften "Keeping the hierarchy (A) performs like ST-MTM; only relaxation helps, as Corollary 1 predicts". Corollary 1 bounds the maximum position error; it predicts nothing about sign reversals of pairwise distance changes.

### W3 [MAJOR]: Reversal rate alone rewards "no-change" readings; the fire result is mostly a shift from reversals to misses

**What is wrong.** A method that compresses motion converts reversals into misses. On fire, R has reversal 3.6% and miss 29.5%, against ST-MTM's 21.4% and 14.3%. The combined error (reversal + miss) is 33.0% for R vs 35.7% for ST-MTM, which is essentially a tie. The per-method permutation null for R on fire is 21.1%, compared with 35–37% for the others, which confirms that R's marginal distribution of readings differs.

The abstract reports only the reversal rate ("wrong direction ... 21–34% ... lowers this to 4–15%"). It also says "21–34% of feature pairs", but the denominator is clear-truth pair-windows (n = 112–353 of 238–479 pairs), not pairs.

**Where.** Abstract; Sec. 7.3; Table 2 (TMTM misses are omitted, although they are 18.7 / 24.8 / 17.9 / 41.9%).

**Minimal fix.**
- Add one threshold-free or composite measure next to the reversal rate:
  - rev + miss,
  - Cohen's κ between the 3-class reading and the truth, or
  - reversal rate among *committed* readings (rev / (rev + correct)).
- Report TMTM misses, perhaps in the supplement if space is short.
- Change "feature pairs" to "clear cases (pair × 24-h window)".
- State that on fire the relaxation trades reversals for misses, with no net gain in the combined error.

### W4 [MAJOR]: Statistical reporting in RQ2 is incomplete, and the block bootstrap is too coarse for the short datasets

**What is wrong.**

- **No intervals in Table 2.** Table 2 gives point estimates only. The per-method `T2D_ci95` exist in the JSON but are computed with a *frame* bootstrap, which ignores temporal autocorrelation: overlapping k = 2 windows share frames.
- **Too few blocks.** The paired test uses 8-frame blocks starting at fixed offsets (`np.arange(0, T, 8)`). That gives 15 and 16 blocks for ERA5 but only **4 blocks for wildfire (30 frames) and 5 for Ring (40)**. A percentile bootstrap over 4 blocks cannot yield a reliable 95% interval. Two symptoms in the output:
  - the fire miss difference has CI [+4.2, +40.0] pp around a point estimate of +15.2;
  - Ring's R − A reversal difference has CI [−14.6, −12.9] pp, which is implausibly narrow.

  "Significantly less often ... on all three real datasets (paired 95% intervals exclude zero)" is therefore not established for fire.
- **Multiplicity.** "The ranking is stable" across 3 ε × 3 k × 4 datasets is asserted without numbers or multiplicity control.

**Where.** Sec. 7.3; Table 2; `misreading.py` (`stats()`, `paired_differences`).

**Minimal fix.**
- Report paired differences with block-bootstrap CIs in Table 2, or in a compact forest plot.
- For fire and Ring, use a moving-block or stationary bootstrap with a block length of about k + 1 frames, or a within-pair permutation (sign-flip) test of method labels. State the number of blocks.
- Label fire and Ring as descriptive if they stay underpowered.
- Put the ε/k sensitivity table in the supplement with numbers. Note that on Ring the relaxed map is *worse* than ST-MTM for k = 1 (12.8 vs 8.5%) and k = 4 (8.6 vs 5.7%).

### W5 [MAJOR]: The RQ3 optimality claim is well-defined but weakly discriminative, and it is computed on the order rather than on the displayed layout

**What is wrong.**

- **Mostly unrelaxed frames.** The claim "368 of 376 frames on the exact frontier at κ = 2%" is not circular: F is computed independently over all n! orders. But at κ = 2% only 54 of 376 frames are relaxed (15 + 19 + 14 + 6 + 0, from `replicate_*.json` `frames_relaxed`). The other 322 are hierarchy-consistent frames, where "on the frontier" just means τ(π) ≈ τ* = F(0). The method targets that by construction, up to the β slack. The off-frontier frames already occur at κ = 0 (4 on ERA5-14, 2 on fire), so they are budget-slack frames, not relaxation failures.
- **Easy at the extremes.** At κ = ∞ the relaxed order approaches a reference-sorted order, which attains τ_free = F(∞) and is on the frontier almost trivially (371/376).
- **Order, not layout.** `attainable.py` compares τ(π), the *best* error of the chosen order, with F. The displayed layout's error can exceed τ(π) by up to β = L/120 (0.83% of the axis). The two quantities are mixed in the paper: the teaser reports the realized error (9.6% → 3.5%, `frontier.json`), whereas Fig. 5 plots τ(π) (8.8% at κ = 0, 2.7% at κ = 20%, `attainable_era5.json`). The Fig. 5 caption calls τ(π) "maximum position error", which implies the realized error.

**Where.** Abstract ("98%"); Sec. 7.4 "Optimality"; Fig. 5 caption; Fig. 1 caption.

**Minimal fix.**
- Report the on-frontier rate **among relaxed frames only**, per κ.
- Add a naive comparator on the same frames, such as the greedy one-node policy of Sec. 6 or "flatten all γ_v ≤ κ without pruning", to show that the rate discriminates.
- Report the mean vertical gap to F at the frame's own δ* for relaxed frames.
- Either plot the realized error in Fig. 5 or rename its axis to "τ(π) of the chosen order" and state that realized error ≤ τ(π) + β.

### W6 [MAJOR]: Baseline configuration and sensitivity

**What is wrong.**

- ST-MTM has no official code and is reimplemented (§4.1–4.3 of that paper). On all real datasets it runs with "adapted defaults" (`experiments/era5.py`: uniform weights, K = total scaled area, r = 0.95, λ = 0.5). Only Ring uses published parameters.
- On Ring, which is the one dataset with tuned ST-MTM, ST-MTM beats R on reversals (7.3 vs 10.5%; also for k = 1 and k = 4). This suggests tuning matters, and Sec. 8 concedes that "the parameter sensitivity of ST-MTM is not studied".
- The reimplementation is not validated against figures in the ST-MTM preprint. At minimum, the paper should show that the reimplementation reproduces the Ring or three-Gaussian figure qualitatively.

**Where.** Sec. 7.1 (Methods), Sec. 8.

**Minimal fix.**
- Give ST-MTM a best-case setting: a small grid over weights, r and λ on one real dataset, reporting its best reversal rate.
- Add one sentence plus a supplement figure validating the reimplementation against the published Ring or Gaussian result.
- State the TMTM configuration explicitly.

### W7 [MAJOR]: Hidden costs of relaxation are not reported; the new `quality.py` analysis needs fixes before it can be

**What is wrong.** The paper says nothing about distance preservation or temporal stability of R, even though ST-MTM's own evaluation uses stress and neighbourhood preservation. `quality.py` / `quality.json` contain the relevant numbers, but two of its five metrics are not neutral:

- **`spurious_flip_rate` is q-referenced.** It counts map-order flips that q does not show. R tracks q, so a low value partly restates the construction: R has 0.4–0.5% vs 7–12% for the others. It measures fidelity to the reference, not stability. There is also a denominator problem: pairs whose q order flips are counted in the denominator but can never count as flips.
- **`motion_residual` is also q-referenced, and R's QP explicitly minimizes this residual (Sec. 6, Layout).** It favours R by construction. Sanity check: the residual of a map that never moves (Δu = 0) is mean |Δq|/L = 0.043 on ERA5 and 0.015 on fire. TMTM (0.055), ST-MTM (0.044) and A (0.054) are no better than a frozen map on ERA5, so this metric mostly measures jumps, not motion fidelity. The global affine calibration also differs from the monotone calibration used in RQ1.
- **`stress`, `spearman` and `nn_preservation` are sound and standard.** Stress uses Kruskal stress-1 with optimal scale, per frame, between 1-D anchor distances and 2-D extremum distances. Their caveats:
  - nn_preservation has a high chance level for n = 3 and is averaged unweighted over frames;
  - none of the three has uncertainty or paired tests;
  - Gaussians are excluded;
  - they inherit κ = ∞ (see W1).

I added two method-agnostic measures on ERA5 / fire (scratch computation; identical inputs):

| Method | Raw order flip rate | Anchor jitter (\|Δu\| / extent) | Stress | NN |
|---|---|---|---|---|
| TMTM | .157 / .334 | .073 / .102 | .397 / .458 | .663 / .639 |
| ST-MTM | .074 / .076 | .027 / .053 | .291 / .256 | .780 / .753 |
| A | .088 / .094 | .075 / .054 | .436 / .261 | .516 / .658 |
| R (κ = ∞) | .033 / .010 | .044 / .019 | .405 / .219 | .445 / .600 |
| Oracle q | .039 / .005 | .043 / .017 | .417 / .227 | .420 / .589 |

**Reading.**

- R is genuinely more order-stable than every baseline, even without referencing q.
- R's anchors move more than ST-MTM's on ERA5 but match the reference's own motion.
- R's distance preservation is clearly worse than ST-MTM's on pressure data (stress .40 vs .29; NN .45 vs .78). It is **at the level of the oracle projection**, so this cost belongs to using a single reference direction, not to the relaxation.

That is a clean, honest story, and it pre-empts an obvious reviewer objection.

**Where.** Missing from Sec. 7. Belongs in RQ3 or a short "hidden costs" paragraph, with the table in the supplement.

**Minimal fix.**
- Report a 5-metric table (raw flip rate, jitter, stress, Spearman, NN) with rows for TMTM, ST-MTM, A, R at the κ used, and oracle q.
- Present `spurious_flip_rate` and `motion_residual` separately as "fidelity to the reference", with the frozen-map baseline.
- Add paired block-bootstrap CIs for R vs ST-MTM.
- State plainly that ST-MTM preserves 2-D distances better and that this is inherent to any 1-D projection.

### W8 [MINOR]: Preprocessing sensitivity is not studied

**What is wrong.**

- The wildfire smoothing is chosen as "the smallest smoothing that yields at most 12 maxima per frame" (`datasets_extra.py`). That cap is driven by the n! enumeration. A broad background Gaussian (1e-3, σ = 16 cells) is also added to remove zero plateaus. The paper does not mention the background term.
- ERA5 uses a fixed 250 km smoothing.
- Conflict prevalence (58–63%) and the tree shapes plausibly depend on both choices, but no sensitivity is shown. RQ1 varies θ, direction and width model, but not the feature extraction.
- The ERA5 mirror-vs-CDS issue is disclosed, and a TODO remains in the text (Sec. 7.1, red). The claim "reproduce the features ... exactly" has no stated evidence.

**Minimal fix.**
- Report RQ1 shares for two more smoothing levels per real dataset: ERA5 at 150 and 350 km; fire at the next σ up.
- Mention the background term.
- Either rerun on CDS or state the evidence of identity (identical per-frame extrema, tracks and hierarchies, with a hash), and remove the TODO.

### W9 [MINOR]: Some statements are not traceable or are slightly imprecise

- **Witness share (Sec. 4.1).** "The best witness explains a median of 92–94% of τ*" is not stored in any `prototypes/output/*.json`. The only code mentioning witnesses is the new, untracked `fig_witness.py`, which prints a single frame. Add the computation to a script that writes JSON.
- **"No method falls below the width-free certificate" (Sec. 7.1 Checks).** `pointcert.json` shows R below it in 68 ERA5 frames, which is expected because R breaks the hierarchy. Say "no hierarchy-preserving method".
- **Stale docstring.** `paper_numbers.py` says it prints numbers for `draft_zh.md`, not `main.tex`. Several paper numbers come from `attainable_*.json`, `pointcert.json`, `frontier.json` and `dendrogram_demo.json`, which it does not read. A single claim → file → key manifest would make the artifact audit-ready.
- **RQ4 reference.** The "geographic rank-scaled position" does not say which geographic coordinate or direction is used.

## Detailed comments by section

- **Sec. 1, para. 3.** The motivating number (33.7% vs 24.9%, null 37–40%) is fine. Consider also giving the projection floor (12.7%), so that readers see what a perfect 1-D map along the principal direction would still get wrong.
- **Sec. 3.2.** The argument for the reference is good ("a property of the task, not of a method"). But the evaluation *fits* the reference from the evaluated tracks. Say so, and give the leave-out variant (W2).
- **Sec. 3.3.** "Reverses 22.4% ..., close to ST-MTM (24.9%)" is consistent with the JSON.
- **Sec. 6, Constants.** θ = 2% is justified by legibility. κ is not listed among the constants, yet it determines everything in RQ2 (W1). Either make κ an explicit user parameter with a recommended default, or say that κ = ∞ subject to the gate is the default.
- **Sec. 7.2.** RQ1 is methodologically sound. The robustness to eight fixed directions (23–77%) is honest. Report the auto-direction share alongside that range; currently 58% sits in the middle of it.
- **Sec. 7.3, proxy definition.** Map threshold = 2% of the "occupied anchor range" per method, over the whole sequence. One outlying anchor inflates ε_map and thus the miss rate. A per-frame span, or the canvas length, would be more robust; at least state the choice.
  - The permutation null shuffles readings across all pairs (not within frame), which preserves each method's marginal distribution. Say this explicitly, because it explains why R's null on fire is 21% rather than about 36%.
- **Sec. 7.4, Cost.** Numbers verified. "By 45% on fire" is κ = 2% (`replicate_wildfire.json`), consistent.
- **Sec. 7.4, Tightness.** Numbers are consistent with `attainable_*.json` (gap mean 0.4–2.3%, tight 29–36%, max 25% on ERA5-14).
- **Theory verification gap.** Prop. 5 is checked for *attainment* (barrier filling hits δ* to 1e-15), but not for *minimality* by an independent solver. A cheap check: for random orders, solve min_b d_top as an LP over the barrier heights and compare with δ*. The proof is in the supplement, but Fig. 5 and RQ3 depend on δ* being a true minimum.

## Questions to authors

1. Which κ is the "certificate-driven relaxation" of the abstract and Table 2? Is κ = ∞ subject to the θ gate the intended default? If so, how do you reconcile it with merge-level distortions of 50–70% of the value range?
2. What reversal rate does a map that draws q exactly (no hierarchy) obtain? Do you agree that the proxy's floor for all 1-D methods is 13–14% on pressure data?
3. How much of R's advantage over ST-MTM remains when R uses a fixed direction, or a direction fitted on a different period?
4. Of the 54 frames relaxed at κ = 2%, how many are on the exact frontier? How does a naive flattening policy score on the same frames?
5. Was the ST-MTM reimplementation validated against the preprint's figures? What is its best reversal rate over a small parameter grid on ERA5?
6. How do the RQ1 prevalence and the RQ2 ranking change for ±100 km of ERA5 smoothing and for a different wildfire maxima cap?

## What would raise my score by one point

- (i) Table 2 with R at κ ∈ {2%, 20%, ∞}, the δ* each costs, the oracle-q floor and fixed-X rows, paired CIs, and an abstract rewritten to match.
- (ii) The on-frontier rate reported on relaxed frames, with a naive comparator.
- (iii) A short hidden-costs paragraph built on the corrected `quality.py`, using method-agnostic stability measures, the oracle-q row and CIs, which honestly concedes ST-MTM's advantage in distance preservation.

With these, the empirical claims would match the evidence, and the paper's real strength, certified and exact trade-offs, would stand on its own.
