# 扩大 ERA5 区域 + 海岸线：进度与恢复说明（2026-09-27 开始）

**背景**：旧协议在固定的欧洲区域（30–75°N、30°W–40°E，49×49 网格）上提取合并树。区域边界会截出大量"边界极小值"：ERA5 中 62% 的叶子在边界上，68 个冲突帧里有 63 个的见证涉及边界叶子（见 `prototypes/boundary.py` 与 `output/boundary.json`）。用户选择**方案 B：扩大区域**。

## 方法（已定）

1. 从同一个 ARCO-ERA5 镜像下载更大的区域：纬度 20–90°N，经度 50°W–60°E，每 12 小时一帧，两个冬季各一份。
2. 目标网格不变（49×49，同样的投影与格距），四周加缓冲格：西、东、南各 10 格（约 1000 km），北边 3 格（受极点限制）。在扩大后的网格上做 250 km 平滑，边界处的平滑因此用到真实数据。
3. **真实极小值**：在扩大网格上检测严格局部极小值（8 邻域，不在扩大网格边界上），只保留落在目标网格内的那些。
4. 裁剪回目标网格后，用 priority-flood（加 ε）把**不含真实极小值**的洼地填到溢出点（即 minima imposition）。这样合并树的叶子只剩真实极小值，边界截出的假极小值消失；其余流程（`experiments/era5.py::scene_from_fields`）保持不变。
5. 旧的裁剪版数据保留为 `era5_crop` / `era5_2014_crop`，作为敏感性对照。

## 步骤与状态（每完成一步就改状态并 commit）

| 步 | 内容 | 状态 | 产物 / 恢复方法 |
|---|---|---|---|
| S1 | 下载 Natural Earth 110m 海岸线 → `data/geo/ne_110m_coastline.geojson`（data/ 不入库），重画首页图与案例图 | ✅（海岸线版本已放入论文；数据仍是旧的裁剪版，窗口决定后在 S6 中重画） | `prototypes/fig_teaser.py`、`fig_witness.py` 会自动读取这个文件 |
| S2 | 下载扩大区域的 ERA5：`prototypes/era5_arco_expanded.py`（20–90°N，50°W–60°E，281×441）→ `data/real/ERA5_MSLP/*_12h_arco_expanded.nc`（1999：26.5 MB，118 帧；2014：124 帧） | ✅ | 命令写在脚本的 docstring 里；文件已存在时脚本自动跳过 |
| S3 | 新加载器 `prototypes/era5_expanded.py`：极小值检测 + 洼地填充 + 统计边界叶子占比 | ✅ | 自检通过：坐标与原协议完全一致；距边界 12 格以内的平滑场差为 0.0 |
| S4 | 在 `replicate.LOADERS` 中把 era5 / era5_2014 切换到扩大版（旧版改名为 *_crop），并删除 `output/attainable_era5*_cache.pkl` | ✅ | 见文末"决定"一节 |
| S5 | **运行 `bash prototypes/run_expanded.sh`（可断点续跑）**。重跑实验（每个脚本单独运行，避免超时被杀）：`replicate.py era5 era5_2014` → `robustness.py` → `pointcert.py` → `persistence.py` → `boundary.py` → `witness_stats.py` → `filling.py` → `frontier.py` → `attainable.py era5`、`attainable.py era5_2014`（先加 `--cache-only`）→ `eval_v2.py era5`、`eval_v2.py era5_2014` → `stmtm_grid.py era5 era5_2014` → `sensitivity.py`（ERA5 变体已改用扩大版） | ⏳ | 每个脚本写自己的 JSON；看 JSON 修改时间判断是否已完成 |
| S6 ✅ | 重画所有 ERA5 相关的图：`fig_teaser.py`、`fig_pipeline.py`、`fig_rq1.py`、`attainable.py plot`、`fig_witness.py`（案例时刻需重新挑选：见证三元组在内部、冲突清楚） | ⏳ | 复制到 `paper/pacificvis2027/figures/` |
| S7 | 用 `paper_numbers.py` 更新正文所有 ERA5 数字，写清楚新协议；更新中文翻译与大白话版 | ⏳ | |
| S8 | 打包 Overleaf zip，commit + push，向用户汇报 | ⏳ | |

## 已知风险

- 去掉边界极小值后，每帧叶子数会变少，ERA5 的冲突比例可能明显下降（旧数据只保留内部叶子时降到 2–5%）。结果如何都如实报告；必要时讨论是否换更大的目标区域。
- 运行超过约 10 分钟的后台任务曾被系统杀掉（exit 137）。所以要逐个数据集单独运行，精确曲线先用 `--cache-only`。

## S3 结果（2026-09-27）：结论改变，需要决策

原协议窗口（30–75°N、30°W–40°E）只保留真实极小值后：

| 数据 | 叶子/帧（旧 → 新） | 裁剪后的局部极小值/帧 | 冲突帧比例（旧 → 新） | ≥3 叶子的帧 |
|---|---|---|---|---|
| ERA5 1999 | 4.93 → 2.54 | 5.55 | 57.6% → **13.6%**（16/118） | 56 |
| ERA5 2014 | 4.18 → 2.20 | 4.87 | 59.7% → **2.4%**（3/124） | 39 |

试验：更大的目标窗口 25–80°N、40°W–50°E（仍是 49×49 网格，格距约 124 km，缓冲 5 格，同样只保留真实极小值）：

| 数据 | 叶子/帧 | 冲突帧比例 |
|---|---|---|
| ERA5 1999 | 3.43 | **33.9%**（40/118） |
| ERA5 2014 | 3.32 | **24.2%**（30/124） |

解读：
- 旧的 58–60% 冲突比例主要来自边界截断产生的假极小值。
- 冲突的多少取决于窗口里真实低压的数量：至少要有 3 个叶子，还要彼此交错。
- 这对论文叙事是实质性的变化，用户需要选择（见下）。探测脚本：用 `era5_expanded.loader(season, name, window=..., buf=...)` 调用 `general_method` 的冲突判定。

待用户决定：
- **A**：保持原窗口 + 真实极小值作为主结果，ERA5 冲突 14% / 2%；论文主证据转向 wildfire（63%）与合成数据，ERA5 作为"冲突罕见时方法不添乱"的对照；旧的裁剪结果放进附录作为边界效应的示例。
- **B**：预先声明一个更大的窗口（例如 25–80°N、40°W–50°E，或下载更大范围做北大西洋-欧亚扇区）+ 真实极小值：冲突 34% / 24%。要说明窗口的选取准则，避免"看结果调窗口"的质疑。
- 无论选 A 还是 B，"边界极值会制造虚假冲突"本身都是可以写进论文的发现：它说明要先对裁剪域做 minima imposition。

## 决定（2026-09-27，用户选择）：更大窗口 + 真实极小值作为主设定

- 主窗口为 25–80°N、40°W–50°E，49×49 网格，缓冲 5 格。准则是：在已下载的数据范围内取最大的窗口，南、西、东三侧各留 ≥5 格（约 620 km，即 2.5σ）的平滑缓冲；北侧受极点限制。见 `era5_expanded.MAIN_WINDOW`。
- `gm.era5()` 和 `dx.era5_2014()` 已切换到新设定。旧设定改名为 `gm.era5_crop()` 和 `dx.era5_2014_crop()`，并作为敏感性变体进入 `sensitivity.py`（放附录）。
- 旧结果已存档：git tag `era5-crop-v1`，以及 `prototypes/output/era5_crop_v1/`（含旧的 exact-frontier 缓存）。
- S4 ✅。S5 用 `bash prototypes/run_expanded.sh` 运行，可断点续跑（完成标记在 `prototypes/output/.done_expanded/`，日志在 `prototypes/output/run_expanded.log`）。中断后重新执行同一命令即可。
- 首页图和案例图的 2-D 快照现在显示平滑后的真实场（`fields_smooth`），不是填平后的场；地理框取自 `sc['window']`。

## S5/S6 进度（2026-09-27 14:40）

- S5：除 `sensitivity` 外全部完成（结果 JSON 已 commit）。`era5_s150` 的 ST-MTM SLSQP 失败，已改为记录错误、不再中断；`era5_2014_s150` 超过 12 叶（第 83 帧 14 叶），改用 σ=200。数字汇总见 `prototypes/output/paper_numbers_expanded.txt`（`paper_numbers.py` 的输出）。
- S6：图全部重画并复制进论文：
  - 首页图：快照改为 SN=[5,26,48,62,108]，包含冲突时刻；
  - 流程图：改用第 62 帧（1999-12-18，5 个低压，H=22%，压平 2 个合并，δ*=5.3 hPa，LCA 为 10.7）；
  - 案例图：仍用第 48 帧（1999-12-11；两个深低压 985/988 hPa 同属一棵子树，1007 hPa 的亚得里亚低压位于两者之间；见证 7.8%，τ*=H=8.4%，该帧 δ*=12.6 hPa，窗口内最大 21 hPa，松弛后误差 0.8%）；
  - RQ1 图、精确前沿图同步更新。
