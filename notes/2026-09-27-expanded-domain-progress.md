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
| S1 | 下载 Natural Earth 110m 海岸线 → `data/geo/ne_110m_coastline.geojson`（data/ 不入库），重画首页图与案例图 | ⏳ | `prototypes/fig_teaser.py`、`fig_witness.py` 会自动读取这个文件 |
| S2 | 下载扩大区域的 ERA5：`prototypes/era5_arco.py`（新增 bbox 参数）→ `data/real/ERA5_MSLP/*_expanded.nc` | ⏳ | 文件存在即可跳过 |
| S3 | 新加载器 `prototypes/era5_expanded.py`：极小值检测 + 洼地填充 + 统计边界叶子占比 | ⏳ | 运行 `.venv/bin/python prototypes/era5_expanded.py` 自检 |
| S4 | 在 `replicate.LOADERS` 中把 era5 / era5_2014 切换到扩大版（旧版改名为 *_crop），并删除 `output/attainable_era5*_cache.pkl` | ⏳ | |
| S5 | 重跑实验（每个脚本单独运行，避免超时被杀）：`replicate.py era5 era5_2014` → `robustness.py` → `pointcert.py` → `persistence.py` → `boundary.py` → `witness_stats.py` → `filling.py` → `frontier.py` → `attainable.py era5`、`attainable.py era5_2014`（先加 `--cache-only`）→ `eval_v2.py era5`、`eval_v2.py era5_2014` → `stmtm_grid.py era5 era5_2014` → `sensitivity.py`（ERA5 变体已改用扩大版） | ⏳ | 每个脚本写自己的 JSON；看 JSON 修改时间判断是否已完成 |
| S6 | 重画所有 ERA5 相关的图：`fig_teaser.py`、`fig_pipeline.py`、`fig_rq1.py`、`attainable.py plot`、`fig_witness.py`（案例时刻需重新挑选：见证三元组在内部、冲突清楚） | ⏳ | 复制到 `paper/pacificvis2027/figures/` |
| S7 | 用 `paper_numbers.py` 更新正文所有 ERA5 数字，写清楚新协议；更新中文翻译与大白话版 | ⏳ | |
| S8 | 打包 Overleaf zip，commit + push，向用户汇报 | ⏳ | |

## 已知风险

- 去掉边界极小值后，每帧叶子数会变少，ERA5 的冲突比例可能明显下降（旧数据只保留内部叶子时降到 2–5%）。结果如何都如实报告；必要时讨论是否换更大的目标区域。
- 运行超过约 10 分钟的后台任务曾被系统杀掉（exit 137）。所以要逐个数据集单独运行，精确曲线先用 `--cache-only`。
