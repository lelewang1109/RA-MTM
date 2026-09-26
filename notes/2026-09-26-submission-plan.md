# 投稿计划：PacificVis 2027 会议轨道（2026-09-26 决定）

- 摘要：**11/2**；全文：**11/9**（投稿前在官网确认时区）
- 正文 9 页 + 2 页参考文献；IEEE VGTC 模板
- 定位与主张边界以 `notes/review/2026-09-26-research-review.md` 为准。
- 核心三条贡献：
  1. 位置偏差下界 + 精确算法；
  2. 与画法无关的拓扑代价定理 + 位置–拓扑下界曲线；
  3. 跨领域刻画 + 聚类像素图的设计用途。
- **不做用户实验**：所有涉及"读者"的说法一律写成"几何代理下的符号不一致"。

## 状态

| 项 | 状态 |
|---|---|
| 理论与证明（中 / 英） | ✅ `paper/proofs_zh.md`、`paper/proofs.tex` |
| 中文正文 v0.3 | ✅ `paper/draft_zh.md` |
| 英文正文初稿 | ✅ 初稿 `paper/main.tex`（本次） |
| 全部实验可复现 | ✅ `prototypes/replicate.py`、`frontier.py`、`generality.py`、`robustness.py`、`paper_numbers.py` |

## 剩余任务（按优先级）

| 周 | 任务 | 说明 |
|---|---|---|
| W1（9/27–10/4） | **与合作者对齐**定位与署名；向合作者要 CDS 原始 ERA5；补跑第 2 轮 GPT 评审打分 | 评审简报：`notes/review/RESEARCH_REVIEW_ROUND_2.md`；Codex 的 MCP 桥接失效时直接用 `codex exec` |
| W2（10/5–10/11） | 在基线各自的宽度模型下计算下界（TMTM 用样本数，ST-MTM 用拟合宽度）；小规模最优放松对比；τ_free 改为精确求解 | 评审第 2 周的建议 |
| W3（10/12–10/18） | 下界的显示设计：每列的下界条带 + 放松标记；teaser 图 1；图 2（流程）、图 5（展平示意）；在树状图演示中标出见证三元组 | 用 `/aris:figure-spec` 或 matplotlib |
| W4（10/19–10/25） | 用 CDS 原始数据重跑全部数字；英文稿定稿；时间间隔 6 h 的稳健性（需要逐小时数据） | 运行 `paper_numbers.py` 核对每个数字 |
| W5（10/26–11/2） | `/ars-reviewer` 模拟审稿 → 修改；**11/2 提交摘要** | |
| W6（11/3–11/9） | `/aris:citation-audit` 核查引用；匿名化（不附 GitHub 链接）；补充材料（完整证明、代码说明）；**11/9 提交** | |
