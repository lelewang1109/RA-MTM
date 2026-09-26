# 相关工作地图（2026-09-26，用于论文 Related Work 与对比）

- **核实状态**：全部 42 篇已核实存在。32 篇来自 CrossRef 标题匹配（`notes/novelty/verified_v2_crossref.json`）；10 篇为 arXiv / LIPIcs / 出版社页面直接确认，标记为 ◆。
- **优先级**：★ 必须引用并正面比较；○ 应引用；· 可选背景。
- 带 † 的条目由 GPT 在第一轮查新中提供，只核实了存在性，还没通读。

## A. 合并树 / 线性化的静态时空图（直接前作）

| | 工作 | 与我们的关系 | 差异 |
|---|---|---|---|
| ★ | Köpp & Weinkauf, *Temporal Merge Tree Maps*, TVCG 2023 | 基础方法，保合并树 | 纵轴没有几何含义，也没有失真度量 |
| ★ | *Spatiotemporal Merge Tree Maps*, C&G 投稿, SSRN 6604235 | 在合并树约束下保相对距离 | 没有下界；把失真当作"弹簧效应"定性讨论（§7.1–7.2） |
| ★ | Franke et al., *Visual Analysis of Spatio-temporal Phenomena with 1D Projections*, CGF 2021 | 多种一维投影供选择 | 不保特征或拓扑 |
| ○ | Zhou, Johnson, Weiskopf, *Data-driven space-filling curves*, TVCG 2021 ◆ | 数据自适应线性化 | 不保特征 |
| ○ | Hovmöller 图（1949）；热带气旋的径向–时间图 | 固定参考轴 × 时间 | 对另一维做聚合或切片，特征被合并 |

## B. 运动数据的一维摘要

| | 工作 | 关系 | 差异 |
|---|---|---|---|
| ★ | **Stolk, Wulms, Verbeek, *GroupRugs*, PacificVis 2025** | **同一会议**；组连续 vs 空间质量 vs 稳定性的权衡，用整数规划最小化交叉 | 轨迹数据；扁平分组；衡量排序质量（邻域）而非度量位置；没有下界和放松曲线 |
| ★ | Buchmüller et al., *MotionRugs*, TVCG 2019 | 一维排序 × 时间的原型 | 不保特征 |
| ○ | Wulms et al., *Stable Visual Summaries for Trajectory Collections*, PacificVis 2021 | Stable PCA：投影到平滑变化的主方向 | 与我们的自动方向接近（我们对位移做 PCA） |
| ○ | *SpatialRugs* ◆（arXiv 2003.12282） | 用颜色编码二维位置 | 标量图里颜色已经被占用 |
| ○ | Valdrighi et al., *MoReVis*, TVCG 2024 | 标记尺寸与位置优化，接近原始空间 | 没有层次约束和下界 |
| ○ | Rauscher et al., *Visually Assessing 1-D Orderings of Contiguous Spatial Polygons*, CGF 2025 | 一维排序的质量评估 | 多边形数据，没有拓扑 |
| ★ | Rauscher et al., *Visual Boosting Techniques for Spatiotemporal Dense Pixel Visualizations*, EuroVA 2026 ◆ | 在图中标示线性化失真 | 标示的是邻域失真，不是可证明的偏差下界 |
| ○ | Andrienko et al., *Space Transformation for Understanding Group Movement*, TVCG 2013 | 任务相关的参考坐标 | 不涉及合并树 |

## C. 基于拓扑的时变 / 树布局

| | 工作 | 关系 | 差异 |
|---|---|---|---|
| ○ | Köpp & Weinkauf, *Temporal Treemaps*, TVCG 2019 | 演化树的静态布局，全时段优化 | 不处理位置 |
| ○ | Dobler & Nöllenburg, *Improving Temporal Treemaps by Minimizing Crossings*, CGF 2024 | 对时变树布局做精确优化 | 目标是交叉数 |
| ○ | Lukasczyk et al., *Nested Tracking Graphs*, CGF 2017 | 层次特征演化 | 固定阈值，不处理位置 |
| ★ | Weber, Bremer, Pascucci, *Topological Landscapes*, TVCG 2007 | 构造与原场拓扑等价的替代场 | 二维地形，不讨论空间位置失真 |
| ★ | Beketayev et al., *Geometry-Preserving Topological Landscapes*, WASA 2012 | **保拓扑的同时加入几何邻近**，支持比较 | 没有下界，也没有权衡曲线 |
| ○ | Heine et al., *Drawing Contour Trees in the Plane*, TVCG 2011 | 等值线树绘制的审美准则 | 抽象树绘制 |
| · | Lohfink et al., *Fuzzy Contour Trees*, CGF 2020 | 多棵树的联合布局 | |
| · | *Analyzing Time-Varying Scalar Fields using PL Morse–Cerf Theory*, VIS 2025 | 时变临界点演化图 | 不是空间线性化 |
| · | Wetzels et al., *Merge Tree Geodesics and Barycenters with Path Mappings*, TVCG 2024 | 合并树的嵌入与平面布局 | |

## D. 合并树距离（拓扑代价的理论基础）

| | 工作 | 关系 |
|---|---|---|
| ★ | Munch & Stefanou, *The ℓ∞-Cophenetic Metric … as an Interleaving Distance*, 2019 | **我们的拓扑代价 = 带标签合并树的 ℓ∞-cophenetic 距离 = 带标签交错距离**。已验证：放松后的一维图叶子数与原树相同 |
| ★ | Morozov, Beketayev, Weber, *Interleaving Distance between Merge Trees*, 2013 ◆ | 交错距离的原始定义 |
| ○ | Gasparovic et al., *Intrinsic Interleaving Distance for Merge Trees*, La Matematica 2024 | 带标签版本的 O(n²) 计算 |
| ○ | Yan et al., *Geometry-Aware Merge Tree Comparisons … Interleaving Distances*, TVCG 2022/2023 | 在可视化中用交错距离做时变比较 |
| ○ | *ParkView: Visualizing Monotone Interleavings*, PacificVis 2025 | 如何**展示**交错，可借鉴来标注放松的位置 |
| · | *Locally Correct Interleavings Between Merge Trees*, SoCG 2026 ◆；*A Practical Algorithm for (Geometry-Aware) Interleavings*, SEA 2026 ◆ | 最新算法 |

## E. 一维放置与排序算法

| | 工作 | 关系 | 差异 |
|---|---|---|---|
| ★ | **Li & Wang, *Separating Overlapped Intervals on a Line*, JoCG 2019** ◆ | 无层次约束时，我们的 τ_free 就是这个问题（我们多了画布和偏心约束） | 没有层次约束 |
| ○ | Dwyer, Koren, Marriott, *IPSep-CoLa*, TVCG 2006 | 分离约束的二次规划布局，对应我们的第二阶段 | 没有下界证书 |
| ○ | Bar-Joseph et al., *Fast optimal leaf ordering*, 2001 | 在树允许的叶序上做动态规划 | 目标是相邻叶子的相似度 |
| ○ | Brusco & Stahl, *Optimal least-squares unidimensional scaling*, Psychometrika 2005 | 一维尺度化是 NP-hard，用精确方法求解 | 没有层次约束 |
| ○ | Bulteau, Gambette, Seminck, *Reordering a tree according to an order on its leaves*, CPM 2022 ◆† | 让树的叶序去贴合外部给定的顺序 | 离散顺序，没有宽度和度量位置 |
| ○ | Huson, *Displacement-Optimized Tanglegrams*, MBE 2026 | 受树约束的位移最小化 | 两棵树对齐，没有宽度和画布 |
| ★ | Klawitter et al., *Visualizing Geophylogenies*, GIScience 2023 / JGAA 2025 | **树约束叶序 vs 地图位点**，组合结构最接近 | 目标是引线交叉数，叶子等距 |
| ○ | *Paged Geophylogenies*, arXiv 2607.23559（2026）◆ | 同上的最新进展 | |
| · | *Versatile Ordering Network*, VIS 2025 | 学习式排序，面向多种质量指标 | |
| · | *Constrained Boundary Labeling*, arXiv 2402.12245 | 带顺序约束的标注；一般情形 NP-hard | |

## F. 地图式布局中的权衡与保证

| | 工作 | 关系 |
|---|---|---|
| ★ | van Beusekom, Meulemans, Speckmann, Wood, *Data-Spatial Layouts for Grid Maps*, GIScience 2023 ◆ | 在空间与数据布局之间**渐变**，是"权衡导航"最接近的先例 |
| ★ | Wood & Dykes, *Spatially Ordered Treemaps*, TVCG 2008 | 层次布局中的位置一致性，画出位移向量 |
| ○ | Nusrat & Kobourov, *The State of the Art in Cartograms*, CGF 2016 | 面积、形状、拓扑三类误差的权衡框架 |
| · | *Treemaps with Bounded Aspect Ratio*, CGTA 2014 | 可视化布局中的可证明保证（反例：矩形无法保证有界纵横比） |
| · | *Adjacency-Preserving Spatial Treemaps*（arXiv 1105.0398） | 层次 + 空间邻接 |

## G. 失真可视化与设计理论

| | 工作 | 关系 |
|---|---|---|
| ○ | Aupetit, *Visualizing distortions and recovering topology in continuous projection techniques*, 2007 | 把投影失真直接画在图上 |
| · | CheckViz（2011） | 用二维色表编码两类失真 |
| ★ | Kindlmann & Scheidegger, *An Algebraic Process for Visualization Design*, TVCG 2014 | 忠实性原则（数据与视觉的对应），可作为理论引子 |
| ★ | Meulemans, *An Algorithmic Perspective on Information Visualization*, arXiv 2607.29360（2026）◆ | 主张质量必须先定义、才能测量；我们的证书正是这样做的 |

## 对论文的直接影响

1. **与两篇前作的对比要扩展为"三线对比"**：
   - 合并树图线：TMTM、ST-MTM；
   - 一维运动摘要线：MotionRugs、GroupRugs、MoReVis；
   - 带约束的一维放置线：Li & Wang、地理系统发育图、IPSep-CoLa。
   相关工作一节按 A–G 组织，约 0.75 页。
2. **实验对比建议**：TMTM、ST-MTM、固定 X 轴的 RA-MTM 作为方法基线；无层次约束的 τ_free（即 Li & Wang 情形）作为理论对照。GroupRugs 数据类型不同，只在文字中比较。
3. **理论表述**：拓扑代价直接定义为带标签交错距离，引用 Munch & Stefanou 和 Morozov et al.；它是真正的度量，并且有稳定性保证。
