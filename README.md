# XY RA-MTM

**固定世界参考下的双轴 Merge Tree Maps。** 当前主线使用同一个 topological feature 的叶极值点作为 X/Y 参考，输出时间对齐的两个一维标量图，并组合其 anchor 估计二维位置与运动。保持 merge-tree 层次及固定绝对宽度；不可兼容之处用 tau、error budget 和 geometry error 报告。

## 只从这三个入口开始

1. [方法流程](docs/XY_METHOD.md)：坐标原点、极值参考、质心几何、LP/QP、渲染、身份配对与评价。
2. [当前实验报告](docs/EXPERIMENT_REPORT.md)：Ring / ERA5 所有 baseline、主线与质心消融结果。
3. [文件与清理索引](docs/PROJECT_STRUCTURE.md)：哪些是当前代码，哪些只是历史证据。

## 当前方法定义

在固定世界坐标中，R_i 为叶极值点，C_i 为叶支撑域质心：

```
q_i^X = (1,0)ᵀ R_i         q_i^Y = (0,1)ᵀ R_i
geometry distance = ||C_i-C_j||₂
absolute interval width = c A_i
reconstructed reference position = (anchor_i^X, anchor_i^Y)
```

**质心不是峰/谷，原点不是参考点，优化 anchor 也不保证等于参考点。**
Ring 支撑域质心起初靠近域中心，叶峰才位于左下方；主线明确采用叶极值位置。
质心参考保留为消融，历史低层 API 默认行为不变。
左下原点与世界尺度跨时间固定，绝不逐帧居中或缩放。

主图只有标量背景；独立轨迹图标注 track ID、目标位置和优化 anchor。
ERA5 红蓝表示气压，沿用固定 pressure_soft 颜色卡，不表示 feature 身份。

## 运行

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python scripts/run_all.py --dataset ring
# 本地存在 ERA5 数据时运行两套完整实验
.venv/bin/python scripts/run_all.py --dataset both
# 不重跑，只验证当前发布文件的内容哈希
.venv/bin/python experiments/xy/verify.py --verify
```

ERA5 输入：`data/real/ERA5_MSLP/ERA5_MSLP_19991117_20000114.nc`。
每套比较包含 TMTM、ST-MTM、X-only extremum RA、Dual extremum RA、X-only centroid RA、Dual centroid RA。
固定参数，三次循环顺序重跑；不修改 baseline 算法或为了指标选择不利参数。
结果只写入 `results/xy/`，不会清空其他实验。

```python
from ramtm.reference_points import reference_points_from_frames
from ramtm import Parameters, solve_dual_reference_sequence

# frames / leaf_ids / track_ids 必须按同一 feature 行顺序组织。
landmarks = reference_points_from_frames(frames, leaf_ids, kind="extremum")
dual = solve_dual_reference_sequence(
    centers, measures, hierarchies, Parameters(),
    feature_ids=track_ids, reference_points=landmarks,
)
positions = dual["positions"]
```

参数中的画布、面积到宽度比例与坐标单位须由具体数据协议固定，示例默认值不是通用数据预设。
任意固定参考方向仍使用 `project_reference` / `solve_sequence`，有限非零方向会先归一化。

## 当前与历史

| 目录 | 角色 |
|---|---|
| `src/ramtm/` | 共用算法、渲染、评价；`baselines/` 原样保留 |
| `experiments/xy/` | 当前主线入口与审计 |
| `results/xy/` | **当前主结果、图、协议、完整证书** |
| `experiments/dual_reference/` | 共用公共数据驱动，以及保留的质心机制/消融协议 |
| `results/dual_reference/` | 25 个质心机制与 canonical 序列，历史定义不更换 |
| `results/dual_public/` | 上一轮公共数据质心协议及 Ring 参考点诊断 |
| `results/{main,supplementary,ablation,sensitivity,validity,auxiliary}/` | 历史单轴证据，保留路径以维持可追溯性 |
| `experiments/history/`、`docs/history/` | 已停止的探索分支及旧报告 |

历史证据不等于当前方法结果。旧 manifest 保留原运行来源，不在改源码后重新贴上“通过”标签。
旧机制可用 `scripts/run_all.py --suite mechanisms` 重跑；旧单轴全套需显式运行 `scripts/run_legacy.py`。
当前 manifest 仅覆盖当前 XY 包。

## 结论边界

两个一维视图互补，不能无损恢复二维 scalar field 或 feature 内部形状。
极值位置也不等于 Ring 环中心或经过气象验证的气旋中心；匹配与采样跳变会影响运动评价。
ST-MTM 仍可能更好地保持相对几何；主线没有“所有指标胜出”的结论。
目前仅在小树上枚举合法叶序，未解决大树可扩展性。
