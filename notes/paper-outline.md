# 论文大纲 v1（academic-paper outline-only，2026-09-26）

> 本文件由 ARS `academic-paper` 的 outline-only 模式生成，依次完成三个阶段：配置 → 文献 → 结构与证据映射，**不包含正文初稿**。
> 所有数字都取自 `notes/` 里的原型结果（ERA5 为 ARCO 12 小时数据）。**投稿前须用 CDS 原始文件重跑一次**。
> 标 ❗ 的是尚缺的证据或证明，汇总在 §E。

---

## A. 论文配置记录（Phase 0）

| 项 | 值 | 状态 |
|---|---|---|
| 会议 | IEEE PacificVis 2027，Conference Paper Track（普通研究论文） | 用户已给出 |
| 截止 | 摘要 2026-11-02，全文 2026-11-09（投稿前在官网确认时区） | 已查证 |
| 篇幅 | 正文 9 页 + 2 页（仅限参考文献和致谢） | 已查证 |
| 模板 | IEEE VGTC conference 模板（LaTeX，双栏） | **❓ 待确认**：下载官方 CfP 模板 |
| 审稿方式 | 官网未写明是否双盲 → **按双盲准备**：不附合作者公开的 GitHub 链接，自引用第三人称 | **❓ 待确认** |
| 论文类型 | 技术 + 分析论文：可证明的方法 + 实证刻画 | 用户已同意转向 |
| 引用格式 | IEEE 数字编号 | 默认 |
| 写作语言 | 英文；本大纲说明用中文，关键论点句用英文 | 用户指定 |
| 正文字数预算 | 约 6,300 词（按 9 页双栏、约 30% 版面给图表估算） | 估算 |
| 作者 | 用户（ydvislab）与合作者（lelewang1109）；署名顺序待定 | **❓ 待定** |

## B. 文献阶段（Phase 1）

已完成，见 [related-work-map.md](related-work-map.md)（42 篇，全部核实过存在，按 A–G 七类分组）和 [novelty/2026-09-26-novelty-report-v2.md](novelty/2026-09-26-novelty-report-v2.md)（PROCEED，7/10）。下文引用时用文献地图里的简称。

---

## C. 论文大纲（Phase 2）

### 结构模式

混合型"技术论文"。以 Conference 模式为骨架，把方法部分拆成"模型 → 证书 → 权衡导航"三节，评估按研究问题（RQ）组织。这是 PacificVis / VIS 技术论文的通行结构。

### 标题候选

1. **How Faithful Can a Merge Tree Map Be? Certified Position–Topology Trade-offs in Static Visualizations of Time-Varying Scalar Fields**（首选）
2. Certified Merge Tree Maps: Bounding and Trading Positional Distortion Against Topology
3. Where Merge Tree Maps Must Lie: …（偏口语，备选）

### 全文主线（一段话）

合并树时空图（TMTM、ST-MTM）把每个时刻的二维标量场压成一列一维像素，同时保持合并树。它们各自优化某种目标，却从不告诉读者图在空间上有多失真。

我们先把这类图形式化为"满足层次约束的一维区间布局"，区分拓扑、位置、大小三种忠实度。在此基础上证明：对每一帧，任何保合并树的布局，其位置偏差都有一个可精确计算的下界 τ\*；它可以分解为层次造成的部分和空间造成的部分。然后给出按持久性顺序、由证书触发的局部放松，并用带标签交错距离度量拓扑代价，从而画出位置–拓扑权衡曲线。

在两个合成数据和 ERA5 上的实验表明：真实天气数据中冲突普遍存在（58% 的帧），而且代价高（位置误差降低 42% 需要 27.8 hPa 的合并失真）。据此给出针对整个方法族的设计建议。

---

### 0. Abstract（约 180 词，固定）

五句结构。关键论点句草稿：
1. 问题：*Merge tree maps summarize a time-varying scalar field in one static image by linearizing each time step while preserving its merge tree, but they do not tell the reader how far features are displaced from where they are in space.*
2. 问题的核心：*We ask how faithful to spatial position such a map can be at all.*
3. 方法：*We model merge tree maps as hierarchy-constrained 1-D interval layouts and derive, for every time step, an exact lower bound on the positional error that any merge-tree-preserving layout must incur, attributing it to hierarchy or to space; a certificate-driven relaxation then trades merge-tree fidelity—measured by the labeled interleaving distance—for position.*
4. 结果：*On ERA5 sea-level pressure, hierarchy-induced conflicts occur in 58% of time steps; reducing the mean positional error by 42% requires distorting merge levels by up to 27.8 hPa.*（❗ 数字须用 CDS 数据和稳健性区间更新）
5. 意义：*The bound makes the geometric fidelity of merge tree maps certifiable and exposes a trade-off that affects the whole family of topology-based static maps.*

关键词：merge trees; time-varying scalar fields; static visualization; linearization; layout optimization; faithfulness; interleaving distance

---

### 1. Introduction（约 950 词，1.0 页，含 Fig. 1）

**目的**：用一个看得见的问题抓住读者，提出研究问题，列出贡献，并预告带数字的发现。

- **1.1 背景**（1 段）
  - 静态图是动画的补充：它能一次展示全部时间，适合打印、比较和发现短暂事件（引用 TMTM §1、ST-MTM §1）。
  - 两条路线：空间填充曲线线性化（Franke 2021、Zhou 2021），以及基于合并树的线性化（TMTM → ST-MTM）。
- **1.2 问题**（1 段，配 Fig. 1）
  - 一维纵轴把二维空间压扁了，失真不可避免（ST-MTM §7.2 自己承认，并称之为"弹簧效应"）。
  - 但现有方法都**不报告**失真有多大、在哪里。读者看到两条带靠近，无法判断是真实接近还是布局造成的。
  - 论点句：*Every merge tree map lies about space somewhere; none of them says where, or by how much.*
- **1.3 研究问题**（1 句，加粗）
  - **RQ: How faithful to a spatial reference can a merge-tree-preserving 1-D map be, and can its unfaithfulness be bounded, located, and controlled?**
- **1.4 思路**（1 段）
  - 把"布局方法之争"变成"可证明的界 + 可控的权衡"。
  - 呼应 Meulemans 2026：质量必须先被定义，才能被度量和保证。
- **1.5 贡献**（编号列表，与 §4–§7 一一对应）
  1. 忠实度模型：统一 TMTM / ST-MTM / 参考锚定图，区分三种忠实度（§4）。
  2. 偏差证书：精确下界 τ\*、固定叶序的闭式解、层次 / 空间分解（§5）。
  3. 证书驱动的局部放松：拓扑代价 = 带标签交错距离，得到位置–拓扑权衡曲线；默认无需按数据集设参数（§6）。
  4. 实证刻画：ERA5 与合成数据上冲突的普遍性和代价，以及对方法族的设计含义（§7–§8）。
- **1.6 主要发现预告**（1–2 句带数字）
- **过渡**：先交代相关工作与合并树图的背景。

来源：TMTM、ST-MTM、Franke 2021、Zhou 2021、Meulemans 2026、Kindlmann & Scheidegger 2014。

---

### 2. Related Work（约 700 词，0.75 页）

**目的**：沿三条主线说明"没有人给出过保层次一维布局的失真下界或权衡曲线"。

- **2.1 Static visualizations of time-varying fields**
  - Hovmöller 图 / 径向–时间图：聚合或切片会合并特征。
  - 空间填充曲线：Franke 2021、Zhou 2021。
  - TMTM、ST-MTM：差异见 §3。
  - 拓扑景观：Weber 2007；Beketayev 2012 在保拓扑的同时加入几何邻近，但**没有下界**。
- **2.2 1-D summaries of movement and regions**
  - MotionRugs、Stable Visual Summaries、SpatialRugs、MoReVis。
  - **GroupRugs（PacificVis 2025）必须单独一句话比较**：组连续 vs 空间质量，但它衡量排序质量、分组扁平、没有下界。
  - Rauscher 2025/2026：失真的视觉标示。
- **2.3 Constrained 1-D placement and ordering**
  - Li & Wang 2019（无层次时的最小最大位移，**对应我们的 τ_free**）。
  - IPSep-CoLa（分离约束的二次规划）；OLO（Bar-Joseph）。
  - 地理系统发育图系列、Bulteau 2022、Huson 2026：树约束叶序，但目标是交叉数或位移和。
  - 一维尺度化是 NP-hard（Brusco）。
- **2.4 Faithfulness, trade-offs and guarantees**
  - 变形地图的误差三分法（Nusrat & Kobourov 2016）。
  - 数据–空间网格图（van Beusekom 2023，权衡导航最接近的先例）。
  - 空间有序树图（Wood & Dykes 2008）。
  - 投影失真可视化（Aupetit 2007）。
- **2.5 Merge tree distances**
  - 交错距离（Morozov 2013）；ℓ∞-cophenetic = 带标签交错距离（Munch & Stefanou 2019）；Gasparovic 2024；Yan 2022；ParkView 2025。
  - 论点句：*To our knowledge, interleaving distances have not been used to evaluate linearizations or layouts.*
- **缺口总结**（1 句）：*No prior work bounds the positional distortion forced by hierarchy constraints in 1-D layouts, nor quantifies the position–topology trade-off for merge tree maps.*
- **过渡**：回顾合并树图的共同骨架。

来源：related-work-map 中的 A、B、E、F、G、D 各类。

---

### 3. Background: Merge Tree Maps（约 450 词，0.5 页）

**目的**：给出后续形式化需要的最少概念，并把两个前作放进同一个流程。

- **3.1 Augmented merge trees**
  - join / split tree，叶弧即特征，采用二叉化约定。
  - 符号：f、T_t、叶子 ℓ、LCA、合并值 f(LCA)。
- **3.2 The shared pipeline**：树 → 叶序 → 区间 → 填充 → 按时间堆叠（配小图 Fig. 2 左半）。
  - TMTM：DFS 线性化，宽度 = 样本数（**绝对量**），证明了 Merge Tree Identity。
  - ST-MTM：用 OLO 定叶序，用 stress 定 anchor，宽度 ∝ σ^α 且总和为 K，再做 LCA 填充。
  - 参考锚定变体（合作者 RA-MTM）：加入固定世界参考 q。
  - **说明我们沿用 ST-MTM 的填充方法，不作为贡献。**
- **过渡**：这三种方法都是同一类布局问题的特例。

来源：TMTM §3、ST-MTM §4、`docs/solver.md`。

---

### 4. A Fidelity Model for Merge Tree Maps（约 800 词，1.0 页，含 Fig. 2、Fig. 3）

**目的**：把"好不好"变成可以定义、可以证明的量。

- **4.1 Merge tree maps as hierarchy-constrained interval layouts**
  - 每帧的布局 = (π, u, z)：π 是合法叶序（每个子树的叶子连续），u 是 anchor，z 是区间中心。
  - 约束：宽度 w_i = c·A_i、间距 g、画布 [a, a+L]、anchor 偏心 \|u_i − z_i\| ≤ ρw_i/2。
  - 合法叶序的个数 = ∏ 各内部结点子结点数的阶乘。
- **4.2 Three fidelities**（定义）
  - 拓扑：一维图的带标签合并树与 T 相同。
  - 位置：e_i = u_i − q_i，其中 q_i = φ(R_i)，φ 为参考坐标。
  - 大小：宽度正比于测度，跨帧的比例系数 c 固定。
  - 论点句：*Existing methods fix one fidelity and optimize another without measuring the third.*
- **4.3 Where existing methods sit**（小表或 Fig. 2 右半）
  - TMTM：拓扑 + 绝对大小，位置不控制。
  - ST-MTM：拓扑 + 相对距离，大小为相对量。
  - 参考锚定：拓扑 + 位置（有预算）+ 绝对大小。
- **4.4 Why conflicts are unavoidable**（Fig. 3 三叶例子）
  - 树 ((A,B),C)，参考值 q_A < q_C < q_B：任何保拓扑的布局都必须偏移。
  - 用一句话点出下界的数量级（宽度为零时约为 min(q_B − q_C, q_C − q_A)/2）。❗ 需写成严格表述
- **过渡**：这个偏移最少是多少？

来源：`docs/solver.md` §3–4、`docs/method.md`、`notes/2026-09-26-prototype.md`（三高斯例子）。

---

### 5. Certifying Positional Distortion（约 1,000 词，1.25 页，含 Fig. 4、Algorithm 1）

**目的**：核心技术贡献，给出命题和证明（长证明放补充材料）。

- **5.1 The certificate τ\***
  - 定义：τ\*(T) = min over 合法 (π, u, z) of max_i \|u_i − q_i\|。
  - **命题 1（最优性与可计算性）**：固定 π 时是一个线性规划，因此 τ\* 是在模型约束下的**精确**最小值，而不是启发式估计。❗ 写出证明
- **5.2 Closed form for a fixed leaf order**
  - **命题 2**：固定叶序时，
    τ(π) = max{0, max_{i<j} (q_i − q_j + S_ij − h_i − h_j)/2, max_i (a + D_i − q_i − h_i), max_i (q_i − h_i − (a + L − E_i))}，
    其中 h_i = ρw_i/2，D、E、S 为链上的累积间隔。
  - 证明思路：带盒约束的链式差分约束，最早放置法（与 LP 的一致性已验证到 1e-14，见 `prototypes/relax_hierarchy.py::tau_orders`）。❗ 写出证明
  - 意义：O(n²) 计算一个叶序，可以批量枚举。
- **5.3 Attribution: hierarchy vs. space**
  - τ_free = 去掉连续约束后的同一问题（即 Li & Wang 情形，另加画布和偏心约束）。
  - **命题 3**：τ_free ≤ τ\*；展平任一结点，τ\* 单调不增；全部展平后等于 τ_free。❗ 证明（直接由可行集包含关系得出）
  - 层次代价 H = τ\* − τ_free；空间代价 = τ_free。
  - 论点句：*H is exactly the price of keeping every subtree contiguous.*
- **5.4 Algorithm and complexity**（Algorithm 1）
  - 枚举合法叶序，每个用闭式解；需要时用 QP 在预算内精修（沿用合作者的第二阶段）。
  - 复杂度 O(\|P(T)\|·n²)；ERA5 最多 11 个叶子，可以运行。
  - 老实说明：多项式算法仍是开放问题。
- **5.5 Choosing the reference**（1 段，降级为实现细节）
  - 默认参考方向 = 追踪到的位移的主方向（与坐标系摆放无关）；也支持用户自选参考（径向、焦点）。
  - 统一的画布比例常数；θ = 2% 轴长（唯一的全局常数）。
- **过渡**：知道了界，怎样用它？

来源：Li & Wang 2019、IPSep-CoLa、`docs/solver.md`、`prototypes/general_method.py`、`prototypes/relax_hierarchy.py`。

---

### 6. Navigating the Position–Topology Trade-off（约 900 词，1.1 页，含 Fig. 5）

**目的**：把证书变成可操作的设计。默认诚实披露，可选地做受控放松。

- **6.1 Certificate-driven relaxation**
  - 只在 H > θ 的帧放松。
  - 每次从"能降低 τ\*"的结点中选最弱的合并 \|f(v) − f(parent)\|，把它展平。
  - 直到 H ≤ θ，或者没有结点可以再帮助。
  - 与持久性简化的区别：**不改变数据，只放松布局**。
- **6.2 Measuring topological cost**
  - 定义 d_top = 所有叶对 (i, j) 上 \|m_1D(i, j) − f(LCA_T(i, j))\| 的最大值。
  - **命题 4**：若一维图与 T 具有相同的带标签叶集，则 d_top 等于 ℓ∞-cophenetic 距离，即带标签交错距离（Munch & Stefanou）。❗ 写出证明
  - 已在 ERA5 全部 51 个放松帧验证：没有伪极值（`notes/novelty/2026-09-26-novelty-report-v2.md`）。
- **6.3 Trade-off curve and the user's control**
  - 以单次放松允许的合并改变 κ（占值域的比例）为参数扫描，得到 (d_top, 位置误差) 曲线。
  - 默认 κ = 0（保拓扑 + 披露偏差）。
  - κ 作为用户显式控制的滑块，**不是按数据集调的参数**。❗ 改为按累积量限制
- **6.4 Visual encoding**
  - 证书强度带（每列画 τ\* 和 H）。
  - 被放松的合并在断开处加标记（借鉴 ParkView 的交错可视化）。
  - **不画**逐特征刻度（在 ERA5 上不可读，这是负面结果）。❗ 需设计并实现
- **过渡**：这些工具在真实数据上揭示了什么？

来源：Munch & Stefanou 2019、Morozov 2013、ParkView 2025、van Beusekom 2023、`notes/2026-09-26-local-relaxation.md`、`notes/2026-09-26-conflict-strategies.md`。

---

### 7. Evaluation（约 1,900 词，2.4 页，含 Fig. 6–8、Tab. 1–3）

**目的**：按研究问题回答，每个结论对应一张图或表。

- **7.1 Setup**（Tab. 1）
  - 数据集：Gaussian 三斑（复刻 ST-MTM 的动机例子）、Ring（TMTM / Franke 的合成数据）、ERA5 MSLP（1999-11-17 至 2000-01-14，118 帧，12 小时间隔）。❗ 考虑加一个真实数据集（Wildfires 或 TMTM 的 Storms 全月）
  - 预处理沿用合作者的协议；所有常数由统一规则决定。
  - 基线：TMTM、ST-MTM、固定 X 轴的参考锚定图。
- **7.2 RQ1 — How pervasive are hierarchy-induced conflicts?**（Fig. 6）
  - 逐帧的 H 与 τ_free。
  - ERA5：68/118 帧 H > θ，最大 H 为轴长的 31%。Ring：21/40 帧。
  - **稳健性**：θ ∈ {1, 2, 5}%、参考方向（自动 / X / Y / 8 个角度）、时间步（6 h / 12 h）、简化阈值。❗ 尚未做
  - 论点句：*Conflicts are the norm, not the exception, on real weather data.*
- **7.3 RQ2 — What does it cost to reduce positional error?**（Fig. 7，Tab. 2）
  - 三个数据集的权衡曲线。
  - ERA5：κ = 2% 时平均误差 −9%；κ = 20% 时 −42%（约 28 hPa）；不设限时 −60%（最大 58 hPa，10% 的叶对受影响）。
  - Ring：κ = 2% 时 −18%（冲突来自弱合并）。
  - Gaussian：κ < 20% 时无收益（冲突来自强脊）。
  - 归因：冲突来自持久性高的鞍点。
- **7.4 RQ3 — What does the certificate reveal about existing maps?**（Fig. 8）
  - 同一段 ERA5 上的 TMTM / ST-MTM / 固定 X / 我们的方法，每张图上方都叠加证书强度带。
  - TMTM 的宽度也是绝对量（样本数），因此可以在它自己的宽度模型下计算 τ\*。❗ 待做
  - 对前两者经仿射校准后测位置误差，与 τ\* 对照，说明"它们离可达下界有多远"（沿用合作者的 affine readout）。❗ 待做
  - 老实说明：ST-MTM 的相对几何（SNS）更好。
- **7.5 Case study: December 1999 storms**（Fig. 8 局部放大或单独一图）
  - Lothar（12/26）、Martin（12/27）、Anatol（12/03）：证书在哪些时段报警；放松改变了哪些合并；气象上是否合理。
  - 谨慎表述：叶极小值不等同于经过验证的气旋中心。❗ 待做
- **7.6 Runtime**（Tab. 3）
  - 每帧的合法叶序数、闭式解与 LP 的耗时、整体运行时间（ERA5 当前约 10 秒）。
- **过渡**：这些结果对整个方法族意味着什么？

来源：`notes/2026-09-26-general-method.md`、`notes/2026-09-26-local-relaxation.md`、`prototypes/output/*.json`、`results/era5/`（合作者的基线协议）。

---

### 8. Discussion（约 450 词，0.5 页）

- **8.1 Implications for the method family**
  - 保合并树的一维图不能同时忠实于位置，所以默认应保拓扑并**披露**偏差；
  - 需要位置时，应显式放松，并展示代价。
  - 设计建议 3 条。
- **8.2 Limitations**
  - 枚举合法叶序，适合小树；
  - 贪心放松不保证到达 Pareto 前沿；
  - 自动径向中心不可靠（跟随追踪伪影），自动方向只捕获部分运动；
  - 跨帧匹配只是支撑重叠；
  - 12 小时间隔；
  - 没有用户实验；
  - θ 是一个全局常数。
- **8.3 Future work**
  - 多项式时间的树上动态规划；
  - 精确的多目标放松；
  - 用户实验；
  - 三维数据与多变量场。

### 9. Conclusion（约 200 词，0.25 页）

用一句话回答 RQ，重复最重要的数字，再用一句话说明意义。

---

## D. 图表计划

| 编号 | 内容 | 位置 | 数据来源 | 状态 |
|---|---|---|---|---|
| Fig. 1 | Teaser：同一段 ERA5，(a) TMTM 或 ST-MTM（没有任何失真提示），(b) 我们的图 + 证书强度带 + 被放松合并的标记，(c) 小权衡曲线 | §1 | era5 relax / general | ❗ 需重新设计并出图 |
| Fig. 2 | 左：共同流程；右：三种忠实度 × 三种方法的定位 | §3–4 | 示意 | ❗ 画图（`/aris:figure-spec`） |
| Fig. 3 | 三叶冲突例子，以及 τ\* 的几何意义 | §4.4 | 示意 | ❗ |
| Fig. 4 | 证书分解示意：τ_free 与 H 的柱状对比，以及一个真实帧 | §5 | general_metrics | ❗ |
| Fig. 5 | 展平一个结点：树的变化、一维列的变化、合并层级改变 = 交错距离 | §6 | 示意 + 真实帧 | ❗ |
| Fig. 6 | RQ1：ERA5 逐帧的 H / τ_free 时间线 + 稳健性热图（θ × 方向） | §7.2 | 待跑 | ❗ |
| Fig. 7 | RQ2：三个数据集的权衡曲线（已有原型图 `relax_tradeoff.png`） | §7.3 | relax_tradeoff.json | 原型已有，需美化 |
| Fig. 8 | RQ3 + 案例：四种方法的 ERA5 图 + 证书强度带，放大 12 月 24–28 日 | §7.4–7.5 | 待跑 | ❗ |
| Tab. 1 | 数据集统计（帧数、叶子数范围、合法叶序数、冲突帧占比） | §7.1 | protocol + metrics | 部分已有 |
| Tab. 2 | 主结果：各 κ 下的位置误差与 d_top（三个数据集） | §7.3 | relax_tradeoff.json | 已有 |
| Tab. 3 | 运行时间 | §7.6 | 待测 | ❗ |
| Alg. 1 | 证书 + 放松 | §5.4 / §6.1 | 代码 | 需写伪代码 |

## E. 证据映射（论点 ← 证据）

| 论点 | 所在节 | 证据 | 文件 | 状态 |
|---|---|---|---|---|
| 现有方法不报告失真 | §1.2 | TMTM / ST-MTM 原文（ST-MTM §7.1–7.2 定性讨论） | references/pdf | ✅ |
| 没有人给出层次约束下的界或权衡曲线 | §2 | 42 篇文献与查新 v2 | related-work-map、novelty-report-v2 | ✅（Codex 复核待补） |
| τ\* 是精确最小值 | §5.1 | LP 最优性（命题 1） | error_budget.py | ❗ 证明待写 |
| 固定叶序的闭式解 | §5.2 | 与 LP 一致到 2×10⁻¹⁴ | relax_hierarchy.py | ✅ 数值；❗ 证明待写 |
| H 是保连续的代价 | §5.3 | 可行集包含关系 | — | ❗ 证明待写 |
| d_top = 带标签交错距离 | §6.2 | Munch & Stefanou + 51 帧没有伪极值 | novelty-report-v2 | ✅ 数值；❗ 证明待写 |
| 冲突普遍（58%，最大 31%） | §7.2 | general_metrics.json | notes/2026-09-26-general-method.md | ✅ 原型；❗ 稳健性与 CDS 重跑 |
| 放松收益与代价（−9% / −42% / −60%；13 hPa，最大 58 hPa） | §7.3 | relax_tradeoff.json | notes/2026-09-26-local-relaxation.md | ✅ 原型；❗ 累积上限后重跑 |
| Ring 冲突便宜，Gaussian 冲突强 | §7.3 | 同上 | 同上 | ✅ |
| 自动方向优于固定 X（0.74 vs 0.69） | §5.5 | general_metrics.json | general-method | ✅（降为次要） |
| 未放松帧的拓扑完全精确 | §6 / §7 | 逐帧签名检查、A 的合并误差为 0 | relax_metrics.json | ✅ |
| 逐特征标注不可读；稳定性优先不能推广 | §6.4 / §8 | 负面结果 | conflict-strategies、general-method | ✅（一句话即可） |
| 与 TMTM / ST-MTM 的对照 | §7.4 | 仿射读出 + τ\* | results/era5（合作者） | ❗ 待做 |

## F. 尚缺清单（按优先级）

**P0：影响能否投稿**
1. **与合作者对齐定位与署名**（第一周）。
2. 命题 1–4 的严格表述与证明（正文给要点，完整证明放补充材料）。
3. 稳健性扫描：θ × 参考方向 × 时间步 × 简化阈值，支撑"普遍存在"。
4. 用 CDS 原始 ERA5 文件重跑全部数字。
5. RQ3：在 TMTM 自己的宽度模型下算 τ\*，并对 TMTM / ST-MTM 做仿射读出。

**P1：影响质量**
6. 放松上限改为按累积量限制；重画权衡曲线。
7. 证书强度带 + 放松标记的视觉编码；Fig. 1 与 Fig. 8。
8. ERA5 案例（1999 年 12 月的风暴）。
9. 把原型整理进 `src/`，加单元测试（审稿人可能要求复现）。

**P2：加分项**
10. 第二个真实数据集。
11. 1–2 位气象专家的简短定性反馈。
12. Codex 交叉审稿补跑；模拟审稿（`/ars-reviewer`）。

## G. 写作顺序与 6 周排期

| 周 | 日期 | 写作 | 实验 / 代码 |
|---|---|---|---|
| W1 | 9/27–10/4 | 与合作者确认大纲；写 §3、§4 初稿（最稳定的部分） | 累积上限；稳健性扫描脚本；申请 CDS 文件 |
| W2 | 10/5–10/11 | §5（命题与证明）、§6 | 原型进入 `src/` + 测试；RQ3 基线 |
| W3 | 10/12–10/18 | §7 结果（边出图边写） | 全部实验定稿；Fig. 1–8 |
| W4 | 10/19–10/25 | §2、§8，然后 §1（最后写引言），摘要初稿 | 补漏实验 |
| W5 | 10/26–11/2 | 全文模拟审稿（`/ars-reviewer`）→ 修改；**11/2 提交摘要** | 运行时间表 |
| W6 | 11/3–11/9 | 润色、引用核查（`/aris:citation-audit`）、匿名化、补充材料（证明、代码说明）；**11/9 提交** | 冻结代码 |

写作原则：
- 每节开头一句话说明本节回答什么；
- 每个论点都能在 §E 里找到证据；
- 负面结果各用一句话写成边界。

## H. 页面与字数汇总

| 节 | 页 | 词 |
|---|---|---|
| Abstract | – | 180 |
| 1 Introduction | 1.0 | 950 |
| 2 Related Work | 0.75 | 700 |
| 3 Background | 0.5 | 450 |
| 4 Fidelity Model | 1.0 | 800 |
| 5 Certificate | 1.25 | 1,000 |
| 6 Trade-off | 1.1 | 900 |
| 7 Evaluation | 2.4 | 1,900 |
| 8 Discussion | 0.5 | 450 |
| 9 Conclusion | 0.25 | 200 |
| **合计** | **8.75 + 余量** | **约 7,500（含图注）** |

说明：正文约 6,300 词，加上图注和算法框约 1,200 词。如果超页，优先压缩 §2 和 §3。

---

## I. 需要你确认的事项（outline 模式要求在进入下一阶段前确认）

1. 配置记录中标 ❓ 的三项：模板、是否双盲、署名。
2. 结构是否认可：特别是 §4 模型、§5 证书、§6 权衡三节分开写；自动方向降为 §5.5 的实现细节。
3. 是否要增加第二个真实数据集（会影响 W2–W3 的工作量）。
