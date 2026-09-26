# Review R2: Computational topology and merge trees

**Reviewer role and identity.** Peer Reviewer 2. I work in the TopoInVis community on merge trees, interleaving distances, topological simplification, and topology-based visualization of time-varying data.

**Review focus.** I checked whether the theory is correct and whether it adds something. I audited every formal statement in Sec. 4–5 (Definition 1, Propositions 1–5, Theorems 1–3, Corollary 1) against its proof sketch and against the supplement `paper/proofs.tex`, and I tried to build counterexamples. I also checked the related work on merge trees and topology, and how safely the interleaving-distance and novelty claims are worded.

---

## Recommendation

- **Recommendation:** Major Revision
- **PacificVis score:** 3 / 5 (borderline; leaning accept if the qualifications below are made)
- **Confidence:** 4 / 5

## Summary assessment

The paper models merge tree maps, and other hierarchy-constrained pixel displays, as 1-D interval layouts constrained by a tree. It then proves:

- a closed-form positional "certificate" for a fixed order,
- an exact pseudo-polynomial dynamic program for the best hierarchy-consistent order,
- a width-free variant,
- a filling-independent lower bound γ_v/2 on the merge-level distortion caused by breaking a subtree,
- a closed-form optimal filling,
- an exact position–topology frontier for small trees.

I rechecked every proof. **I found no false statement within the model the paper actually uses.** I also verified Proposition 5 numerically on random trees and all orders: no barrier vector beats the closed form, and the barrier filling attains it.

Three things are stated too strongly or placed badly:

1. **The optimal filling and the "exact frontier of all 1-D maps" assume the filling keeps the true extremum values.** The paper also calls d_top a labelled interleaving distance. Under that distance, which penalises leaf-value changes on the diagonal, the leaf-height term of Proposition 5 halves. So the "second mechanism … whatever the filling" is an artefact of that restriction, not a property of topology.
2. **Topological simplification by persistence is never discussed.** My rerun of the authors' code shows that the headline conflict rates (58–63%) depend strongly on extrema with persistence of about 1–2% of the value range.
3. **Several results are close relatives of known results on ℓ∞ ultrametric fitting, cluster stability, and the merge distortion metric.** The claim "interleaving distances have not been used to evaluate layouts" is not safe as worded.

All three can be fixed without changing the core contribution, which I find useful and cleanly argued.

---

## Strengths

- **S1. The central lower bound (Theorem 2, Sec. 5.2) is correct, short, and applies to any map.** The three-term telescoping proof is valid, and I could not break it. It holds for any function g on the line, needs no assumption that anchors are extrema (supplement, Remark after Thm. 2), and so applies to TMTM, ST-MTM and future methods. The γ_v/2 constant is tight, with the caveat in W6.
- **S2. Proposition 1 and Theorem 1 are correct and carefully derived.** Supplement Lemmas 1–2 and Prop. 1:
  - The chain-with-box-windows lemma is right, including the binding cases (ii) and (iii).
  - The DP is correct: F_M = min_c E_c ∘ F_{M∖c} is valid because each E_c is non-decreasing (min over σ commutes with a monotone outer map), and blocks interact only through the earliest next start.
  - Monotonicity (Prop. 2) and witness triples are correct.
- **S3. Proposition 5 is correct as a statement about leaf-value-preserving fillings.** The reduction to barrier heights, the collapse of the upper constraints to C_k + δ, and the "raise barriers" argument are all sound. The proof of δ\* = 0 ⇔ π ∈ Π(T) via the ultrametric inequality is neat.
- **S4. Proposition 4 (width-free certificate) is correct and well chosen.** The attaining calibration c(u_k) = ½(max_{i⪯k} q_i + min_{j⪰k} q_j) is non-decreasing, and its error is at most τ_pt(π); I checked this. Reading the axis the other way round (decreasing calibrations) is implicitly covered, because Π(T) is closed under reversal. It is the right tool for separating "hierarchy-forced" from "method-chosen" error in existing maps.
- **S5. The theorems are checked numerically on every rendered frame, and limitations are stated honestly.** Supplement Sec. 6 and paper Sec. 7.1 "Checks" test Theorem 2 and Corollary 1 on every frame, confirm that the barrier filling attains δ\* to 1e-15, and confirm that F_T(0) = τ\*. Sec. 8 openly states that no approximation guarantee exists and that NP-hardness is open. This is uncommon and welcome.

---

## Weaknesses (ranked by impact on acceptance)

### W1 [MAJOR]: "Optimal filling", "whatever the filling" and "exact frontier of all 1-D maps" hold only for fillings that keep true leaf values

**Where.** Sec. 5.3 (Prop. 5 and the paragraph after it: "raises their 1-D merge level at least to its own value, whatever the filling"). Theorem 3 ("achievable pairs"). Abstract ("exact position–topology frontier of all 1-D maps"). Sec. 5.1 (interleaving interpretation).

**What is wrong.**
- d_top is defined over i ≠ j only, and Prop. 5 fixes g(a_k) = f(k). The paper then identifies d_top with the Munch–Stefanou labelled interleaving distance. That distance is the ℓ∞ distance of the full cophenetic matrices, **including the diagonal** (leaf heights).
- If a map may shift a leaf value by at most δ, which is exactly what an interleaving budget of δ permits, the constraint b_k ≥ ℓ_k becomes b_k ≥ ℓ_k − δ. The optimum is then:

  δ\*_IL(π) = max{0, max_k ½(ℓ_k − C_k), max_{i<j} ½(P_ij − max_{i≤k<j} C_k)}

  The leaf-height term is halved.

**Counterexample.** T = ((i,j)_v, k) with f(i) = f(j) = 0, f(v) = 1, f(k) = 5, f(root) = 6; map order i, k, j.
- Prop. 5 gives δ\* = ℓ − C = 5 − 1 = 4.
- Lowering the displayed value of k to 3 and setting both barriers to 3.5 gives labelled interleaving distance 2.5 = γ_v/2. This is Theorem 2's bound, attained.

**Frequency.** In my random-tree check (400 trees, n = 3–6, 60 orders each; script available on request), δ\*_IL < δ\* for 3.4% of orders, by up to 2.7 value units. The paper itself says the leaf-height term dominates on ERA5 at large budgets (Sec. 7.4, "Tightness"; supplement Remark after Prop. 5). So the fire-versus-pressure contrast and the gap F − Φ both depend on this modelling choice.

**Minimal fix.**
1. State the restriction explicitly in Prop. 5, Thm. 3 and the abstract. For example: "among fillings that display the true extremum values", and "F_T is the exact frontier over maps that preserve extremum values (task T1)".
2. Delete "whatever the filling" in Sec. 5.3, or replace it with "for any filling that preserves leaf values".
3. Add one sentence with δ\*_IL and note that Φ (Corollary 1) remains valid for both notions, since Theorem 2 needs no leaf-value assumption.

Keeping leaf values is a defensible design choice for merge tree maps. It just has to be named as a choice.

### W2 [MAJOR]: Persistence-based simplification is missing, and the conflict statistics depend on it

**Where.**
- Sec. 2 (no simplification literature is cited, although `refs.bib` contains Edelsbrunner:2002, Carr:2004 and Tierny:2012 uncited).
- Sec. 3.1: it is never said whether the merge trees are persistence-simplified; only spatial smoothing is mentioned in Sec. 7.1.
- Sec. 5.2 / 6: γ_v is never distinguished from persistence in the main text. The supplement Remark does distinguish them, and the code docstrings (`theory.py`) call γ_v a "persistence gap".
- Sec. 7.2 (RQ1 robustness).

**What is wrong.** A TopoInVis reader will immediately ask whether most conflicts are caused by noise-level extrema that standard practice would remove. I reran the authors' own pipeline:
- `prototypes/` loaders, `auto_reference`, `universal_parameters`, `theory.dp_tau` at N = 1024, with τ_free from the same DP on the star tree.
- It reproduces the published conflict counts exactly at ε = 0.
- I then removed younger subtrees whose elder-rule persistence was below ε, keeping the remaining widths unchanged (a rough approximation).

| Dataset (conflict frames H > θ) | ε = 0 | 1% of range | 2% | 5% |
|---|---|---|---|---|
| ERA5 1999/2000 | 58% | 42% | 34% | 15% |
| ERA5 2013/14 | 60% | 27% | 18% | 8% |
| Wildfire | 63% | 57% | 33% | 7% |
| Mean leaves ERA5 99/00 | 4.9 | 3.4 | 3.0 | 2.2 |

At about 1 hPa of persistence, half of the ERA5 2013/14 conflict frames disappear. The paper's own case study (Sec. 7.4 "Case") also involves a shallow low at 1019 hPa that merges at 1020.3 hPa, i.e. persistence 1.3 hPa (1.5% of the range).

The headline "58–63%" is therefore a statement about unsimplified merge trees. The paper's robustness checks vary θ, the reference direction, and the width model, but not the persistence threshold, which is the parameter a topology reader expects.

Flattening a merge (keep all extrema, distort merge levels by about γ_v/2) and pruning a branch (delete an extremum, interleaving cost about persistence/2) are the two natural simplifications in the interleaving neighbourhood of T. Only one is discussed.

**Minimal fix.**
1. State the persistence threshold used, if any.
2. Add a persistence-threshold row to the RQ1 robustness sentence.
3. Add two sentences in Sec. 5/6 that contrast flattening with persistence pruning: γ_v is the length of the edge (v, p(v)), i.e. the lifetime of cluster S_v, not the persistence of a branch. Explain why feature-preserving flattening is preferred for T2/T3 (tracked features must not vanish).
4. Cite Edelsbrunner et al. 2002, Carr et al. 2004, and Tierny & Pascucci 2012 (already in `refs.bib`).

Optionally, report how often the best witness triple contains a leaf with persistence below 1–2% of the range.

### W3 [MAJOR]: Positioning against known results on ultrametrics and cluster trees; the novelty sentence about interleaving is unsafe

**Where.** Sec. 2 "Merge tree distances", Sec. 5.1–5.3, contribution bullet 2.

**What is wrong.**
- **Prop. 5 has the same structure as ℓ∞ ultrametric fitting.** For a fixed order, the realizable 1-D merge structures are exactly the ultrametrics whose clusters are intervals of π (order-compatible, or Robinsonian, ultrametrics; Diday's pyramids generalise these). max_{i≤k<j} C_k is the largest such ultrametric below P, i.e. the "subdominant" in that class. The pair term ½ max(P − U) is the classical closed form of Farach, Kannan & Warnow (Algorithmica 1995) for ℓ∞ ultrametric fitting, extended to order constraints by Chepoi & Fichet (J. Math. Psych. 2000, "ℓ∞-approximation via subdominants"). Please check the latter for the exact class it covers.
- **Theorem 2 is the contrapositive of a standard cluster-stability fact.** A cluster whose lifetime exceeds 2ε survives any ℓ∞ ε-perturbation of the ultrametric (Carlsson & Mémoli 2010, among others). Combine that with the observation that 1-D clusters are intervals.
- **d_top is the merge distortion metric** of Eldridge, Belkin & Wang (COLT 2015), restricted to labelled leaves.

None of this invalidates the paper: the application to layouts, the leaf-height term, the width-aware positional side, and the frontier are new as far as I know. But a topology reviewer who recognises these links will read "we prove" as overclaiming unless they are acknowledged.

**"To our knowledge, these distances have not been used to evaluate layouts" is risky.** Persistence-based distances have been used to evaluate projection layouts (Rieck & Leitte, CGF 2015), and TopoMap (Doraiswamy et al., TVCG 2021) builds layouts that preserve 0-dimensional persistence.

**Minimal fix.**
1. One paragraph in Related Work citing FKW 1995, Chepoi–Fichet 2000, Carlsson–Mémoli 2010, Eldridge et al. 2015, Cardona et al. 2013 (cophenetic metrics), and Rieck–Leitte 2015 / TopoMap.
2. Reword the claim to: "Labelled interleaving (merge-distortion) distances have, to our knowledge, not been used to quantify the topology displayed by a 1-D merge tree map; persistence-based distances have been used to evaluate projections [Rieck & Leitte; TopoMap]."
3. After Prop. 5, add: "The pair term is the order-constrained analogue of ℓ∞ ultrametric fitting [FKW95]; the leaf-height term is specific to maps that display extremum values."

### W4 [MAJOR, easy]: Assumptions the theorems need are stated only in the supplement, or nowhere

**Where.** Sec. 3.1, 3.5, 5.1–5.4.

**What is missing from the main text.**
- **(a) Generic values, or equivalently γ_v > 0 for every non-root node.**
  - "δ\*(π) = 0 iff π ∈ Π(T)" (Prop. 5) and F_T(0) = τ\* (Thm. 3) are **false** when γ_v = 0. A binarised multi-saddle can be broken at zero cost.
  - The supplement "Conventions" paragraph contracts such nodes, and |Π(T)| = ∏ deg(v)! also needs unary nodes contracted. The main text says neither.
- **(b) Split-tree sign convention.** γ_v = f(p(v)) − f(v) is negative for split trees (wildfire, Ring). State "negate f for split trees" once, including for m_g (use min instead of max).
- **(c) Anchors must be strictly ordered** (g > 0, ρ ≤ 1). The supplement setting allows g ≥ 0, while Thm. 3 uses g > 0.
- **(d) Conditions for the interleaving interpretation.** It requires no extra minima of the column, including at the canvas ends, and a root extension (Munch–Stefanou). If b_k = ℓ_k (the leaf-height term binds), a labelled anchor stops being a strict local minimum. Please confirm that Munch–Stefanou's labelled merge trees allow labels on non-leaf vertices; otherwise the equality in Sec. 5.1 needs b_k > ℓ_k.
- **(e) The supplement still ends with "Assumptions to double-check" (items 1–3).** This reads as an unfinished audit and must be resolved or removed before submission.

**Minimal fix.** Add a "Conventions" sentence at the start of Sec. 3.5 covering (a)–(c). Add (d) to the Sec. 5.1 qualification. Resolve (e).

### W5 [MINOR]: Algorithm 1 and Proposition 3 differ from the supplement and from the reported numbers

- **Canvas clamps missing.** Algorithm 1, line 3 omits the canvas clamps lo_i = max(0, ·) and hi_i = min(N − W_i, ·). The supplement and `theory.py::_leaf_E` include them. As printed, the algorithm ignores the right canvas end and computes a smaller value than τ\*_disc. Theorem 1 refers to "the window of Proposition 1", but Prop. 1 never defines windows. **Fix:** add the clamps and define [lo_i, hi_i] explicitly.
- **Grid alignment and bisection tolerance.** Prop. 3 omits "canvas grid-aligned" (present in the supplement). The certified bound must also subtract the bisection tolerance (the code does this: `tau_lower` subtracts `(tol + .5)` pixels). **Fix:** state both.
- **The 0.6-pixel agreement looks inconsistent with the λ/2 bound.** "On all ERA5 and Ring frames within 0.6 pixels" (Sec. 4.2) seems to contradict the λ/2 bound of Prop. 3 until one notices that real widths are rounded, so the second part of the proposition applies. That relaxed bound can be loose by up to about (Σ rounding)/2, i.e. O(n) pixels, not λ/2. **Fix:** one clarifying clause.

### W6 [MINOR]: The tightness of Theorem 2 needs a condition

The tightness example needs f(k) ≤ f(v) + γ_v/2; otherwise the leaf-height term forces δ\* > γ_v/2. **Fix:** add this condition to the proof sketch (main text) and to the supplement Remark.

### W7 [MINOR]: Notation clashes (a theory paper at a visualization venue needs clean symbols)

- **g** is both the minimum gap (Sec. 3.5, (D)) and the filling function (Sec. 5). Thm. 3's sketch says "separated by the gap g" next to "filling g".
- **a** is the canvas origin, and **a_i** are the anchors in Sec. 5, which are **u_i** in Sec. 3–4.
- **E_k** (canvas term, Prop. 1) versus **E_S(x)** (earliest function, Thm. 1).
- **S** is used for S_ij, S_v, S_n and the subtree S.
- **C_k** versus constraint (C); **c** is both the width scale and the calibration.
- **T** is both the tree and the number of time steps (Alg. 2, line 2). **W** is both the pixel widths and the set of flattened nodes (Alg. 2).
- **ℓ_k** (leaf height) versus ℓ_k (window lower end, supplement).
- The supplement still uses **δ** for the pixel size while δ is the distortion level; the main text uses λ.
- "τ\*_disc", "τ\*_cont" are undefined in the main text.

**Fix:** rename the gap (e.g. σ), use u_i throughout, rename the canvas term (e.g. R_k), write S_n as 𝔖_n, and sync the supplement.

### W8 [MINOR]: Claims that go beyond what the theorems show

- **Sec. 7.3:** "only relaxation helps, as Corollary 1 predicts." Corollary 1 bounds the maximum position error, not motion-reading reversals. **Fix:** write "consistent with Corollary 1".
- **Sec. 7.4 "Optimality" and Fig. 1b.** The frontier comparison uses τ(π) of the chosen order. The realized layout is chosen within a budget τ\*(T') + β, so its error can exceed τ(π) by up to β = L/120, and "attains the certificate τ\*" in the teaser caption is not literally true. **Fix:** say "within β", or report the realized error.
- **Toy example (Fig. 3).** The formula τ\* = (q_B − q_C + w)/2 assumes g = 0 and ρ = 0 (`paper_figs.py`: B at 59, C at 71), while the model requires g > 0 and the constants use ρ = 0.5. **Fix:** state "g = 0, ρ = 0" in the caption.

### W9 [MINOR]: Related work on merge trees is thin

Beyond W2 and W3, the paper should cite:
- **Merge/contour tree layout:** Pascucci et al. 2004 (branch-decomposition layouts); Heine et al. 2011, "Drawing contour trees in the plane" (TVCG); Oesterling et al., time-varying merge tree visualization (TopoInVis 2015 / Springer 2017).
- **Tracking graphs:** Widanagamaachchi et al. 2012; Saikia & Weinkauf 2017.
- **Merge tree distances:** Beketayev et al. 2014; Sridharamurthy et al. 2020 (edit distance); the Yan et al. 2021 STAR on topological descriptors for comparison.
- **1-D realizations of merge trees:** Curry 2018, "The fiber of the persistence map for functions on the interval". This is the natural home of the Sec. 5.1 observation that merge trees of functions on a line are ordered ("chiral") trees.
- **PQ-trees:** Π(T) is the frontier set of a PQ-tree with only P-nodes (Booth & Lueker 1976).
- **Why the labelled distance:** unlabelled interleaving/GH distance is NP-hard (Agarwal et al. 2018), while the labelled distance is O(n²).

---

## Detailed comments by section

**Definition 1 (Sec. 4.1).** Well posed. Say that τ(π) = +∞ when Σw + (n−1)g > L; the supplement does.

**Proposition 1.** Correct.
- The i = j cases of the chain lemma are covered by the D_k / E_k families; I checked this.
- The requirement h_i ≤ w_i/2 (ρ ≤ 1) is also what makes anchor order equal interval order. Mention it once.

**Proposition 2.** Correct.
- The witness bound could be sharpened to ½·(the gap on the side where k actually lies in π), but as a bound over all of Π(T) the min is right.
- "92–94% of τ\* explained by the best witness" is a nice diagnostic.

**Theorem 1.**
- "E_S(x) … in some legal order" should read "minimised over legal orders".
- **Useful remark:** the subset recursion on the star tree computes τ_free exactly in O(2^n nN) per test. That is cheaper than the n! enumeration used in Alg. 2, line 3, and than the hill-climb in `general_method.tau_free` for n > 6. I used it for W2.
- Your open NP-hardness question is related to single-machine scheduling with release times and deadlines (1|r_j|L_max is strongly NP-hard). Your windows are symmetric around q_i with a common τ, so hardness does not transfer directly. Worth one sentence.

**Proposition 3.** Correct; see W5.

**Proposition 4.** Correct. The proof sketch in the supplement for τ\*_pt ≤ τ\* ("pair terms with w = g = h = 0 are dropped constraints") is imprecise. The correct argument is S_ij ≥ (w_i + w_j)/2 + g ≥ h_i + h_j, because ρ ≤ 1, so every pair term of Prop. 1 is at least ½(q_i − q_j).

**Sec. 5.1 (interleaving).** The qualification is mostly right; add (d) of W4. Also state explicitly that d_top **upper-bounds** the unlabelled interleaving distance between T and the column's merge tree, so Theorem 2 gives no lower bound for the unlabelled distance. That is the reason the labelled distance is the right one here: tracked feature identities matter for T2/T3.

**Theorem 2.** Correct and tight (with W6). The main text should carry the supplement's remark that γ_v is an edge length (cluster lifetime), not elder-rule persistence; see W2.

**Proposition 5.** Correct under leaf-value preservation; see W1. "Raising its existing peak to b_k … so no new extrema appear" is true in the continuous model. In the pixel implementation it needs at least one pixel between anchors; `filling.py` asserts this. Say so.

**Theorem 3.**
- **Independence of positions and filling:** I tried to break it and could not. δ\*(π) depends only on π and the leaf values, the barrier filling needs only strictly separated anchors, and τ(π) is attained with strictly separated anchors when g > 0. So the joint attainment is correct.
- **Limits:**
  - The claim is exact only within the model: fixed widths, filling free between anchors, leaf values kept (W1).
  - The filling "semantics" of merge tree maps (leaf-arc values inside a leaf's interval) are not enforced, so F_T is the frontier of an abstraction slightly larger than the maps actually rendered. It is still a valid lower envelope for rendered maps.
  - F_T(0) = τ\* needs genericity (W4a).

**Corollary 1.** Correct, and it remains valid even for fillings that change leaf values, since Theorem 2 needs no such assumption. That is a point in its favour worth stating.

**Sec. 6.** "Threshold and prune" selects by γ_v, while the realized cost δ\* also contains the leaf-height term. The paper says this in Sec. 7.4; move one sentence of it to Sec. 6.

---

## Questions to authors

1. Are the merge trees persistence-simplified before layout? If not, how do the RQ1–RQ3 numbers change at a persistence threshold of 1–2% of the range (see my table in W2)?
2. Do you intend F_T to be the frontier for leaf-value-preserving maps only? If maps may show extremum depths with error up to δ (the labelled interleaving budget), do you agree the leaf-height term becomes ½(ℓ_k − C_k)? How would this change Fig. 5 and the fire-versus-pressure conclusion?
3. Does Munch–Stefanou's labelled merge tree definition allow labels on non-leaf vertices? This decides whether the equality in Sec. 5.1 survives when b_k = ℓ_k.
4. How does Prop. 5's pair term relate to Chepoi–Fichet's ℓ∞ approximation by order-compatible ultrametrics? Is anything beyond the leaf-height term new?
5. How is τ\*_pt(T) computed for large trees? `pointcert.py` enumerates Π(T). Is there a DP analogous to Theorem 1 with W = G = 0?
6. In Sec. 4.2, which direction is the 0.6-pixel discrepancy, and does it respect the relaxed bound of Prop. 3?

## What would raise my score by one point

1. Qualify Prop. 5, Thm. 3 and the abstract as leaf-value-preserving, and add the one-line δ\*_IL variant (W1).
2. Add the persistence-threshold sensitivity to RQ1 and the flattening-versus-pruning discussion, and cite the simplification papers already in the `.bib` (W2).
3. Add the positioning paragraph (FKW / Chepoi–Fichet / Carlsson–Mémoli / Eldridge et al. / Rieck–Leitte / TopoMap) and reword the novelty sentence (W3).
4. Move the genericity and sign conventions into the main text and remove the "Assumptions to double-check" block from the supplement (W4).

With these changes I would move to 4 (accept). The mathematics is sound; the framing needs to match exactly what is proved.
