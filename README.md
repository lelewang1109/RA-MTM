# RA-MTM

**Reference-Anchored Merge Tree Maps · 参考锚定合并树图**

RA-MTM 将二维时变标量场中的同一组特征分别沿固定世界 X、Y 方向布局，生成两张时间对齐的一维时空图，并按特征身份配对 anchor，估计二维位置与运动。X/Y 是方法的双轴设计，方法名称统一为 **RA-MTM**。

## 方法概览

```text
标量场 → 合并树 → 叶面积 A、质心 C、极值 E、跨帧身份
                         ├─ qX = E.x → LP 最小参考偏移 → 预算内 QP → X map
                         └─ qY = E.y → LP 最小参考偏移 → 预算内 QP → Y map
同一身份的 (anchor X, anchor Y) → 二维位置及运动评价
```

两轴保持树层次及绝对区间宽度 `w=cA`。主线用叶极值作为参考，质心用于相对几何及消融。参考位置与层次、宽度、几何可能冲突，因此报告最小偏移 `tau`、预算与几何误差。双轴视图不能无损恢复二维场或完整形状，当前枚举求解适合小树。

## 阅读顺序

1. [方法流程](docs/method.md)：输入、坐标、身份、双轴求解、渲染和评价。
2. [求解推导](docs/solver.md)：每个轴的 LP/QP、约束及与已有方法的区别。
3. [实验复现](docs/reproducibility.md)：数据准备、运行命令、代码对应和验证。
4. [实验结果](docs/results.md)：Ring、ERA5、所有基线及质心消融。
5. [结果文件索引](results/README.md)与[目录规范](docs/project_structure.md)。

## 安装与运行

Python ≥3.10。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e .
# 验证发布文件，不需要原始数据
.venv/bin/python scripts/run_experiments.py --verify
# Ring 自动生成
.venv/bin/python scripts/run_experiments.py --dataset ring
# 提供 ERA5 文件后重跑两套实验
.venv/bin/python scripts/run_experiments.py --dataset both
# 单独运行测试
.venv/bin/python -m unittest discover -s tests -v
```

ERA5 数据准备见 [data/README.md](data/README.md)。重跑会更新所选数据集的输出、报告及 manifest；仅重跑 Ring 时，报告和 manifest 的验证范围为 Ring。

## 目录结构

```text
RA-MTM/
├── README.md
├── pyproject.toml
├── src/ramtm/          # 核心算法、渲染、评价和基线
├── experiments/       # 实验协议、ERA5 预处理、Ring 数据生成
├── scripts/           # 统一运行与结果校验入口
├── tests/             # 单元测试、回归样例、基线快照
├── docs/              # 方法、推导、复现和实验报告
├── results/           # ring/、era5/、完整性清单及验证摘要
├── data/              # 数据说明；原始输入不入库
└── references/        # 参考资料出处及来源哈希
```

## 结果摘要

| 数据集 | X-only 位置 NRMSE | RA-MTM 位置 NRMSE | RA-MTM 方向误差 rad |
|---|---:|---:|---:|
| Ring | 0.06397 | 0.02880 | 0.16143 |
| ERA5 | 0.08364 | 0.05830 | 0.64123 |

完整结果含 TMTM、ST-MTM、X-only 和质心消融。ST-MTM 的相对几何可能更好；上述结果不代表全面优越，ERA5 极值也不等于经过验证的气旋中心。

![Ring comparison](results/ring/comparison_maps.png)

原项目历史保留在 Git 中；原始数据、论文 PDF、本地归档和可再生数值数组不上传。
