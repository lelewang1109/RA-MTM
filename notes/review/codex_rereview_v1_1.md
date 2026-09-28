**Score: 3/5 — borderline, leaning reject in its present form. Confidence: 4/5.** The revision substantially improves the evidence and presentation. The positional certificate remains a credible contribution. The main remaining problems are overstated interpretations of the new experiments, a mismatch between the frontier audit and the implemented layout, and an unresolved condition on the interleaving interpretation.

I checked the LaTeX, supplement, evaluation code, saved JSON, and figure assets. I independently matched **all 64 rate entries in Table 2 and all 48 metric entries in Table 3** to `eval_v2.json`. An independent LP check of the fixed-order formula passed on 100 randomly generated feasible instances, with maximum discrepancy \(3.6\times10^{-15}\). I did not rerun the complete data pipeline or verify a compiled manuscript.

Below, **M:Lx** means line x of [main.tex](/Users/yudong/Research/RA-MTM/paper/pacificvis2027/main.tex), and **P:Lx** means line x of [proofs.tex](/Users/yudong/Research/RA-MTM/paper/proofs.tex).

**The first-round verification is as follows.** “PARTIALLY” means that substantive work was completed but part of the original concern remains.

| Issue | Verdict | Verified changes and remaining gap |
|---|---|---|
| **C1: mixed κ operating points** | **RESOLVED for the original RQ2 defect** | Table 2 now explicitly separates κ = 2%, 20%, ∞ and gives their maximum \(\delta^*\). Its values match JSON. The abstract’s reversal result now belongs to κ = 20%. However, “budget 20%” should say **merge-gap threshold**, since actual distortion reaches 32.5%. The new 391-frame abstract claim introduces a separate configuration mismatch discussed below. |
| **M1: non-discriminating frontier optimality** | **PARTIALLY** | Relaxed-only counts, greedy and flatten-all comparators, and the corrected figure axis are present. But the new audit chooses a **τ-optimal order with a topology-based tie-break**, whereas Algorithm 2 chooses an order using the QP objective within a β budget. Thus the reported 100% result does not verify the implemented method. M:L364; `attainable.py:157–175`. |
| **M2: projection reference, direction fitting, missing baseline** | **PARTIALLY** | Oracle-q and fixed-X are now in Table 2; the inappropriate corollary citation is removed. There is still **no fixed-direction R or cross-fitted R**. Comparing oracle-x with oracle-q does not bound direction-fitting effects on the constrained methods. Worse, the reference result has been promoted into an unjustified universal “floor.” |
| **M3: reversals alone and statistics** | **PARTIALLY** | Reversal + miss is reported, denominators are clear cases, and circular moving-block intervals replace fixed disjoint blocks. Fire is labelled descriptive. However, `paired()` computes intervals only for reversal and miss separately—not their combined error—and Table 2 has no uncertainty for the prominently interpreted error reductions. Ring also needs descriptive framing. |
| **M4: filling assumptions and simplification** | **PARTIALLY** | The value-preserving qualification is correctly added, and the persistence comparison is implemented with traceable results. But preserving anchor values does **not** ensure that anchors remain distinct extrema. This was already raised in R2 W4(d), and still affects the interleaving interpretation. “Simplification is not a remedy” also overstates the results. |
| **M5: visualization and disclosure** | **PARTIALLY** | The witness figure and worked walkthrough are meaningful improvements. Relaxed steps are visibly marked. Barrier-modified pixels remain unmarked; the evaluated feature flags are not the same diagnostic described in the rendering paragraph. The statement that R’s remaining reversals cannot be flagged contradicts the new JSON. |
| **M6: hidden costs** | **PARTIALLY** | Table 3 supplies genuinely q-independent metrics and oracle-q; its numbers are correct. But no uncertainty is supplied, only two datasets are shown, and “most stable” ignores contrary jitter and Ring results. The claimed 4–8% modified pixels has no identifiable saved statistic. |
| **M7: baselines and positioning** | **PARTIALLY** | Reimplementation is disclosed, the 54-configuration ST-MTM grid exists, and the added literature substantially improves positioning. Parameter sensitivity is not implementation validation. The ST-MTM bibliography entry still has no authors. Scheduling/PQ-tree/seriation connections remain largely unaddressed, although adding every suggested citation is unnecessary. |
| **M8: formatting and presentation** | **PARTIALLY** | PDF figure assets exist; visible TODO calls are removed; theorem numbering is unified in the main paper; the dendrogram’s linear/rank distinction is corrected. Some main figure text remains 5.5–6.5 pt, and the pipeline still uses `twinx()`. “And Beyond” remains broader than the demonstrated transfer. Final pagination remains unverified. |

The minor issues deserve separate treatment because several are fully fixed.

| First-round minor issue | Verdict | Evidence |
|---|---|---|
| Notation clashes | **PARTIALLY** | Main-paper pixel size/slack use λ/β. Gap \(g\) versus filling \(g\), origin \(a\) versus anchors \(a_i\), and \(E_k/E_S\) remain. The supplement still uses δ for pixel size. |
| Genericity and split-tree sign | **RESOLVED** | Explicit at M:L210. |
| Algorithm 1 canvas clamps | **RESOLVED** | Both clamps appear at M:L181. |
| Grid alignment and bisection tolerance | **RESOLVED** | M:L193–195 includes both. |
| Tightness example’s leaf-height condition | **RESOLVED** | Added at M:L217 and P:L90. |
| Toy figure’s \(g=\rho=0\) assumption | **RESOLVED** | Explicit at M:L139. |
| Supplement’s “Assumptions to double-check” | **RESOLVED** | Replaced with stated conventions/assumptions. Their mathematical adequacy still needs the extrema correction below. |
| Witness statistic absent from JSON | **RESOLVED** | `witness.json` stores the three medians. |
| “No method falls below” width-free certificate | **PARTIALLY** | Main paper correctly says hierarchy-preserving methods at M:L306; P:L118 remains unqualified. |
| Preprocessing sensitivity | **PARTIALLY** | Smoothing and leaf-cap experiments exist. Background-term sensitivity remains absent, and the new limitation sentence contradicts the 150-km result. |
| Stale `paper_numbers.py` | **PARTIALLY** | Substantially refreshed and executable. It still does not substantiate “every number,” notably modified-pixel coverage and the detailed case-study values. |

**The numerical audit supports most reported measurements.** These are direct checks against [saved outputs](/Users/yudong/Research/RA-MTM/prototypes/output), beyond the automated table comparison.

| Revised-text quantity | JSON evidence | Result |
|---|---|---|
| Real-data conflicts: 58%, 60%, 63% | `replicate_*.json → certificate`: 68/118, 74/124, 19/30 | Correct rounding |
| Witness explains median 92–94% | `witness.json`: 91.6%, 91.9%, 93.5% | Correct |
| ERA5 TMTM: 33.7% reversal / 52.4% error | `eval_v2.json → era5.proxy`: 119/353; 185/353 | Correct |
| ERA5 R20: 14.7% / 24.4% | Same: 52/353; 86/353 | Correct |
| ERA5-14 R20: 15.6% / 32.1% | Same dataset’s proxy: 41/262; 84/262 | Correct |
| Fire R20: 6.2% / 31.2% | Proxy: 7/112; 35/112 | Correct at displayed precision |
| Ring ST-MTM: 7.3% / 34.7% | Proxy: 9/124; 43/124 | Correct |
| R20 maximum distortion: 32.5%, 27.9%, 19.6% | `eval_v2.json → dstar`: 0.325260, 0.279340, 0.195639 | Correct |
| ERA5 paired reversal difference −10.2 pp, CI [−16.5, −4.5] | `eval_v2.json → era5.paired` | Correct |
| ERA5 2% persistence pruning: 40% removed, 34% conflicts | `persistence.json`: 39.7%, 33.9% | Correct |
| Idealized policy audit: 54, 155, 182 relaxed frames | Four datasets’ `attainable_*.json → relaxed_only` | Correct counts; interpretation needs correction |
| Greedy resolves 130/182 conflicts | Same files, greedy at ∞ | Correct |
| ERA5 R20: flips .039, jitter .051, stress .416, NN .485 | `eval_v2.json → era5.hidden` | Correct |
| Dendrogram certificate 67%; OLO maximum 88% | `generality.json`: 67.285%; `dendrogram_demo.json`: 88.2% | Correct |
| Teaser mean maximum error 9.6% → 3.5% | `frontier.json → era5.achieved`: 9.551%, 3.463% | Correct |
| “391 relaxed time steps” at the abstract’s operating point | \(54+155+182=391\), pooled across three κ settings | **Mischaracterized**, not 391 distinct time steps at κ = 20% |
| Barrier filling modifies 4–8% of pixels | No corresponding output field or counting operation found in the cited evaluation scripts | **Not verified** |

The barrier precision check is also supported as an order-of-magnitude statement: the maximum stored normalized discrepancy is approximately \(1.33\times10^{-15}\).

**The revision introduces or intensifies four important claim problems.**

1. **Oracle-q is a reference baseline, not a proven lower bound on reversal rate.**  
   Locations: M:L57, L78, L304, L345, L412–416.

   Table 2 itself supplies counterexamples: fire R∞ has **3.6% reversals versus oracle-q’s 5.4%**; Ring ST-MTM has **7.3% versus oracle-q’s 9.7%**. R∞ also has lower combined error than oracle-q on ERA5. Positional exactness and motion-classification accuracy are different objectives; positional distortion can accidentally correct a projection-induced reversal or convert it into a miss.

   **Minimal fix:** replace “floor” throughout with “exact-reference projection baseline.” Replace “no 1-D map … can beat” with “even exact projection retains reversals.” Do not identify every method–oracle difference as hierarchy-caused. The oracle-x comparison is a sensitivity observation, not a bound on in-sample optimism.

2. **The frontier claim changes the evaluated algorithm and pools operating points.**  
   Locations: M:L57, L364; [attainable.py:157](/Users/yudong/Research/RA-MTM/prototypes/attainable.py:157).

   The new audit minimizes τ within the relaxed hierarchy and breaks ties by smaller \(\delta^*\). The actual solver instead considers orders within β of minimum τ and selects by its multi-objective QP. See [relax_hierarchy.py:147](/Users/yudong/Research/RA-MTM/prototypes/relax_hierarchy.py:147).

   Consequently, the 100% result characterizes an **idealized order selection after hierarchy relaxation**. The existing actual-order audit at κ = 20% reports **370/376 frames overall**, including Gaussians; it does not provide the required relaxed-only fraction. Also, unrelaxed implemented layouts do not lie on \(F(0)\) “by construction” when β slack is used.

   **Minimal fix:** report relaxed-only optimality for the actual selected orders. Keep the idealized audit as a separately named policy diagnostic. Replace 391 with the appropriate denominator and explicitly retain the half-pixel tolerance.

3. **The new disclosure interpretation contradicts its own measurements.**  
   Location: M:L349.

   At κ = 20%, the feature flag catches **40.4%, 24.4%, and 57.1%** of R’s reversals on ERA5, ERA5-14, and fire. Thus “remaining reversals of R cannot be flagged by any positional certificate” is false.

   For A, unflagged cases still reverse in **11/91 = 12.1%, 7/46 = 15.2%, and 2/32 = 6.25%** of cases. “Unflagged readings are rarely wrong” is an unsupported assurance, particularly because these percentages exclude misses.

   There is also a diagnostic mismatch: M:L252 describes actual positional deviations; the evaluation uses a per-frame minimax monotone calibration \(c(u)\), which primarily diagnoses ordering.

   **Minimal fix:** state the flag definition consistently, report conditional risks, and describe the flags as diagnostics without claiming trust guarantees.

4. **“Most stable” exceeds what the new hidden-cost table establishes.**  
   Location: M:L368.

   R20 has fewer flips than ST-MTM on the real datasets, but ERA5 jitter is **.051 versus .027**, and ERA5-14 jitter is **.052 versus .034**. On Ring, omitted from Table 3, R20 has **.059 flips versus .030** for ST-MTM and also higher jitter. Oracle-q is more stable on several measures.

   **Minimal fix:** “R20 reduces order flips relative to TMTM and ST-MTM on the real datasets; displacement-based stability is mixed.” Show the remaining datasets in supplementary results and avoid attributing every distance-preservation cost solely to projection.

**The most important unresolved theoretical issue is preservation of extrema, rather than preservation of their values.**

At [M:L225–238](/Users/yudong/Research/RA-MTM/paper/pacificvis2027/main.tex:225), the barrier formula permits \(b_k=\ell_k\). Consider
\[
T=((i,j)_1,k)_6,\qquad f(i)=0,\quad f(j)=0.2,\quad f(k)=5,
\]
with anchor order \(i,k,j\). Then \(C_1=C_2=1\), \(\ell_1=\ell_2=5\), and \(\delta^*=4\), attained by barriers \(b_1=b_2=5\).

The middle anchor retains value 5, but it is not a distinct birth minimum: at height 5 it already connects to the other components. Therefore the rendered merge tree does not have the original three labelled leaves. The cited Munch–Stefanou formulation requires a bijection onto leaves, explicitly in Definition 3.7. [Original paper](https://arxiv.org/pdf/1803.07609)

**What remains correct:** the formula optimizes the manuscript’s pairwise anchor-merge distortion over value-preserving scalar fillings. The positional formula, non-contiguity lower bound, and that optimization argument survive.

**Minimal fix:** distinguish anchor-merge distortion from leaf-labelled interleaving distance. Either permit labels at non-leaf points under an explicitly justified alternative definition, or require positive barrier clearance above adjacent leaf values. Under a strict-extremum requirement, the example has infimum 4 but no attaining filling at 4. Synchronize the frontier’s “attained” claim, “keeps every feature,” rendering checks, and supplement accordingly.

This is an unresolved first-round concern—R2 W4(d)—rather than a newly discovered revision regression.

**Other remaining overclaims and inconsistencies have relatively small fixes.**

| Exact location | Problem | Minimal correction |
|---|---|---|
| M:L52, teaser caption | A is said to “attain” \(\tau^*\), although the displayed QP layout uses β slack. | “Achieves error within β of the certificate.” |
| M:L57, L254 | “Budget 20%” can imply a bound on topological distortion; maxima reach 32.5%. | Say “merge-gap threshold κ = 20%”; give actual maximum distortion in the abstract. |
| M:L195 | “All frontier values … use this certified bound” conflicts with exact enumeration of F. | Restrict the sentence to the plotted **lower-bound curve \(\Phi\)**. |
| M:L319; abstract/contribution | “Simplification is not a remedy” understates substantial reductions, e.g. ERA5-14 conflicts 59.7% → 17.7%. At 5% pruning, saved conflict shares fall to 6.7–15.3%. | “Simplification reduces but does not eliminate conflicts at the tested thresholds, while deleting features.” Identify removal percentages as **leaf instances**, not unique tracks. |
| M:L319 | “Many … tracked cyclones” is not established by the persistence output. | Use “tracked pressure minima” unless domain identification is supplied. |
| M:L347 | The threshold/window wording suggests a full Cartesian grid. Only six settings per dataset were evaluated. | State: three thresholds at k = 2, plus k = 1, 4, 8 at threshold 2%. Treat 11 significant settings as exploratory. |
| M:L347, L416 | “Relaxation no longer helps” at fire cap 8 overlooks lower combined error: R20 33.3% versus ST-MTM 35.1%. | Say it no longer improves **reversal rate**. |
| M:L416 | “Smoothing below 200 km exceeds 12 leaves” contradicts `era5_s150`, whose saved maximum is 11. | Specify the dataset/configuration that actually exceeded the limit. |
| M:L77, L250–254 | “Only free parameter” conceals fixed QP weights absent from the method description. | Say “one exposed user parameter”; document reference/geometry/motion/eccentricity weights **4/1/.5/.1** and normalization. |
| M:L252, L368 | Changed scalar pixels are neither visibly identified nor supported by the 4–8% statistic. | Add a modification mask and save its numerator, denominator, tolerance, and κ; otherwise remove the percentage. |
| M:L210; P:L109, L121 | “No additional extrema” is imprecise; the supplement permits \(g\ge0\) but later relies on \(g>0\). “Equal leaf heights” is ambiguous. | Say “exactly the labelled birth minima”; use consistent strict anchor separation and “matching corresponding leaf values.” |
| `refs.bib:3` | ST-MTM still lacks authors. | Add Mauro Diaz, Juanpablo Heredia, Nivan Ferreira, and Jorge Poco, with DOI 10.2139/ssrn.6604235. [SSRN record](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6604235) |

The case study is now useful, but it demonstrates a positional conflict rather than a specific approach/separation reversal against ST-MTM. Its strips also suppress numeric tick labels, limiting the claim that readers can recover exact per-frame costs. An annotated selected-frame value and one explicit motion example would strengthen it without requiring a full user study.

**The page budget is high risk.** The official allowance is **nine content pages plus two pages containing only acknowledgments and references**. The abstract deadline is November 2 and the paper deadline November 9, 2026. [Conference CFP](https://pacificvis2027.github.io/contribute/conference-papers/)

I count approximately **8,532 whitespace-delimited source tokens**, including mathematical/LaTeX material. The seven figure assets occupy approximately **30.25 column-inches, or 1.64 pages**, before captions and float spacing. Six are full-width. Three tables, two algorithms, displayed equations, theorem spacing, and the title/abstract add considerable overhead.

My estimate is **roughly 9–10.5 content pages**, with substantial uncertainty from line breaking and float placement. I would not assume it fits. Nor should the remaining small figure text be reduced: the frontier legend is explicitly 5.5 pt, and some strip labels are 6 pt.

Cut in this order:

1. Move Algorithm 1’s detailed pseudocode and DP implementation exposition to the supplement, keeping the recurrence, complexity, and guarantee.
2. Compress repeated motivation and interpretation across the abstract, introduction, task discussion, implications, and conclusion.
3. Move detailed sensitivity/grid narrations into a supplementary table; retain the principal results and exceptions.
4. Reduce duplication between the six-panel pipeline and the witness case study. Preserve the case study’s readable scale.
5. Shorten the dendrogram discussion and title claim; retain the transfer result and its actual scope.

A first target is **1,200–1,800 words of reduction**, followed immediately by compilation and float inspection.

**The five most valuable changes before submission are:**

1. **Correct the empirical claim hierarchy:** remove the universal projection floor, causal attribution of every excess reversal to hierarchy, and unflagged-reading assurances.
2. **Audit the actual method against F:** use its selected orders, report relaxed-only results per κ, and remove or correctly characterize 391.
3. **Resolve the extrema/interleaving boundary:** make the theorem domain, renderer behavior, and feature-retention claims agree.
4. **Finish the evaluation rather than expand it broadly:** add fixed-direction or cross-fitted R, paired intervals for combined error, complete hidden-cost results, and a concrete ST-MTM reproduction check.
5. **Produce a submission-sized, readable manuscript:** cut repetition, retain the witness walkthrough, mark modified scalar regions, fix the bibliography, and verify the compiled nine-page body.

The core deserves preservation: the fixed-order certificate, width-free bound, hierarchy/space decomposition, and filling-independent topological lower bound are substantive results. The revision will be stronger if it presents the relaxation as an empirically useful operating choice with explicit costs, while reserving universal claims for what the mathematics actually proves.