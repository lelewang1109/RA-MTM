# 结果导航

**当前只先看 `xy/`，总报告为 [当前实验报告](../docs/EXPERIMENT_REPORT.md)。**

- `xy/{ring,era5}/metrics.csv`：当前六种方法比较。
- `xy/{ring,era5}/metrics_by_target.csv`：极值/质心两套真值，不混用。
- `xy/{ring,era5}/comparison_maps.*`：无身份散点的 scalar maps。
- `xy/{ring,era5}/longest_tracks.*`：目标点 vs anchor，明确 track ID。
- `xy/{ring,era5}/protocol.json`、`*_records.json`、`validation.json`：来源、协议、证书。
- `xy/manifest.json`：当前来源及结果哈希，用 `experiments/xy/verify.py --verify` 检查。

以下全部是保留的历史/补充证据，不是另一套“当前主结果”：

| 目录 | 角色 |
|---|---|
| `dual_reference/` | 质心参考25序列机制证据，包含不利结果 |
| `dual_public/` | 上轮公共数据质心主表与参考点诊断 |
| `main/`, `supplementary/` | 历史单轴表、图、所有重复与参数实验 |
| `ablation/`, `sensitivity/`, `validity/`, `auxiliary/` | 历史单轴配套证据 |
| `exploratory/jolt_mtm/` | 已停止探索，未通过预设门槛的结果仍保留 |

历史 manifest 是原运行的来源记录，不能用当前修改后的源码重新解释成已重跑。
重复 Ring 单帧导出已移出仓库；原输入来源和完整数值实验仍在。
大数组 `.npz` 可从脚本再生，不纳入 Git。
