# RA-MTM 论文项目结构与复现流程

## 1. 目录职责

```text
src/ramtm/                         方法实现
  error_budget.py                  RA-MTM 布局与误差预算核心
  reference_anchored.py            固定参照渲染入口
  baselines/                       TMTM、ST-MTM 基线复现

experiments/                       只放实验逻辑，不保存结果
  synthetic_1d/                    一维与折线机制实验、验证、扫描、消融
  gaussian_2d/                     二维高斯场完整实验

data/
  generated/synthetic_1d/          一维实验生成输入
  generated/gaussian_2d/           二维实验生成输入
  real/                            本地真实数据，不纳入当前论文结果

results/
  <experiment>/figures/            论文图与辅助图
  <experiment>/tables/             指标、轨迹、消融与检查表
  <experiment>/records/            参数、证书、验证和中间记录
  <experiment>/arrays/             大型 NPZ 数组，不上传 Git

docs/                              实验报告与项目结构说明
references/                        论文来源和哈希；PDF 仅本地保存
archive/                           旧版本与历史材料，仅用于追溯
```

## 2. 从方法到论文结果的流程

```text
方法/基线实现
    ↓
实验生成器 → data/generated/<experiment>
    ↓
三种方法运行
    ↓
数值与拓扑验证
    ↓
results/<experiment>/{figures,tables,records,arrays}
    ↓
docs/EXPERIMENT_REPORT.md
```

## 3. 推荐复现顺序

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
./scripts/run_all.sh
```

若只验证核心机制，运行 `./experiments/synthetic_1d/run_pipeline.sh`；若只生成二维论文主图，运行 `python experiments/gaussian_2d/run_experiment.py`。

## 4. 写论文时如何取材料

- 方法公式与假设：`docs/EXPERIMENT_REPORT.md` 第 2–5 节。
- 数据与实验设置：报告第 6–7 节，以及两个实验目录内的 README。
- 主文候选图：两个结果目录的 `figures/`。
- 定量表格：两个结果目录的 `tables/metrics.csv`。
- 消融与敏感性：`results/synthetic_1d/tables/ablation.csv` 和 `sensitivity.csv`。
- 可复现证据：`records/`、`manifest.json` 与拓扑检查表。

真实数据目前与受控实验明确隔离，尚未进入论文主结果，避免把历史探索与已验证结论混在一起。

