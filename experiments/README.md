# 实验入口

**默认只运行：** `.venv/bin/python scripts/run_all.py`。

| 路径 | 用途 |
|---|---|
| `xy/` | 当前极值参考 XY 主线；Ring / ERA5；六种方法与完整审计 |
| `dual_reference/public_data.py` | 主线与历史质心版共用驱动；不复制 solver |
| `dual_reference/` 其余文件 | 质心机制实验、25序列与历史诊断，作为补充证据 |
| `ring/` | 原作者生成器、数据来源、旧单轴适配器 |
| `real_era5/` | 共享数据提取/匹配/baseline驱动，以及旧单轴实验 |
| `synthetic_1d/`, `gaussian_2d/` | 原 canonical 输入及 baseline 适配器，兼容保留 |
| `history/jolt_mtm/` | 已停止的 JOLT 探索，不是 XY 的组成部分 |

旧单轴入口：`scripts/run_legacy.py`；不要把其结果当作当前主线。
共享旧目录中的函数是代码复用，不表示这些目录下的每个实验都是当前主线。
