# 数据准备

Ring 输入由 `experiments/ring/dataset.py` 和随附的作者参数自动生成，不需要外部下载。

ERA5 输入不随仓库分发。请将已有数据放置为：

```text
data/real/ERA5_MSLP/ERA5_MSLP_19991117_20000114.nc
```

文件应与 `results/era5/protocol.json` 的源数据 SHA-256、网格和时间范围一致。使用变量 `msl`（Pa）、`valid_time`、`latitude`、`longitude`；代码检查小时采样连续性、缺失值和单位。它是再分析场，不是独立气旋轨迹真值。

本机 `data/real` 可以链接到共享输入目录；该链接和所有原始数据均由 `.gitignore` 排除。无需 ERA5 数据即可运行 Ring 或检查已发布文件哈希。
