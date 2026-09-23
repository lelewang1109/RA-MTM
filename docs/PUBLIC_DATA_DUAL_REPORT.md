# Ring / ERA5：Dual-Reference RA-MTM 验证

本次为固定协议的初步实证验证，不是调参后的最佳结果。完整原始表、三次计时、拓扑检查与失败栅格尝试均保留。

## 数据与公平性

- Ring：已有作者生成器及固定版本生成的40帧14×14 float32场，固定域[0,210]²；不是声称从论文网页下载了原始二进制文件。
- ERA5：本地公共再分析MSLP子集，1999-11-17至2000-01-14，沿用完整118帧、12小时采样、49×49网格、250 km平滑及等面积投影；不能声称与两篇文章所有预处理/文件逐字节一致，也没有独立气旋真值。
- 所有方法共享提取树、叶支持centroid/area及正重叠Hungarian匹配。baseline核心、preset、对应与预处理未改。与历史Ring和ERA5的TMTM/ST连续anchor对照最大差为0。
- 本次候选严格采用centroid reference，rho=.5；不是此前Ring的extremum reference/rho=1修正。X-only与Dual-X完全相同，唯一新增信息来自Y；beta=4、gamma=1、lambda=.5、eta=.1。测度尺度沿用固定域容量规则，Ring按210/120换算gap和budget，ERA5保持原单位。
- 单视图的二维主读出给予真实出生帧Y，此后保持不变（birth-Y oracle）；Dual直接组合两轴。另报告只用首帧拟合、此后固定的二维仿射读出，均不改baseline算法。Ring首帧只有一个feature，仿射方向不可辨识，约定零斜率/首帧均值并明确标记，不声称完成可靠校准。

## 指标解释

SNS越低越好；TW越高越好，k=3仅在叶数>6的帧定义，报告有效帧数，不能把少数有效帧外推到整条序列。TD是匹配anchor的总位移，越低不自动代表运动越准确：静止布局也有低TD。Dual逐轴报告SNS/TW/TD，不把两轴平均伪装成一个同等成本一维布局。
二维位置NRMSE、轨迹/运动误差沿用固定正方形域对角线归一化（Ring 210√2，ERA5 120√2）；这里ERA5的120是固定显示画布边长，不是原始经纬度跨度。direction为wrapped radians，仅真步长>0.001×canvas有效；预测静止而真运动有效记π。所有数值是提取feature的编码保真度。
运行时间是三次轮换顺序测量的layout+render+validation总耗时中位数，排除共享提取、指标计算、画图与I/O。Dual每次耗时为X+Y，不因复用X-only消融结果而漏计第二个solver。此实现运行时间不等于论文作者C++系统性能。

## RING

| method | SNS_x | TW_x | TD_x | SNS_y | TW_y | TD_y | runtime_seconds | position_2d_nrmse | trajectory_2d_nmae | distance_nrmse_x | distance_nrmse_y |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TMTM | 0.136475 | 0.793651 | 282.153846 | — | — | — | 0.034136 | 0.227599 | 0.072914 | 0.857920 | — |
| ST-MTM | 0.064366 | 0.936508 | 780.712301 | — | — | — | 0.125491 | 0.333000 | 0.126154 | 0.282430 | — |
| X-only RA-MTM | 0.146821 | 0.706349 | 867.933360 | — | — | — | 0.423262 | 0.065739 | 0.057387 | 0.514341 | — |
| Dual-Reference RA-MTM | 0.146821 | 0.706349 | 867.933360 | 0.092756 | 0.880952 | 588.390972 | 0.804819 | 0.029084 | 0.031899 | 0.514341 | 0.383997 |

相对X-only，二维位置NRMSE变化 0.065739 → 0.029084；轨迹NMAE 0.057387 → 0.031899。最大tau_X=32.8791，tau_Y=20.8307。

首帧二维仿射读出对照：

| Method | 2D position NRMSE | 2D trajectory NMAE | Identifiable |
|---|---:|---:|---|
| TMTM | 0.307859 | 0.066532 | False |
| ST-MTM | 0.307859 | 0.066532 | False |
| X-only RA-MTM | 0.307859 | 0.066532 | False |

匹配可靠性筛查（运动矢量NMAE）：

| Method | IoU min | Interior only | Pairs | Motion 2D NMAE |
|---|---:|---|---:|---:|
| TMTM | 0.0 | False | 146 | 0.021434186105962025 |
| TMTM | 0.25 | False | 141 | 0.01862077693538133 |
| TMTM | 0.5 | False | 127 | 0.01461215320787364 |
| TMTM | 0.0 | True | 71 | 0.016813679054311862 |
| ST-MTM | 0.0 | False | 146 | 0.03040728896165906 |
| ST-MTM | 0.25 | False | 141 | 0.027176390230653366 |
| ST-MTM | 0.5 | False | 127 | 0.020825903862897423 |
| ST-MTM | 0.0 | True | 71 | 0.023096496366238322 |
| X-only RA-MTM | 0.0 | False | 146 | 0.022217397036010472 |
| X-only RA-MTM | 0.25 | False | 141 | 0.02093182743647843 |
| X-only RA-MTM | 0.5 | False | 127 | 0.017792910522011957 |
| X-only RA-MTM | 0.0 | True | 71 | 0.020892567398439834 |
| Dual-Reference RA-MTM | 0.0 | False | 146 | 0.017545737605299535 |
| Dual-Reference RA-MTM | 0.25 | False | 141 | 0.018022385569229287 |
| Dual-Reference RA-MTM | 0.5 | False | 127 | 0.01695304696720965 |
| Dual-Reference RA-MTM | 0.0 | True | 71 | 0.017155198434353394 |

## ERA5

| method | SNS_x | TW_x | TD_x | SNS_y | TW_y | TD_y | runtime_seconds | position_2d_nrmse | trajectory_2d_nmae | distance_nrmse_x | distance_nrmse_y |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TMTM | 0.148970 | 0.803912 | 3537.800000 | — | — | — | 0.716353 | 0.227620 | 0.149430 | 0.525862 | — |
| ST-MTM | 0.078461 | 0.875942 | 3781.155548 | — | — | — | 0.828798 | 0.600873 | 0.146880 | 0.299981 | — |
| X-only RA-MTM | 0.217439 | 0.713284 | 2713.285835 | — | — | — | 1.669844 | 0.068127 | 0.063386 | 0.526819 | — |
| Dual-Reference RA-MTM | 0.217439 | 0.713284 | 2713.285835 | 0.129072 | 0.867825 | 1626.445057 | 3.348091 | 0.048036 | 0.044568 | 0.526819 | 0.394023 |

相对X-only，二维位置NRMSE变化 0.068127 → 0.048036；轨迹NMAE 0.063386 → 0.044568。最大tau_X=31.9122，tau_Y=18.9535。

首帧二维仿射读出对照：

| Method | 2D position NRMSE | 2D trajectory NMAE | Identifiable |
|---|---:|---:|---|
| TMTM | 0.237049 | 0.154770 | True |
| ST-MTM | 0.501107 | 0.144020 | True |
| X-only RA-MTM | 0.190910 | 0.062153 | True |

匹配可靠性筛查（运动矢量NMAE）：

| Method | IoU min | Interior only | Pairs | Motion 2D NMAE |
|---|---:|---|---:|---:|
| TMTM | 0.0 | False | 439 | 0.06672770554465753 |
| TMTM | 0.25 | False | 310 | 0.055641356803526935 |
| TMTM | 0.5 | False | 204 | 0.04645546564949754 |
| TMTM | 0.0 | True | 45 | 0.04429458921522787 |
| ST-MTM | 0.0 | False | 439 | 0.06535339514220896 |
| ST-MTM | 0.25 | False | 310 | 0.060102828760544215 |
| ST-MTM | 0.5 | False | 204 | 0.06548871556329504 |
| ST-MTM | 0.0 | True | 45 | 0.050950611942146236 |
| X-only RA-MTM | 0.0 | False | 439 | 0.03481770357843934 |
| X-only RA-MTM | 0.25 | False | 310 | 0.031979159754235896 |
| X-only RA-MTM | 0.5 | False | 204 | 0.029738633495730464 |
| X-only RA-MTM | 0.0 | True | 45 | 0.026525722278224858 |
| Dual-Reference RA-MTM | 0.0 | False | 439 | 0.03194182713692035 |
| Dual-Reference RA-MTM | 0.25 | False | 310 | 0.03215221764669583 |
| Dual-Reference RA-MTM | 0.5 | False | 204 | 0.03305416559532533 |
| Dual-Reference RA-MTM | 0.0 | True | 45 | 0.023920342436109843 |

## 如何解释创新价值

两组数据都支持“第二个参考方向改善feature级二维参考位置/运动编码”的结论，不能支持“Dual在所有性能指标优于ST-MTM”。ST-MTM的相对几何通常更好，Dual仍有非零tau和距离失真，且需要两个solver与两张图。应把固定参考语义和可解释冲突作为贡献，而不是把SNS/TW/TD综合包装成全面优越。
Ring中支持集重分配会使centroid突然变化，因此跟随centroid并不等于准确追踪物理环或极值位置。ERA5的大量边界特征及估计匹配同样限制物理解释；筛查表保留小样本或不利结果。不能从单个气象时段推出跨季节/多数据集泛化。

## 图与验证

每组数据有 input_fields、comparison_maps、longest_tracks 三张图，各含PNG、SVG、PDF。比较图中X-only=Dual-X，上X下Y用相同时间轴与固定世界轴；TMTM/ST图清楚标注原生归一化输出位置，不伪装成世界坐标。轨迹选择按寿命最长3条，不按表现挑选。
Ring TMTM/ST保持196 samples；Dual每轴784。ERA5的实际分辨率见metrics.csv与各records；RA两轴16,384。仅增加栅格分辨率以满足拓扑/非零像素宽度，连续宽度和solver不变。不宣称等总像素预算优势。
共632个不同标量图（158输入帧×TMTM/ST/Dual-X/Dual-Y）通过完整标量拓扑检查；三次运行的anchors及maps一致。独立审计有限坐标、宽度、非重叠、预算、合法序与全部LP候选。macOS数值后端出现matmul overflow/invalid警告，但输出均有限、有界且独立不使用矩阵乘法的约束审计通过；运行日志保留，未将警告隐藏成无异常运行。

## 文件路径

- 实验：`experiments/dual_reference/public_data.py`；审计/报告：`experiments/dual_reference/public_report.py`。
- 表：`results/dual_public/{ring,era5}/{metrics,rendered_metrics,affine_metrics,tracking_robustness,runtime_repeats}.csv`。
- 图：`results/dual_public/{ring,era5}/{input_fields,comparison_maps,longest_tracks}.{png,svg,pdf}`。
- 证书/输入：各数据目录的 `*_records.json`、`shared_features.json`、`protocol.json`、`status.json`。
- 审计：`results/dual_public/validation.json`、`manifest.json`、`execution.txt`。本地可再生NPZ不纳入Git。

复现：`.venv/bin/python experiments/dual_reference/public_data.py`，随后 `.venv/bin/python experiments/dual_reference/public_report.py`。原始ERA5文件需保持在protocol记录的路径并与记录SHA256一致。历史结果不覆盖。
