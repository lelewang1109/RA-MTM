# Research summary for external review (2026-09-26)

Repository: /Users/yudong/Research/RA-MTM (read anything). Target: IEEE PacificVis 2027 conference track (9 pages + 2 refs; abstract Nov 2, paper Nov 9, 2026). Authors: a PhD-level visualization researcher and a collaborator whose unpublished prototype (reference-anchored merge tree layout via LP + QP, `src/ramtm/error_budget.py`) is part of our method, NOT prior work.

## Problem
Merge tree maps (TMTM, Köpp & Weinkauf, TVCG 2023; ST-MTM, C&G 2026 preprint) linearize each time step of a time-varying 2-D scalar field into a 1-D column while preserving the merge tree (every subtree's leaves contiguous), then stack columns over time. Readers use them to judge where features are and whether they approach or separate. No existing method bounds or reports how much such a map must misrepresent space. More broadly, the same "hierarchy-constrained 1-D layout vs. positional reference" conflict appears in dendrogram-ordered dense-pixel displays (Franke et al. 2021; MotionRugs family), clustered heatmaps, geophylogenies, storylines with location axes.

## Contributions (current)
1. Fidelity model: merge tree maps as hierarchy-constrained 1-D interval layouts (widths ∝ measure, gap, canvas, anchor eccentricity); topology / position / size fidelity.
2. Certificate τ*: exact min over hierarchy-consistent layouts of the max reference deviation. Closed form for a fixed order (Prop. 1, via chain-with-box-windows lemma); decomposition hierarchy cost H = τ* − τ_free ≥ 0 (Prop. 3); witness-triple lower bound (Prop. 4, explains *which* three features conflict).
3. Theorem 1: exact pseudo-polynomial DP at display resolution (earliest-next-start functions composed over the tree; O(n N log) for binary trees; O(2^m m N) per m-ary node); discretisation gap ≤ δ/2 (Prop. 5). Replaces exponential enumeration.
4. Theorem 2 (topological price of non-contiguity): for ANY 1-D map (any layout, any scalar filling), if node v's leaf set is non-contiguous then the leaf-pair merge-level distortion d_top ≥ (f(parent v) − f(v))/2; tight in general. d_top equals the ℓ∞-cophenetic = labeled interleaving distance (Munch & Stefanou) when no spurious extrema (Prop. 6).
5. Corollary 1 (position–topology lower frontier): any 1-D map has max position error ≥ Φ_T(d_top), Φ_T(δ) = τ*(T with all nodes of gap ≤ 2δ flattened). Our certificate-driven relaxation (flatten weakest merges while H > θ) achieves the full gap (factor 2 from the bound).
6. Empirical: misreading (reader-proxy) analysis + conflict prevalence on 3 real datasets (2 domains) + 2 synthetic.

Full proofs: `paper/proofs_zh.md` (Chinese). Code: `prototypes/theory.py` (DP, frontier), `prototypes/relax_hierarchy.py` (closed form, relaxation, merge-level distortion), `prototypes/misreading.py`, `prototypes/replicate.py`, `prototypes/frontier.py`, `prototypes/generality.py`.

## Verification of theory (numerical)
- Closed form vs LP: max diff 2e-14. DP vs brute force on 300 random hierarchies: max 0.495 px (Prop. 5 bound 0.5 px). DP vs closed form on all 158 ERA5/Ring frames: < 0.6 px, 2 ms/frame. DP 4096 leaves / 16384 px: 4.0 s.
- Theorem 2 checked on 783 frame-instances with broken contiguity across 5 datasets × 8 relaxation caps: 0 violations; measured d_top / gap median 1.00.
- Frontier: all achieved points above Φ (`prototypes/output/frontier.json`).

## Empirical results (θ = 2% of axis everywhere; no per-dataset method parameters)
Datasets: ERA5 MSLP Europe 1999-11-17..2000-01-14 (118 frames, 12 h; features identical to collaborator's CDS protocol), ERA5 winter 2013-12..2014-01 (124 frames), Australian wildfire FRP 10 km (Franke et al. Zenodo; Nov–Dec 2019, 2-day sums, 30 frames, 64×64, smoothing = smallest σ giving ≤ 12 maxima), Ring (TMTM/Franke synthetic), Gaussian (replica of ST-MTM motivating scene).

RQ1 conflict prevalence (H > θ): ERA5 58%, ERA5-2014 60%, wildfire 63% of frames; max H 31% / 38% / 20% of axis; space cost < 5%.

RQ2 misreading (reader proxy: pair distance on the map shrinks/grows by > 2% of axis ⇒ "approach/separate"; truth = real 2-D extremum distance change > 2% diagonal; reversal = clear opposite; chance = shuffled map changes; 95% CI by frame bootstrap), k = 1 step window:
| dataset | TMTM | ST-MTM | ours (topology kept) | ours (relaxed) |
|---|---|---|---|---|
| ERA5 (24 h) | 33.7% [29,38] (chance 40%) | 24.9% [20,30] | 22.4% | 16.7% [13,21] |
| ERA5-2014 (24 h) | 29.4% (chance 37%) | 27.9% [22,33] | 22.1% | 20.2% [15,26] |
| wildfire (4 d) | 21.4% (chance 36%) | 21.4% | 16.1% | 5.4% [1,11] |
| Ring | 22.6% | 7.3% | 15.3% | 8.1% |
Sensitivity to reader threshold 1/2/5%: ranking stable on ERA5; at 5% relaxed ≈ ST-MTM on ERA5-2014; Ring ST-MTM ≈ relaxed.
Frame-level certificate does NOT predict TMTM/ST-MTM misreadings (lift ≈ 1) — reported as a limitation.

RQ3 trade-off (cap on merge-level change per relaxation step, fraction of value range): ERA5 −9% mean error at 2% (1.6 hPa), −42% at 20% (27.8 hPa), −60% unlimited (58 hPa max, 10% of leaf pairs); ERA5-2014 −12% / −52% / −63%; wildfire −38% at 2%; Ring −18% at 2%.

Generality (dendrogram-ordered dense pixel display, 1024 wildfire cells, one row each): hierarchy from FRP time-series similarity (Franke-style) forces H = 47–48% of display height (τ* 67–69%) vs spatial Ward dendrogram H = 1.4%; exact DP in 0.1 s.

Negative results (kept): automatic radial centres follow tracking artefacts; "stability priority" conflict policy does not generalise; per-feature disclosure ticks illegible on ERA5; dual X/Y maps abandoned.

## Open issues
Proof review (esp. Theorem 1 optimal-substructure argument and Munch–Stefanou label conventions); reader proxy not a human study; ERA5 via ARCO mirror (to be rerun on CDS file); only exact for ≤ ~12 leaves per m-ary node; visual encoding of certificate still prototype; paper draft being rewritten (Chinese first, `paper/draft_zh.md`).
