# 查新报告：任务参考合并树图（2026-09-26）

流程：`/aris:novelty-check`。

1. 提取核心声明。
2. 多轮网络检索，约 25 条查询。
3. 把材料整理成 dossier：[NOVELTY_DOSSIER.md](NOVELTY_DOSSIER.md)。
4. 交给 GPT（gpt-6-astra，xhigh 推理强度）独立复核。完整原文在 `.aris/traces/novelty-check/2026-09-26_run01/`。
5. 我对复核中新提到的关键文献逐一做了网络核实，全部存在。
6. `verify_papers.py` 因 API 临时故障只核实了 2/19 篇，但没有标记任何伪造。其余文献都在实时检索中以出版社或 arXiv 链接出现过。

## 结论

**PROCEED（可以推进），新颖性 7/10**（按组合整体评分）。

没有找到任何一篇已发表论文完整包含下面这个组合：合并树层次约束 + 外部指定的有单位参考坐标 + 最小偏差证书 + 把偏差画进图里。

- 最强的是 **C1 + C2 的组合**。
- C3 有较多先例。
- C4 主要是需要用实验证明的"好处"，单独算不上新贡献。
- C5 目前只是算法设想，还没有证明。

## 核心声明逐条对照

| 声明 | 最接近的已有工作 | 仍然成立的差异 |
|---|---|---|
| C1：纵轴是任务指定、带单位的参考坐标，同时保持合并树层次 | ST-MTM、TMTM；Hovmöller 图、径向–时间图；Andrienko 2013 的运动数据空间变换（相对群体中心的坐标） | 外部坐标决定特征"应该在哪"；层次和宽度约束迫使偏离时，偏离量被显式约束并量化。任务参考坐标本身不新，新在与合并树约束的结合 |
| C2：LP 求最小最大偏差 τ\*，再在预算内求 QP | **Li & Wang 2019（JoCG）：区间最小最大位移分离，O(n log n)**；MoReVis 的位置优化 | 在合并树允许的叶序内求最小最大偏差（再加宽度、画布、anchor 偏心约束），并用它作为后续优化的硬预算：max\|u−q\| ≤ τ\*+Δ。**把层次约束去掉，C2 就退化成 Li & Wang 的问题**，论文里必须引用并讨论这一点 |
| C3：把偏差画进图里 | Wood & Dykes 2008（空间有序树图的位移向量叠加）；Rauscher et al. 2026（EuroVA，1D 排序失真的视觉增强） | 同时显示"约束下能做到的下界 τ\*"和"实际偏差 e"，单位与参考坐标一致。**单独不足以作为标题贡献**，需要用户实验证明它能帮读者判断哪里不可信 |
| C4：多张图之间可以直接比较 | Beketayev et al. 2012（保几何的拓扑景观，同一定义域上的函数可以直接比较） | 可比性需要统一 φ 的定义、原点、宽度换算系数 c 和简化参数。可以给出误差界：\|(uᴬ−uᴮ)−(qᴬ−qᴮ)\| ≤ \|eᴬ\|+\|eᴮ\|。这是实验要证明的好处，不是独立创新 |
| C5：树上动态规划 + Viterbi 时间优化 | Bar-Joseph 2001（OLO 树上动态规划）；Li & Wang 2019；Bulteau et al. 2022（按外部叶序重排树）；Huson 2026（位移最优的 tanglegram）；Temporal Treemaps 2019、Dobler 2024（全时段优化） | 带宽度和目标窗口、同时满足子树连续性的精确算法还没有人给出。**复杂度目前未知**，"二分搜索 + 树上动态规划"只是一个设想。Viterbi 在运动项依赖连续位置时并不严格精确，只能算在候选布局集合上的最优，应作为实现细节 |

## 新发现的、比我们原先清单更近的工作（均已核实）

- Li & Wang, *Separating Overlapped Intervals on a Line*, JoCG 10(1):281–321, 2019. https://jocg.org/index.php/jocg/article/view/3077
- Beketayev, Weber, Morozov, Abzhanov, Hamann, *Geometry-Preserving Topological Landscapes*, WASA@SIGGRAPH Asia 2012. https://doi.org/10.1145/2425296.2425324
- Andrienko et al., *Space Transformation for Understanding Group Movement*, TVCG 19(12) 2013. https://doi.org/10.1109/tvcg.2013.193
- Huson, *Displacement-Optimized Tanglegrams for Trees and Networks*, MBE 43(3) 2026. https://doi.org/10.1093/molbev/msag066
- Bulteau, Gambette, Seminck, *Reordering a Tree According to an Order on Its Leaves*, CPM 2022（GPT 提供，**尚未独立核实**）
- GroupRugs（Stolk, Wulms, Verbeek, PacificVis 2025）（GPT 提供，**尚未独立核实**）

## 必须注意的技术限定（GPT 复核指出，我同意）

1. **"保拓扑"需要重新证明**。TMTM 的 Merge Tree Identity 证明不能直接套用到 RA 的填充过程上（合作者的 `docs/solver.md` 也这样写了）。要把三件事分开：输入树不变、子树叶集合在布局中连续、输出的 1D 标量函数与原场有相同的合并树。在证明第三件之前，不要在标题里用"topology-preserving"。
2. **坐标保证只针对 anchor**。区间里每个像素并不处于它真实的 φ 坐标上；宽度 w = cA 表示面积，不是沿 φ 方向的空间跨度。图例必须写清楚。
3. **"绝对"这个词不准确**。到移动气旋的距离有单位，但原点是相对的。建议改用 **externally specified, unit-bearing reference coordinate**（外部指定、带单位的参考坐标）。
4. **证书的含义有限**：τ\* ≤ max\|e\| ≤ τ\*+Δ。它只保证在给定约束下最大 anchor 偏差的下界，不保证每个特征的误差，也不单独归因于拓扑。一个很有价值的消融：放松层次约束、保持其他约束不变，两次 τ\* 之差才是"层次连续性"本身的代价。
5. **Hovmöller 的表述要收窄**。Hovmöller 图并不都做平均，也有沿截线或固定方位角采样的。应改为"避免选定的聚合方式把不同的合并树特征合并掉"。

## 审稿人最可能提出的反对意见

> TMTM 提供了保特征的表示，ST-MTM 加了几何，MoReVis 优化了投影位置，区间分离问题早有最优解，失真可视化也有现成工作。除了换一个目标坐标，还剩什么？

能站住的定位：**在保留标量场特征合并树组织的前提下，读出任务坐标上的位置和变化，并对坐标保真度给出可计算的限度。**

实验需要包括：

- 软约束基线：ST-MTM 式布局加参考惩罚项，证明硬预算能保证而调权重做不到的东西。
- 坐标忠实基线：直接把特征画在 q 上，再做去重叠处理，证明层次约束带来了什么。
- 合适的 Hovmöller 变体：平均、切片、截线。
- 可控冲突场景：平移、特征增长、子树顺序冲突、径向拥挤。
- 读者任务实验。
- 小规模实例与完全枚举对照。

## 建议的定位句

> Task-referenced merge tree maps organize scalar-field features along an externally specified coordinate with physical units, preserve their hierarchical contiguity and fixed measure encoding, and compute and display the minimum reference deviation required by those layout constraints.

标题主张：**Task-referenced merge tree maps with explicit bounds on coordinate distortion.**

## 主要风险

- **新颖性**：如果只是"换一个 q + 常见的位移叠加 + 几个例子"，审稿人会认为差异太薄。必须靠形式化的保证和它带来的分析价值撑住。
- **技术**：不要过度声称"完全保拓扑""全局不可避免的误差""时间上全局最优"。
- **实用性**：径向距离、到焦点的距离这类参考不是单射，很多特征可能挤在一起，导致偏移过大，削弱读数。**这一点要靠原型实验检验**，见 `notes/2026-09-26-prototype.md`。
