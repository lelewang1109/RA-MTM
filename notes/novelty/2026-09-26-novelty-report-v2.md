# 查新报告 v2：新定位（可证明的位置–拓扑权衡）（2026-09-26）

- 流程：`/aris:novelty-check`，第二轮。检索词按 8 条研究线分组，约 40 组。候选文献 42 篇，全部核实存在：32 篇经 CrossRef 标题匹配，10 篇经 arXiv / LIPIcs / 出版社页面直接确认（ARIS 自带的核验工具因 Semantic Scholar 限流 429 未能完成）。
- 材料：[NOVELTY_DOSSIER_v2.md](NOVELTY_DOSSIER_v2.md)
- **GPT 交叉审稿未完成**：本轮调用 Codex 时触发了用量上限（到 14:11 恢复），已在 `.aris/traces/novelty-check/2026-09-26_run01/002-*` 记录。下面的判断**由我独立完成**，建议额度恢复后补跑一次。
- 完整相关工作地图见 [../related-work-map.md](../related-work-map.md)。

## 结论

**PROCEED（可以推进），新颖性 7/10。**

没有发现任何已发表工作包含以下内容：
- 在"合并树子树必须连续 + 宽度正比于测度"的约束下，给出位置偏差的**精确下界**，并把它分解成层次部分与空间部分；
- 以拓扑距离度量的**位置–拓扑权衡曲线**；
- 真实气象数据上"冲突普遍存在且代价高"的量化结论。

邻近工作很多，但差异可以明确陈述，也能被审稿人核实。

## 核心声明逐条对照

| 声明 | 最接近的工作 | 仍然成立的差异 | 新颖度 |
|---|---|---|---|
| C1 忠实度模型（拓扑 / 位置 / 大小） | Kindlmann & Scheidegger 2014（代数设计原则）；Meulemans 2026（主张把"质量定义"与算法分开，否则质量无法定义也无法测量）；制图变形地图文献对面积 / 形状 / 拓扑误差的三分法 | 专门针对合并树时空图的形式化，并把 TMTM / ST-MTM 定位为同一空间中的不同取舍点 | 中（框架性，Meulemans 2026 是很好的引子） |
| C2 偏差证书 τ\* + 分解 | **Li & Wang 2019**（区间最小最大位移，允许任意顺序，O(n log n)）；IPSep-CoLa 2006（分离约束的二次规划）；地理系统发育图系列 2023/2025/2026 与 Bulteau 2022、Huson 2026（受树约束的叶序，但目标是交叉数、逆序数或位移总和，不是带宽度的最小最大下界） | 在合并树子树连续、宽度、间距、画布、anchor 偏心的约束下，给出最大偏差的**精确最优值**；固定叶序时有闭式解；并分解为层次代价与空间代价。**没有发现先例** | **高**（相对可视化领域）。算法上是"枚举 + 闭式解"，技术深度中等 |
| C3 证书驱动的放松 + 拓扑代价 | van Beusekom et al. 2023 数据–空间网格图（在空间布局与数据布局之间渐变，是"权衡导航"最接近的先例）；持久性简化（删掉弱特征，但改变的是数据本身）；Munch & Stefanou 2019（ℓ∞-cophenetic = 带标签交错距离，但只用于比较树） | 不修改数据，只放松布局中的连续性；按持久性顺序进行；代价用**带标签交错距离**度量（已验证：ERA5 放松的 51 帧中，一维图的叶子数与原树完全一致，没有伪极值，所以两者等价）。**没有发现有人用交错距离评估线性化或布局** | 高 |
| C4 实证发现（ERA5 冲突 58%；误差减半需约 28 hPa） | 没有找到任何量化工作。GroupRugs 2025 等只做了定性讨论或给出各项指标 | 首次量化；适用于整个方法族 | 高（但必须做稳健性分析） |
| C5 自动方向 + 统一常数 | Wulms et al. 2021 Stable Principal Components（对位置做 PCA）；MotionRugs 的 PCA 排序 | 对**运动位移**做 PCA，而不是对位置；差异很小 | 低 → **降为实现细节** |

## 最接近的已有工作

| 工作 | 年份 | 会议 / 期刊 | 重叠 | 关键差异 |
|---|---|---|---|---|
| Köpp & Weinkauf，TMTM | 2023 | TVCG | 保合并树的线性化 | 不处理几何位置，没有失真度量 |
| ST-MTM | 2026 | C&G 投稿 / SSRN 预印本 | 距离感知的合并树线性化 | 只保相对距离，没有下界和权衡 |
| **Stolk, Wulms, Verbeek，GroupRugs** | 2025 | **PacificVis**（同一会议） | 组内连续 + 空间质量 + 稳定性的一维摘要 | 排序而非度量位置；组是扁平的，没有合并层级；没有下界和放松曲线；数据是轨迹 |
| Li & Wang，Separating Overlapped Intervals | 2019 | JoCG | 最小最大位移 | 没有层次约束，也不用于可视化 |
| van Beusekom et al.，Data-Spatial Layouts for Grid Maps | 2023 | GIScience | 空间与数据布局之间的渐变权衡 | 网格图、非层次、非拓扑度量 |
| Beketayev et al.，Geometry-Preserving Topological Landscapes | 2012 | WASA@SIGGRAPH Asia | 保拓扑的同时加入几何邻近 | 静态二维景观，没有下界 |
| Munch & Stefanou，ℓ∞-Cophenetic = Interleaving | 2019 | 会议论文集 | 我们拓扑代价的理论基础 | 只比较树，不评估布局 |
| Klawitter et al.，Visualizing Geophylogenies | 2023/2025 | GIScience / JGAA | 树约束叶序 vs 地图位点 | 目标是交叉数，叶子等距 |
| Wood & Dykes，Spatially Ordered Treemaps | 2008 | TVCG | 层次布局中的位置一致性，画出位移向量 | 二维树图，没有下界 |
| Meulemans，Algorithmic Perspective on InfoVis | 2026 | arXiv | 主张质量必须可定义、可测量 | 立场论文 |

## 审稿人可能的质疑与应对

| 质疑 | 应对 |
|---|---|
| "这就是 Li & Wang 加一个树约束" | 层次约束恰恰是核心：它产生的层次代价在 ERA5 上占到轴长的 31%；而且我们的用途是可视化证书和权衡，不是解一个组合问题 |
| "枚举叶序不可扩展" | 报告 ERA5（最多 11 个叶子）的运行时间；多项式算法列为未来工作 |
| "有权衡是显然的" | 显然的是"存在"；"有多大、在哪里、为什么"此前没人量化过，我们给出了精确下界、真实数据上的曲线和代价归因 |
| "58% 依赖 θ 和方向" | 必须做 θ × 方向 × 时间步 × 简化阈值的稳健性扫描，报告区间 |
| "与 GroupRugs 的关系" | 同一会议，必须在相关工作中正面比较：它面向轨迹、扁平分组、排序质量；我们面向标量场、合并层级、度量位置和可证明下界 |

## 建议的定位句

> We give the first exact, per-time-step lower bound on how far a merge-tree-preserving 1-D map must displace features from their spatial reference, attribute it to hierarchy versus space, and chart — using the labeled interleaving distance — how much merge-tree fidelity must be given up to reduce it; on ERA5 this trade-off is pervasive and expensive.

## 仍需完成

- [ ] Codex 额度恢复后，重跑交叉审稿（用同一份 dossier）
- [ ] 稳健性扫描，支撑 C4
- [ ] 通读 GroupRugs 全文，写出与它的精确对比（同一会议，审稿人很可能是这个圈子的人）
