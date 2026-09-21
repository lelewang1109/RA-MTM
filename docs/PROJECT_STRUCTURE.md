# RA-MTM 项目结构与复现指南

本文档说明代码、实验、论文图表和本地材料各自放在哪里，以及不同类型的修改需要运行哪个入口。方法、指标、公平性、数值结果和证据边界集中在 [EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md)。

## 1. 项目边界

RA-MTM 当前是**论文方法验证与可复现证据仓库**，不是通用软件产品。

| 内容 | 正式位置 | 是否进入 Git | 作用 |
|---|---|---:|---|
| 方法与 baseline | `src/ramtm/` | 是 | 唯一可复用实现 |
| 实验协议与编排 | `experiments/` | 是 | 生成数据、运行方法、验证和整理发表材料 |
| 正式论文证据 | `results/` | 是，NPZ 除外 | 当前一次完整运行的图、表、记录和清单 |
| 理论示意图 | `figures_theory/` | 是 | 方法解释；不作为数值证据 |
| 生成/真实数据 | `data/generated/`、`data/real/` | 否 | 本地输入，可由脚本生成或单独保存 |
| 论文 PDF | `references/*.pdf` | 否 | 本地方法核对；只提交来源与哈希 |
| 历史运行和探索材料 | `archive/` | 否 | 本地回溯，不进入正式流程 |

## 2. 正式目录

```text
RA-MTM/
├── src/ramtm/
│   ├── error_budget.py          RA-MTM 的 LP 下界和预算约束 QP
│   ├── evaluation.py            共享真值、任务指标与首帧规范化
│   ├── reference_anchored.py    固定世界坐标栅格化与完整标量填充
│   └── baselines/               TMTM、ST-MTM 论文方法复现
│
├── experiments/
│   ├── synthetic_1d/            机制、正确性、消融和敏感性实验
│   ├── gaussian_2d/             二维场、18 序列协议和困难场景验证
│   └── publication.py           分类论文证据并生成主表、主图和报告数值段
│
├── scripts/
│   ├── run_all.py               清理、归档、失败即停的完整运行器
│   ├── run_all.sh               shell 入口和 Python 解释器选择
│   └── manifest.py              最终依赖闭包哈希和一致性验证
│
├── results/
│   ├── main/                    正文主指标、LaTeX 表、主图与校准稳健性
│   ├── auxiliary/               静态/缺输入等范围与正确性辅助检查
│   ├── ablation/                简单场景和困难场景的组件消融
│   ├── sensitivity/             参数、噪声、baseline 与首帧校准敏感性
│   ├── validity/                拓扑、可行性、下界、栅格和回归检查
│   ├── supplementary/           全部复现实例、配对差值和原始套件记录
│   ├── run_status.json          `running` / `failed` / `complete`
│   └── manifest.json            一次完整运行的 SHA-256 依赖闭包
│
├── figures_theory/              四张独立理论示意图及其绘图脚本
├── docs/                        实验报告与本指南
├── data/                        数据政策；实际数据文件不上传
├── references/                  文献来源和哈希；PDF 不上传
├── archive/                     旧运行和历史材料；不上传且不被实验导入
└── pyproject.toml               Python 版本、依赖和包配置
```

## 3. 从源码到论文结果

```text
src/ramtm 方法、baseline 和评价
                  │
                  ▼
experiments/synthetic_1d + experiments/gaussian_2d
                  │
                  ├──► data/generated/          本地可重建输入
                  │
                  ▼
        数值、约束、拓扑与栅格验证
                  │
                  ▼
experiments/publication.py       只整理当前运行，不重新优化
                  │
                  ▼
results/{main,auxiliary,ablation,sensitivity,validity,supplementary}
                  │
                  ▼
scripts/manifest.py              最后生成并核验完整依赖闭包
```

只有来自同一次完整运行、通过对应断言、能在表格或验证记录中追溯、且没有超出报告证据边界的结果，才能进入论文主张。

## 4. 完整复现

要求 Python 3.10 或更高版本；正式依赖固定在 `pyproject.toml`。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
PYTHON_RUNNER=.venv/bin/python ./scripts/run_all.sh
.venv/bin/python scripts/manifest.py --verify
```

完整入口按以下顺序执行：

1. 将旧 `results/` 和 `data/generated/` 移入本地 `archive/before_run_*`。
2. 生成并运行一维三方法完整输出。
3. 执行解析、回归、可行性和输出拓扑检查。
4. 执行参数、噪声、baseline 敏感性和组件消融。
5. 生成二维 18 序列，运行三种方法并重新提树验证完整输出。
6. 执行困难二维场景的消融、变体和直接投影合法性检查。
7. 生成论文主表、主图、分类结果和报告数值段。
8. 将状态写为 `complete`，最后生成唯一的 `results/manifest.json`。

任一步失败都会立即停止，并在 `results/run_status.json` 中记录失败阶段；失败运行不会发布成功 manifest。

## 5. 结果目录如何使用

| 目录 | 应用于 | 不应混作 |
|---|---|---|
| `main/` | 正文主表、主图、核心定量陈述 | 全部原始实验记录 |
| `auxiliary/` | 正控制、适用性和缺输入说明 | baseline 优势排名 |
| `ablation/` | 判断各机制是否有独立作用 | 完整方法的主结果 |
| `sensitivity/` | 参数、噪声、校准和 baseline 设置稳健性 | 事后挑选最优参数 |
| `validity/` | 拓扑、约束、LP/QP、栅格及回归正确性 | 任务性能主指标 |
| `supplementary/` | 全 seed、分辨率、轨迹和当前运行原始套件 | 历史版本仓库 |

主文报数应优先读取 `results/main/*.csv`；正确性主张应指向 `results/validity/`；需要复查具体运行时，再进入 `results/supplementary/`。不要直接从本地 NPZ 手抄论文数值。

## 6. 不同修改对应的运行方式

### 6.1 修改算法、指标、数据或实验协议

必须执行完整入口 `./scripts/run_all.sh`。这些变化会影响证据链，不能只改 CSV、报告或 manifest。

### 6.2 只修改论文展示分类或格式

在当前完整 raw 结果仍有效时，可以运行：

```sh
python experiments/publication.py
python scripts/manifest.py
python scripts/manifest.py --verify
```

该流程只重建论文表图和报告数值段，不重新求解布局。

### 6.3 只修改解释文档或理论示意图

理论图用 `python figures_theory/draw_theory_figures.py` 重建。确认内容后只需更新并验证 manifest：

```sh
python scripts/manifest.py
python scripts/manifest.py --verify
```

理论图必须继续标明 schematic，不能与 `results/` 中的实验图混作数值证据。

## 7. 上传范围和清洁检查

提交前至少执行：

```sh
python scripts/manifest.py --verify
git diff --check
git status --short
```

以下内容不应进入 Git：

- `archive/` 及旧运行快照；
- `data/generated/`、`data/real/` 和其他数据文件；
- `results/**/*.npz` 大数组；
- `references/*.pdf`；
- `.venv/`、缓存、日志、`.DS_Store` 和编辑器配置。

## 8. 实现与复现注意事项

- 单套实验脚本是开发中间入口，不会发布完整项目 manifest；论文交付应使用完整入口。
- SLSQP 的内部试探点可能被裁剪到边界；最终判断以约束余量、预算和最优间隙断言为准，不能只看优化器 `success`。
- 不允许手工修改生成 CSV/JSON 来“修复”结果，也不允许按场景临时放宽约束。
- 跨机器运行时间、图像元数据和 NPZ 封装字节可能不同；数值正确性以脚本断言和容差为准。
- `archive/` 从不被正式实验导入；历史探索不能重新贴成当前证据。
