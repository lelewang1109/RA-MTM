# RA-MTM 实验结果

只从这份索引进入当前结果。质心消融与所有baseline都在同一协议下重新运行。

| 要看什么 | Ring | ERA5 |
|---|---|---|
| 主指标（极值真值） | [metrics.csv](ring/metrics.csv) | [metrics.csv](era5/metrics.csv) |
| 两套真值对照 | [metrics_by_target.csv](ring/metrics_by_target.csv) | [metrics_by_target.csv](era5/metrics_by_target.csv) |
| 时空标量图 | [comparison_maps.png](ring/comparison_maps.png) | [comparison_maps.png](era5/comparison_maps.png) |
| 目标与优化anchor | [longest_tracks.png](ring/longest_tracks.png) | [longest_tracks.png](era5/longest_tracks.png) |
| 协议与来源 | [protocol.json](ring/protocol.json) | [protocol.json](era5/protocol.json) |
| 校验 | [validation.json](ring/validation.json) | [validation.json](era5/validation.json) |

同名 PDF/SVG 可用于论文。`X-only RA-MTM_records.json` 同时是Dual-X；`Dual-Y_records.json`是第二轴；
`Centroid-X/Y_records.json`是消融，不能当主线。全部记录包含leaf order、q、anchor、width、tau与预算。
`rendered_metrics.csv`是像素化读出误差；`affine_metrics.csv`是另一种单视图校准；
`tracking_robustness.csv`包含低重叠/边界对结果的影响；`runtime_repeats.csv`保存全部重复。

总解释：[当前实验报告](../docs/results.md)。
`manifest.json`绑定实际执行源码及当前证据，本地 `execution.log` 保留运行警告（不上传）。
当前目录只保留 Ring 与 ERA5 两套结果。
