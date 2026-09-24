# 文件夹规范与清理记录

## 唯一主线

**方法：`docs/XY_METHOD.md` → 运行：`scripts/run_all.py` → 结果：`results/xy/` → 报告：`docs/EXPERIMENT_REPORT.md`。**

不要按“最新修改时间”猜哪种方法是正式方法。
主线是叶极值参考 XY；质心参考是消融；单轴及 JOLT 是历史。

| 文件/目录 | 职责 | 是否主线 |
|---|---|---|
| `src/ramtm/reference_points.py` | 叶极值/支撑质心的明确选择；X/Y身份严格配对 | 是 |
| `src/ramtm/error_budget.py` | 方向投影、合法叶序、LP tau、预算QP | 是，共用 |
| `src/ramtm/reference_anchored.py` | 固定世界像素映射与标量填充 | 是，共用 |
| `src/ramtm/dual_evaluation.py` | 位置与运动指标 | 是 |
| `src/ramtm/baselines/` | TMTM / ST-MTM 核心实现 | 对照，未改 |
| `experiments/xy/` | 主线协议、验证、报告 | 是 |
| `experiments/dual_reference/public_data.py` | 两种参考语义共用的数据实验驱动 | 共用 |
| `experiments/real_era5/run_experiment.py` | 数据预处理、匹配及旧baseline适配器 | 共用，未改算法 |
| `experiments/ring/dataset.py`、`source/` | 原作者数据生成和来源 | 输入 |
| `experiments/dual_reference/`其他 | 25质心机制及历史诊断 | 补充，不能当极值协议 |
| `experiments/synthetic_1d/`、`gaussian_2d/` | 旧canonical数据与基线适配器 | 兼容保留 |
| `experiments/history/jolt_mtm/` | 已停止的探索 | 否 |
| `docs/history/` | 旧单轴与JOLT报告 | 否 |
| `figures_theory/` | 旧单轴概念图 | 否，不作为当前XY方法图 |
| `archive/` | 本地快照、清理备份，不上传 | 否 |

保留共享模块的旧路径是为了不改 baseline 适配器及数据来源哈希；不重复复制这些函数到新 solver。
历史结果目录保留原路径，避免破坏论文证据引用。它们已从 README 的主结果入口移除，并在 `results/README.md` 明确标为历史。

## 运行范围

- 当前公共数据：`.venv/bin/python scripts/run_all.py --dataset both`。
- 只跑Ring：末尾改 `--dataset ring`。
- 保留的25质心机制：`.venv/bin/python scripts/run_all.py --suite mechanisms`。
- 历史单轴全套：`.venv/bin/python scripts/run_legacy.py`，显式选择才会运行；只备份历史所属输出。
- 当前结果哈希检查：`.venv/bin/python experiments/xy/verify.py --verify`。

当前默认入口不再搬走整个results目录，不修改本地ERA5输入，不覆盖历史主表。
当前和历史manifest分开。历史哈希因共享源码迭代而不匹配时，不重新生成旧manifest来掩盖没有重跑的事实。

## 本次清理

- 删除仓库中40张重复 `results/ring_time_steps/ring_t*.png` 及其说明；完整输入、来源、时空图及数值结果保留。
- 删除项目内可再生的 `__pycache__`、Finder元数据、空输出目录。
- 将JOLT代码与旧报告移入history；保留其未通过门槛的结论和所有数值证据。
- 原单轴总报告移入 `docs/history/SINGLE_AXIS_REPORT.md`；原位置现在只报告当前XY。
- `docs/RA_X_METHOD_FLOW.md` 是开始本轮时已有的未提交说明稿，原样保留，没有擅自纳入提交。
- 不删除 baseline、原始数据、未获胜实验、参数敏感性或完整证书。

逐文件删除哈希与本地恢复位置见 [CLEANUP_RECORD.json](CLEANUP_RECORD.json)。
已跟踪的重复导出也可从整理前提交 `f0d6add` 恢复。

## 后续添加规则

1. 主线只增加到 `experiments/xy`、`results/xy`，不要再创建v2/v3/final_new文件夹。
2. 新候选先放 `experiments/history` 或单独明确标为pilot，不能覆盖正式协议。
3. 修改参考点、rho、匹配或geometry定义必须写protocol并单独比较，不能沿用旧指标标签。
4. 图中标量色、identity、q、anchor必须明确区分；禁止无说明循环颜色表示身份。
5. 运行失败的目录保持running/failed，只有校验完成后才能作为正式结果。
