# RA-MTM 项目结构与复现指南

本文档回答三个问题：代码在哪里、实验怎么跑、论文中的图表来自哪个文件。研究动机、方法公式、实验设计与结论见 [EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md)。

## 1. 项目边界

当前仓库是一个**论文方法验证与复现仓库**，不是通用软件产品。

- 上传 Git：方法代码、baseline 复现、实验脚本、文档、图表、紧凑的验证记录。
- 仅本地保存：真实/生成数据、`.npz` 大数组、论文 PDF、虚拟环境、缓存、`archive/` 历史材料。
- 当前论文证据：一维/折线受控实验与二维高斯场实验。
- 尚未纳入主结论：`data/real/` 中的真实数据与历史探索结果。

## 2. 目录职责

```text
RA-MTM/
├── src/ramtm/                         可复用的方法实现
│   ├── error_budget.py                  RA-MTM 布局、叶序与误差预算
│   ├── reference_anchored.py            固定参照离散化与完整标量图渲染
│   └── baselines/
│       ├── tmtm.py                       TMTM 复现
│       └── stmtm.py                      ST-MTM 复现
│
├── experiments/                       实验编排；不保存结果
│   ├── synthetic_1d/                    一维/折线机制、回归、扫描与消融
│   └── gaussian_2d/                     二维高斯场、完整时序图与拓扑验证
│
├── data/                              实验输入；不上传数据文件
│   ├── generated/synthetic_1d/          一维实验生成输入与树
│   ├── generated/gaussian_2d/           二维网格、输入树与生成参数
│   └── real/                            本地真实数据；不参与当前主结论
│
├── results/                           按实验分组的可审计输出
│   └── <experiment>/
│       ├── figures/                      论文图、诊断图和动画
│       ├── tables/                       指标、轨迹、消融、敏感性与检查表
│       ├── records/                      参数、证书、中间记录与验证摘要
│       ├── arrays/                       可重生的 `.npz` 大数组；仅本地保存
│       └── manifest.json                 该次运行的 SHA-256 文件清单
│
├── docs/                              项目流程与实验报告
├── references/                        参考文献来源和哈希；PDF 仅本地保存
├── scripts/run_all.sh                 两套受控实验的统一入口
└── pyproject.toml                     Python 包与依赖的唯一配置
```

`archive/` 是本地历史材料，不属于当前流程，不上传 Git。

## 3. 数据到论文结果的流程

```text
src/ramtm 方法与 baseline
            │
            ▼
experiments/<experiment> 生成器与运行器
            │
            ├──► data/generated/<experiment>      输入与提取树
            │
            ▼
       三种方法的布局/渲染
            │
            ▼
       数值、约束与拓扑验证
            │
            ▼
results/<experiment>/{figures,tables,records,arrays}
            │
            ▼
docs/EXPERIMENT_REPORT.md 中的图表与结论
```

一个结果只有同时满足以下条件才应进入论文：来自当前实验入口、通过对应验证、能在 `tables/` 或 `records/` 中找到数值证据，且报告中没有超出证据边界的表述。

## 4. 环境安装

建议 Python 3.9 或更高版本。在项目根目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

依赖版本统一由 `pyproject.toml` 管理，不在各实验目录重复维护。

## 5. 复现入口

### 5.1 运行全部受控实验

```bash
./scripts/run_all.sh
```

顺序是：

1. 生成并运行一维/折线实验。
2. 执行解析、回归和标量拓扑检查。
3. 执行参数扫描与质心扰动。
4. 执行模块消融。
5. 验证必需产物并更新 manifest。
6. 生成二维高斯场，运行三种方法并验证全部完整输出。

当前完整运行的成功标志是：

- `PASS 117 checks; 92 / 92 STMTM scalar topology checks`
- `PASS 189 full scalar topology checks`

### 5.2 只运行一维/折线套件

```bash
./experiments/synthetic_1d/run_pipeline.sh
```

五个阶段的顺序固定为：

| 阶段 | 脚本 | 主要产物 |
|---|---|---|
| 1. 主实验 | `run_experiments.py` | 生成输入、三种方法的数组、主图、指标、轨迹与证书 |
| 2. 正确性 | `verify.py` | `topology_checks.csv`、`verification.json` |
| 3. 敏感性 | `sensitivity.py` | 参数扫描、质心扰动及摘要 |
| 4. 消融 | `ablation.py` | `ablation.csv`、`ablation_trajectories.csv` |
| 5. 收尾 | `finalize.py` | 边界检查、验证摘要和 `manifest.json` |

### 5.3 只运行二维高斯套件

```bash
python experiments/gaussian_2d/run_experiment.py
```

该入口一次完成场生成、split-tree 提取、特征匹配、三方法运行、完整标量图重新提树、图表/动画生成和 manifest 更新。

## 6. 输出合约

| 目录 | 内容 | 是否上传 | 论文用途 |
|---|---|---|---|
| `figures/` | PNG/SVG/GIF | 是 | 主文图、补充图、过程可视化 |
| `tables/` | CSV | 是 | 定量表格、轨迹、消融、敏感性 |
| `records/` | JSON | 是 | 参数、可行性证书、中间记录、验证摘要 |
| `arrays/` | NPZ | 否 | 本地复查和二次分析 |
| `manifest.json` | 路径与 SHA-256 | 是 | 核对一次实验使用的确切产物 |

论文中不应直接从 `arrays/` 报数；应该引用可审阅的 `tables/` 或 `records/`，并使用 `manifest.json` 确认版本。

## 7. 论文材料对照

| 论文内容 | 主要来源 |
|---|---|
| 方法动机、假设与公式 | `docs/EXPERIMENT_REPORT.md` 第 1–5 节 |
| 一维/折线数据与设置 | 报告第 6–7 节，`experiments/synthetic_1d/` |
| 二维高斯数据与设置 | 报告第 6.4、7.1 节，`experiments/gaussian_2d/` |
| 二维主图 | `results/gaussian_2d/figures/translation_growth_comparison.*` |
| 一维主机制图 | `results/synthetic_1d/figures/comparison.*` |
| 定量指标 | 两个实验的 `tables/metrics.csv` |
| 层次变化与误差预算 | `results/synthetic_1d/figures/diagnostics.*`、`records/*_budget_certificates.json` |
| 消融 | `results/synthetic_1d/tables/ablation.csv` |
| 敏感性 | `results/synthetic_1d/tables/sensitivity.csv`、`centroid_perturbation.csv` |
| 拓扑与数值正确性 | `tables/topology_checks.csv`、`records/verification.json`、`records/validation*.json` |
| 局限与后续工作 | 报告第 11–12 节 |

## 8. 修改实验时的检查顺序

1. 修改 `src/ramtm/` 或对应 `experiments/` 脚本。
2. 从入口重跑受影响的实验，不手工编辑生成的 CSV/JSON。
3. 确认通过数值、约束、拓扑和必需产物检查。
4. 核对 `metrics.csv`、主图和验证摘要是否与研究叙述一致。
5. 更新 `EXPERIMENT_REPORT.md` 中受影响的数值、结论与局限。
6. 检查 Markdown 链接、Git 上传范围和 manifest，再提交。

## 9. 常见问题

- **运行后出现大量未跟踪数据：**检查 `.gitignore`；`data/`、`arrays/`、PDF 和 `archive/` 不应被跟踪。
- **找不到 `ramtm` 包：**先执行 `python -m pip install -e .`；仓库内实验入口也会显式加载 `src/`。
- **图表与报告数值不一致：**以新运行的 `tables/metrics.csv` 为数值源，更新报告并核对 manifest。
- **只有骨架没有完整标量图：**检查输入是否包含完整标量样本、增广弧和填充所需信息。
- **SLSQP 出现边界裁剪警告：**当前已知扫描可能出现该警告；以结果的约束余量、QP 间隙和后续断言为判定依据，不仅凭警告文本判断失败。
