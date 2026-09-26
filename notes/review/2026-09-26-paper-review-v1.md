# Simulated PacificVis 2027 review — paper v1 (compiled 2026-09-26)

- **Tool**: ARS `academic-paper-reviewer`, full mode (5 independent reviewers + editorial synthesis). Codex (GPT) was unavailable (usage limit until 2026-09-27 00:26), so all reviewers are Claude agents with distinct personas; a cross-model round is still pending.
- **Material reviewed**: compiled PDF v1 (body ≈ 7 pages), `paper/pacificvis2027/main.tex` (slightly newer: notation fix, new Sec. 3.2), `paper/proofs.tex`, notes, and `prototypes/` code and outputs. Reviewers re-ran parts of the code in scratch space.
- **Individual reports**: `notes/review/panel_v1/R0_eic.md`, `R1_methodology.md`, `R2_topology.md`, `R3_perspective.md`, `R4_devils_advocate.md`.

## Panel configuration (Phase 0)

| ID | Role | Identity |
|---|---|---|
| R0 | EIC / papers chair | SciVis of time-varying fields, topology-based visualization; VIS/EuroVis PC |
| R1 | Methodology | Visualization evaluation, layout-quality metrics, statistics |
| R2 | Domain | TopoInVis: merge trees, interleaving distances, simplification |
| R3 | Perspective | InfoVis: dense pixel displays, ordering/storyline layouts, perception |
| R4 | Devil's advocate | Skeptical senior visualization researcher |

## Scores

| Reviewer | Recommendation | Score (1–5) | Confidence |
|---|---|---|---|
| R0 EIC | Major Revision | 3 | 4 |
| R1 Methodology | Major Revision | 3 | 4 |
| R2 Topology | Major Revision | 3 | 4 |
| R3 Perspective | Major Revision | 3 | 4 |
| R4 Devil's advocate | Major Revision (weak reject as written) | 2 | 4 |

**Editorial decision: Major Revision** (borderline; would likely be rejected at PacificVis in the current form, but the reviewers agree the core is publishable). Because R4 and R1 flag a CRITICAL issue, the decision cannot be Accept (Iron Rule 4).

## Consensus strengths (all or most reviewers)

1. **The theory is correct and novel as a combination.** R2 audited Def. 1, Props. 1–5, Thms. 1–3 and Cor. 1 and found no false statement within the stated model. A random-tree check confirms Prop. 5. R4 agrees the proofs hold. The certificate, the filling-independent price, and the exact frontier are seen as the core contribution (R0, R2, R3).
2. **Numbers are traceable and correct.** R1 spot-checked all 16 cells of Table 2, the paired differences, the RQ1 shares, 368/376, the κ = 2% costs, the teaser numbers, and the dendrogram numbers, and all match the JSON outputs. R4 agrees: the problems are which configuration a number belongs to, not arithmetic.
3. **The width-free certificate and the audit of existing maps** (R3, R0).
4. **Candid limitations** (R4, R1).
5. **An unreported strength**: the relaxed map is the most temporally stable method, even under q-independent measures (R1, R3, R4).

## CRITICAL issue (must fix)

**C1. The abstract and RQ2 mix operating points; the RQ2 relaxed map is κ = ∞ without saying so** (R1 W1, R4 #1, R0 W2).

- `misreading.method_positions` calls `relax_frame_threshold` without `value_cap`, so every R number in Table 2 and in the abstract ("lowers this to 4–15%") is κ = ∞. That setting gives merge distortions of 52–68% of the value range, and nobody tells the reader.
- "98% on the exact frontier" comes from κ = 2%. The teaser uses κ = 20%.
- R1's re-run: at κ = 2% ERA5 reversals are 24.9%, identical to ST-MTM (diff +0.0 pp, CI [−7.4, +6.4]). At κ = 20% they are 14.7% (−10.2 pp).
- **Fix**: report RQ2 as a trade-off over κ ∈ {2%, 20%, ∞}, each with its δ*; state κ in every caption; rewrite the abstract so that each R number carries its κ and its topological cost; make κ an explicit parameter (it is not covered by "a single global constant").

## MAJOR issues (ranked by panel agreement)

**M1. The frontier-optimality claim does not discriminate** (R1 W5, R4).
- Only 54 of 376 frames are relaxed at κ = 2%. The unrelaxed frames sit on F(0) by construction, and κ = 0 gives the same 368/376.
- F is compared with τ(π) (the best error of the chosen order), whereas the teaser shows the realized error, which can exceed τ(π) by up to β.
- **Fix**: report the on-frontier rate among relaxed frames only, per κ, with a naive comparator (greedy one-node policy, or flatten-all without pruning). Label Fig. 5's axis "τ(π) of the chosen order".

**M2. The proxy's projection floor, the in-sample direction, and the omitted baseline** (R1 W2, R4 #2, R3).
- An oracle map that draws q exactly reverses 12.7 / 14.1 / 5.4 / 9.7%. R (κ = ∞) is at this floor.
- The direction is fitted on the same tracks that define the truth, and baselines never see it.
- The fixed-X anchored baseline was computed but left out of Table 2. On Ring (the only dataset with published ST-MTM parameters), ST-MTM beats R. The k = 8 window was computed but not reported.
- **Fix**: add oracle-q and fixed-X rows; report each method's excess over the floor. This actually supports the story: on ERA5, A is about 10 pp above the floor, and that gap is caused by the hierarchy. Add a cross-fitted or fixed-direction R. Report all computed windows. Drop "as Corollary 1 predicts" (the corollary bounds the maximum error, not reversals).

**M3. Reversal-only reporting; statistics** (R1 W3–W4).
- On fire, R trades reversals for misses: rev + miss is 33.0% vs 35.7% for ST-MTM.
- Table 2 has no CIs, and the 8-frame block bootstrap gives only 4 blocks for fire and 5 for Ring.
- "21–34% of feature pairs" should read "clear cases (pair × window)".
- **Fix**: add rev + miss (or Cohen's κ); give paired CIs with a moving-block or sign-flip test; label fire and Ring as descriptive.

**M4. Filling assumption and persistence simplification** (R2 W1–W2).
- Prop. 5, Thm. 3 and "exact frontier of all 1-D maps" hold only for fillings that keep the true extremum values. Under the labelled interleaving distance with free leaf heights, the leaf-height term halves. Counterexample: T = ((i,j)_v, k), f = 0, 0, 5, merges at 1 and 6 gives δ* = 4 vs 2.5. "Whatever the filling" must be qualified.
- Persistence simplification is never discussed. R2 re-ran the pipeline with persistence pruning at 1% / 2% of the range: conflicts drop from 58/60/63% to 42/27/57% and 34/18/33%. The case-study low has persistence 1.3 hPa.
- **Fix**: qualify the statements; add a "persistence simplification" baseline in RQ1 that reports conflicts and the number of features removed. Our flattening keeps every feature; simplification deletes them.

**M5. Visualization contribution is thin; disclosure is not designed or validated** (R0 W1, R3 #1, R4 #3).
- The witness triple is never shown in the paper.
- The frame-level conflict flag covers 85–92% of clear pairs and barely predicts where TMTM/ST-MTM reverse (lift 0.81–1.08).
- R's error strip flags only 13–26% of its own remaining reversals, whereas per-feature flags on A catch 91–96%.
- Barrier-filled pixels (displayed values that are not in the data) are not marked.
- About 2 pages are unused.
- **Fix**: a full-width annotated case study (fig_witness is ready); a disclosure-design subsection; per-feature rather than per-frame flags; mark relaxed or clipped regions.

**M6. Hidden costs** (R1 W7, R3, R4).
- `quality.py` is not yet reported. Its `spurious_flip_rate` and `motion_residual` are q-referenced, and R's QP minimizes the motion residual.
- **Fix**: a 5-metric table with q-independent measures (raw flip rate, anchor jitter, stress, Spearman, NN), an oracle-q row and CIs. It shows that R is the most stable and that its distance preservation is worse than ST-MTM's but equal to the oracle-q projection — an inherent cost of a single reference direction.

**M7. Baselines and positioning** (R0 W3, R1 W6, R3, R2 W3).
- The ST-MTM reimplementation needs validation and a small parameter grid. The ST-MTM reference has no authors (it is an SSRN preprint).
- Missing literature: StoryFlow / storyline layouts; faithfulness (Nguyen, Eades & Hong); the Nonato & Aupetit distortion survey; ultrametric fitting (Farach–Kannan–Warnow; Chepoi–Fichet) for Prop. 5; cluster stability; Eldridge et al.'s merge distortion; Rieck & Leitte 2015 / TopoMap; seriation, PQ-trees and tanglegrams; scheduling with release times and deadlines (related to the open NP-hardness question).
- The claim "interleaving distances have not been used to evaluate layouts" is unsafe.

**M8. Format and presentation** (R0 W4, R3 #3).
- Red TODOs appear in the PDF.
- Figure text is 3–5 pt; all figures are raster.
- Fig. 1c has a dual y-axis; Fig. 6 has a clipped label; Fig. 5 uses code identifiers as panel titles.
- Theorem numbering is separate per environment.
- "and Beyond" rests on one dendrogram demo, and that demo says "rank-scaled" although the code uses linear scaling (the rank version gives 78–82%).

## MINOR issues

- Notation clashes: g is both gap and filling; a is both canvas origin and anchor positions; E_k vs E_S. The pixel-size/δ clash is already fixed.
- Genericity (γ_v > 0) and the split-tree sign convention are missing from the main text.
- Algorithm 1 omits the canvas clamps.
- Prop. 3 omits grid alignment and the bisection tolerance.
- Theorem 2's tightness example needs f(k) ≤ f(v) + γ_v/2.
- The toy figure assumes g = ρ = 0 without saying so.
- The supplement still ends with "Assumptions to double-check".
- The witness 92–94% statistic is not stored in any output JSON.
- "No method falls below the width-free certificate" should say "no hierarchy-preserving method".
- Preprocessing sensitivity (smoothing, maxima cap, the background term in wildfire) is not studied.
- `paper_numbers.py` is stale.

## Revision roadmap (prioritized, ≤ 12)

| # | Item | Addresses | Effort |
|---|---|---|---|
| 1 | RQ2 as a κ trade-off (2%, 20%, ∞) with δ*; state κ everywhere; rewrite abstract/contributions; κ as explicit parameter | C1 | 0.5 day |
| 2 | Oracle-q floor + fixed-X rows + excess over floor; cross-fitted direction; report all windows; rev+miss; paired CIs with adequate blocks | M2, M3 | 1 day |
| 3 | Frontier optimality on relaxed frames only + naive comparator; τ(π) vs realized error labels | M1 | 0.5 day |
| 4 | Qualify Prop. 5 / Thm. 3 ("fillings that show extrema at their true values"); fix tightness example and assumptions; clean supplement | M4, minor | 0.5 day |
| 5 | Persistence-simplification comparison in RQ1 (conflicts + features removed) and related-work paragraph | M4 | 0.5 day |
| 6 | Case study + disclosure design subsection with fig_witness; per-feature flags; mark relaxed/clipped regions | M5 | 1–1.5 days |
| 7 | Hidden-costs table with q-independent measures, oracle row, CIs | M6 | 0.5 day |
| 8 | ST-MTM validation figure (Ring/Gaussians) + small parameter grid | M7 | 1 day |
| 9 | Related work additions (verified citations) and safe novelty wording | M7 | 0.5 day |
| 10 | Figures: vector PDFs, ≥ 7 pt text, no dual axes, fix Fig. 5/6; unified theorem counter; remove TODOs before submission | M8 | 1 day |
| 11 | RQ4: rank vs linear reference, robust (e.g., 95th percentile) version; tone down "and Beyond" or add a second transfer case | M8, R3, R4 | 0.5 day |
| 12 | Preprocessing sensitivity (ERA5 150/350 km, fire cap) + witness statistic into JSON + refresh `paper_numbers.py` | minor | 0.5 day |

---

## 中文摘要

**总体结论：大修（Major Revision）。** 五位审稿人中四位给 3/5，魔鬼代言人给 2/5；置信度都是 4。按现稿投稿，大概率被拒；但所有人都认为核心工作可以发表。

**大家认可的部分：**
- 理论正确，组合起来是新的。拓扑审稿人逐条核对了全部定义、命题和定理，没有发现错误，并用随机树验证了命题 5。
- 所有数字都能在输出文件中找到，而且与正文一致。
- 不依赖宽度的证书，以及用它审视现有地图的做法，得到肯定。
- 局限写得坦诚。
- 还有一个我们没写进论文的优点：放松后的地图在时间上最稳定。

**唯一的 CRITICAL 问题：摘要和 RQ2 混用了不同的预算 κ。**
- 表 2 和摘要中的"读反率降到 4–15%"实际来自 κ = ∞，此时合并值失真达值域的 52–68%，而正文完全没说。
- "98% 落在精确曲线上"来自 κ = 2%；首页图用的是 κ = 20%。
- 审稿人重跑后发现：κ = 2% 时，ERA5 的读反率（24.9%）与 ST-MTM 完全相同；κ = 20% 时才明显下降（14.7%）。
- 改法：把 RQ2 改成随 κ 变化的权衡曲线，每个 κ 都附上拓扑代价 δ\*；所有图表注明 κ；重写摘要。

**主要问题：**
1. **"98% 最优"没有区分度。** κ = 2% 时只有 54 帧真正被放松，其余帧本来就在曲线上（κ = 0 时也是 368/376）。应改为只统计被放松的帧，并与一个朴素的放松策略比较。
2. **读者代理有一个"投影下限"。** 直接把特征画在参考坐标上（不受层次约束）也会读反 12.7–14%，我们的放松已经在这个下限附近；参考方向又是从同一批轨迹拟合的；固定经度基线被算了但没放进表里。应补"理想投影"和固定经度两行，报告每种方法高出下限多少。这样反而能支持我们的论点：在 ERA5 上，保持层次的布局比下限高约 10 个百分点，这正是层次造成的。
3. **只报读反率不够。** 在山火数据上，放松只是把读反变成了漏判，两者合计与 ST-MTM 基本持平。需要补置信区间；山火和 Ring 的 bootstrap 区块太少，应改用更合适的检验，或者标为描述性结果。
4. **理论表述需要限定，并补上与持续性简化的比较。**
   - 命题 5 和定理 3 只对"锚点显示真实极值"的画法成立。审稿人给出反例：允许改动叶值时，叶值项会减半。
   - 必须讨论按持续性简化：审稿人实测，以值域 1–2% 为阈值做简化后，冲突比例从 58–63% 降到 18–57%。要说明我们的"展平"保留了全部特征，而简化会删掉特征。
5. **可视化部分偏薄。**
   - 见证三元组从未在图中展示。
   - 逐帧的冲突标记基本无法预测读反发生在哪里。
   - 最优画法改动过的像素没有标出。
   - 空着的 2 页正好用来补案例和设计。
6. **隐藏代价没有报告。** 现在的 `quality.py` 有两项指标以参考坐标为准，对我们的方法有利，需要换成与参考无关的指标。结论会是：放松后的图最稳定，但二维距离保持不如 ST-MTM，而这与"理想投影"持平，是只用单一参考方向的固有代价，不是放松造成的。
7. **基线和文献定位。**
   - 要验证 ST-MTM 复现的正确性，并跑一个小的参数网格。
   - 要补故事线布局、忠实性、超度量拟合、Eldridge 的合并失真、TopoMap 等文献。
   - "交错距离从未被用于评价布局"这句话不安全，要改。
8. **格式。**
   - 图中文字只有 3–5 pt，且都是位图。
   - PDF 中有红色 TODO。
   - 图 1c 用了双纵轴；图 5 的子图标题是代码变量名；图 6 标签被截断。
   - 定理编号分开计数。
   - 树状图示例写的是"按排名缩放"，代码实际是线性缩放；按排名算应为 78–82%。

**修改路线图**（共 12 项，约 8–9 个工作日）：见上面英文表格。最先要做第 1–3 项：修正 κ 的混用、补投影下限和基线、只在被放松的帧上重新统计最优性。
