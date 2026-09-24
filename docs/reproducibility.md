# 从输入到可验证结果

## 1. 数据

Ring 由 `experiments/ring/dataset.py::generate` 从随附作者生成器参数产生 40×14×14 序列，不需要 Inviwo。来源、上游提交和 SHA-256 随每套结果的 `protocol.json` 保存。

ERA5 需要用户自行提供原始文件：`data/real/ERA5_MSLP/ERA5_MSLP_19991117_20000114.nc`。输入应与 `results/era5/protocol.json` 中的源数据哈希、时间范围、变量和网格一致。处理代码检查小时序列连续性、Pa 单位、有限值，不静默补缺。原始数据不随仓库分发；本机的 `data/real` 可为工作区共享数据的链接。

## 2. 共享预处理

`experiments/era5.py` 提供字段预处理、增广合并树、叶支撑域、面积、质心、跨帧重叠身份匹配、基线及序列化工具。Ring 使用 split tree，ERA5 使用 join tree。协议中保存共享输入，避免各方法使用不同特征。

## 3. 参考点与双轴求解

`src/ramtm/reference_points.py` 明确区分叶极值与支撑质心，并检查 X/Y 配对身份。

`src/ramtm/error_budget.py` 枚举保持子树连续性的合法叶序；对每个轴先求最小参考误差 LP，再在 tau+Delta 预算内求 QP；按参考、几何、运动和偏心目标选布局。保留求解证书及误差界。

`src/ramtm/reference_anchored.py` 在固定世界尺度下离散化区间与 anchor，调用既有层次填充；`src/ramtm/dual_evaluation.py` 评价二维位置与运动。

## 4. 实验与输出

`scripts/run_experiments.py --dataset ring|era5|both` 先运行现有单元测试，再调用 `experiments/run.py` 和 `scripts/verify_results.py`。共享驱动为 `experiments/public.py`，包括三次顺序重复、所有基线和质心消融；没有修改原实验参数。

每个数据集输出 `results/<dataset>/`：

- `protocol.json`、`shared_features.json`：数据来源、参数、共享特征、轨迹和参考点。
- `*_records.json`：各方法逐帧顺序、位置、宽度及求解证书；X-only 的 X 结果同时用于双轴方法。
- `metrics*.csv`、`affine_metrics.csv`、`rendered_metrics.csv`、`tracking_robustness.csv`：完整指标及敏感性。
- `runtime_repeats.csv`：三次运行时间。
- `comparison_maps.*`、`longest_tracks.*`、`input_fields.*`：PNG 预览及 PDF/SVG 论文输出，三种格式各有用途。
- `*_map.npz`：可再生数值数组；本地保留，Git 忽略。

## 5. 三种验证范围

```sh
# 发布文件的内容哈希检查；不需要原始数据和 map.npz
.venv/bin/python scripts/run_experiments.py --verify
# 重算结果并审计；Ring 不需要外部数据
.venv/bin/python scripts/run_experiments.py --dataset ring
# 已有全部数值数组时，审计约束、证书、拓扑及身份，不重新求解
.venv/bin/python scripts/run_experiments.py --audit --dataset both
```

数值审计会更新报告、validation 和 manifest。当前发布证书绑定执行源码哈希，并与四份旧基线记录比较；整理工作不会通过重新盖章掩盖源码变化。单纯哈希通过不等同于重新运行全实验。

历史单轴推导见 `solver.md`；历史实验可在 Git 历史中追溯。当前结论必须依据 `results.md` 与 `results/`。
