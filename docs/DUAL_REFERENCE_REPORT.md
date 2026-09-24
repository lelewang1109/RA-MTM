> 历史/补充：本文使用质心参考，25序列结果仍保留。当前极值参考XY定义见 [XY_METHOD.md](XY_METHOD.md)。

# Dual-Reference RA-MTM：升级与实验报告

2026-09-23。本报告对应独立新增证据包 `results/dual_reference/`。原有单轴实验及不利结果完整保留。

## 1. 原 RA-MTM 的问题

默认 `q=C[:,0]` 只记录质心 X 投影，无法唯一确定二维位置。Ring 已有 extremum-reference 修正属于另一种参考定义，本次不将它混为 centroid 真值。

## 2. 为什么单 X 不够

`(50,10)` 与 `(50,90)` 有相同 X 参考；共同 Y 平移也不改变 X 参考。对任何共同位移 v，距离矩阵满足 `D(C+v)=D(C)`，因此相对距离本身也无法辨识绝对平移。这不是 ST-MTM 优化器错误，也不意味着其它输入发生变化时它的输出必定不变。

## 3. Dual 的核心思想

同一树、质心、面积和身份对应，两个固定方向独立求解。上图为 X-time，下图为 Y-time；横轴均为时间、纵轴为固定 world reference coordinate，同一身份用同色，第二张不旋转。两个视图是 complementary views。

## 4. 数学定义的变化

将有限非零方向归一化为单位向量，定义

\[
a_k=\tilde a_k/\|\tilde a_k\|_2,\qquad q_i^{(k)}=a_k^T C_i,\qquad d_{ij}=\|C_i-C_j\|_2,\qquad w_i=cA_i.
\]

\[
\tau_k^*=\min_{\pi\in\mathcal L(H),x,z}\max_i|x_i-q_i^{(k)}|.
\]

合法域继续保持子树叶连续、区间非重叠及固定 gap、固定画布、固定绝对宽度和 `|x-z|≤ρw/2`。容量不足报错，禁止缩小宽度。分别使用 `|x-q|≤τk*+Δ`，在预算内优化

\[
J_k=\beta\operatorname{mean}_i(x_i-q_i^{(k)})^2
+\gamma\operatorname{mean}_{i<j}(|x_i-x_j|-d_{ij})^2
+\lambda\operatorname{mean}_{i\in M}[(x_i^t-x_i^{t-1})-(q_i^{k,t}-q_i^{k,t-1})]^2
+\eta\operatorname{mean}_i(z_i-x_i)^2.
\]

新生特征无时间惩罚，空匹配集忽略时间项。正式参数沿用 Gaussian：β=4、γ=1、λ=.5、η=.1、ρ=.5、Δ=1、gap=.5、c=.012、canvas=[0,120]，不逐场景调参。

方向 scale 被消除。负向或斜向投影必须从固定原域设置 `canvas_origin` 和 extent。对于盒域 `[l,u]`，投影下界为 `Σmin(a_j l_j,a_j u_j)`，上界为 `Σmax(a_j l_j,a_j u_j)`。像素映射是 `round((x-origin)*(L-1)/extent)`，全时间保持相同，不能从每帧质心范围估计。通用单视图支持任意方向；当前 dual 重构接口明确固定 Cartesian X/Y。

## 5. 代码修改

共享 `src/ramtm/error_budget.py` 增加 `project_reference`、方向/轴参数、固定原点、身份匹配及 `solve_dual_reference_sequence`。`src/ramtm/reference_anchored.py` 增加双图渲染和身份检查；`src/ramtm/dual_evaluation.py` 实现二维指标。没有复制两个 solver。默认调用仍为 X-only，显式 `reference=` 兼容保留。本轮开始时的 TMTM/ST-MTM 核心及既有 Gaussian/1D baseline 适配器字节未改，哈希见 `experiments/dual_reference/baseline_snapshot.json`。

## 6. 两个 view 分别代表什么

X view 表示横向质心参考；Y view 表示纵向质心参考。显示 anchor 可因层次、宽度、边界和几何目标而偏离真实投影，并非直接绘制 centroid。τx/τy 分别表示最小不可避免的最大参考误差；汇总表记录时序最大值，逐帧值见 budgets.csv。

## 7. 如何重构 feature-level 二维位置

按同一个 persistent feature identity 组合 `C_hat=(anchor_X,anchor_Y)`。两个视图的合法叶序可以不同，不能按排序后的第几个 anchor 拼接。返回数据保持输入行身份，显式 track IDs 支持换序、出生和消失；未给 IDs 时保留旧 API 的固定行身份假设，无法检测调用者错误标注的身份。构造实验的对应由生成器峰身份统一提供，不构成真实场跟踪正确性证明。

## 8. 新增实验

七个完整 scalar-field 场景：pure_x、pure_y、diagonal、same_x、same_y、hierarchy_conflict、motion_growth。每条21帧、65²网格。另重跑全部原7 canonical、9 seed变体、2分辨率变体：总25条、525输入帧。真值来自提取叶弧支持的质心/面积，不用 Gaussian 参数代替。

网格量化使 nominal pure-X/pure-Y 的实际 centroid 有小幅正交波动，same-X/same-Y 的提取质心也非严格相等。`exact_mechanisms.json` 另提供精确 feature-level X/Y/对角/零运动及同轴拥挤控制，检查 ST 距离输入不变和双轴机制；这些是明确的摘要控制，不冒充完整 scalar-field 或 TMTM 实验。

## 9. 新指标与明确公式

固定 `Dx=Dy=120`，`D=sqrt(Dx²+Dy²)`，`e=C_hat-C`。

| 指标 | 定义 |
|---|---|
| position_2d_nrmse | sqrt(mean ‖e‖²) / D |
| position_2d_nmae | mean ‖e‖ / D |
| reference_x/y_nmae | mean abs(e_k) / Dk |
| reference_x/y_p95 | 95% quantile(abs(e_k)) / Dk |
| motion_magnitude_2d_nmae | mean abs(‖v_hat‖−‖v‖) / D |
| motion_2d_nmae | mean ‖v_hat−v‖ / D |
| trajectory_2d_nmae | mean(t>b) ‖(C_hat_t−C_hat_b)−(C_t−C_b)‖ / D；b为连续轨道出生帧 |
| direction_error_radians | abs(atan2(sin(theta_hat−theta),cos(theta_hat−theta))) 的均值 |
| distance_x/y_nrmse | sqrt(sum(d_ij−abs(anchor_i−anchor_j))² / sum d_ij²)，d为原二维距离 |

`v=C_t-C_(t-1)`，`v_hat=C_hat_t-C_hat_(t-1)`；theta由atan2计算。仅真实步长 **>0.12 world units/step** 时计算角度，报告有效样本数；没有有效样本留空，不输出NaN。真实运动有效但预测长度≤1e-10时角误差记π并单独统计，避免将atan2(0,0)误解成准确方向。所有分母固定，不按每帧动态范围归一化。

增长指标沿用现有 log MAE；实际像素 anchor 重新解码后重复二维评价，见 rendered_metrics.csv。连续运动误差为0不代表像素量化误差也为0。

## 10. 与三种单视图的正式比较

TMTM、ST-MTM、X-only均没有原生二维输出。主比较给予它们有利的 **真实初始Y oracle**，使用 `(native calibrated x(t), true_y(0))`，每个特征初始Y此后不动。X采用既有固定物理尺度、首帧反射/平移。Dual直接组合两个anchor，不拟合。不能把此oracle称为baseline本身恢复了Y。

强读出 `first_frame_2d_affine` 对三个单视图统一仅在首帧最小二乘拟合 `[anchor,1]B≈(Cx,Cy)`，随后冻结。它可借助初始相关性解释部分运动，但不能从不变anchor恢复共同平移。不使用未来真值，不更改baseline算法。几何列始终是原生一维布局质量，而非仿射解码后的距离。

完整175行（100主比较+75强读出）在 `results/dual_reference/tables/metrics.csv`，25场景全部保留。下表给出关键二维轨迹 NMAE（初始Y oracle读出）：

| 场景 | TMTM | ST-MTM | X-only | Dual |
|---|---:|---:|---:|---:|
| pure_x | .037870 | .037772 | .000351 | 0 |
| pure_y | .036985 | .036973 | .036960 | 0 |
| diagonal | .045201 | .045185 | .024688 | 0 |
| motion_growth | .026061 | .031424 | .018361 | 0 |
| hierarchy_change | .140390 | .088918 | .078688 | .078629 |
| crowding | .020993 | .021418 | .000836 | .001099 |
| advection_diffusion | .022864 | .025081 | .007151 | .000843 |

几何代价必须同时阅读：pure-Y的ST距离NRMSE为0.014675，Dual-X/Y为0.221396/0.354885；hierarchy_change为ST 0.246003、Dual-X/Y 0.298940/0.435799；crowding为ST 0.000477、Dual-X/Y 0.724784/0.018526；advection_diffusion为ST 0.383242、Dual-X/Y 0.414130/0.461470。所有场景完整伴随列在 main_results.md/.tex 和 metrics.csv。

## 11. 明确解决的问题

纯Y、对角和组合运动中，新增Y直接提供缺失运动分量。上述连续轨迹误差0表示布局误差随时间保持恒定，**不表示绝对位置完全无误差**：这些Dual位置NRMSE为0.008333。same-X中Y view区分纵向位置；same-Y中X view区分横向位置。两个视图无需各自承担完整二维空间。

## 12. 仍存在的冲突与反例

same-X：τx=7.2772、τy=0；same-Y：τx=0、τy=7.2645；hierarchy_conflict：τx=27.2221、τy=11.2470。τ反映排序、宽度、gap、边界联合约束，不能把全部τ叫排序冲突，也不是二维距离误差。

same-Y中，初始Y oracle已精确，而Dual的Y必须给有宽度区间留空间，位置NRMSE反而为0.048699。pure-X也可能因新增静态Y误差使位置指标变差。advection_diffusion中Dual位置0.068960，差于X-only oracle的0.057205，但轨迹显著改善。crowding中Dual轨迹0.001099差于X-only的0.000836。hierarchy_change的0.078629轨迹误差仍然存在。

25条序列对X-only初始Y oracle的位置指标：Dual更低/平/更高=10/1/14，轨迹=14/3/8；对ST强首帧二维仿射读出的轨迹为18/3/4。所有胜平负见 all_case_comparison.csv，1e-6仅作数值平局阈值，不是统计显著性。不得把相关构造序列当独立总体。

## 13. 不能解决的问题与验证边界

不能恢复完整二维scalar field、feature内部形状或无损全二维几何；两张图增加显示面积，未做等总像素预算用户研究；输入身份仍可能错误；centroid会受支持重分配影响，不能直接称为物理目标轨迹。新双轴证据仅覆盖构造场，旧ERA5/Ring保留原单参考定义。

穷举合法叶序只适合小树。LP证明当前帧所有合法序的最小最大偏差；QP间隙是给定上一帧的条件证书，非全时间最优性。方向独立优化，不直接最小化联合二维误差。硬约束优先，因此不能承诺精确位置或运动。

验证通过：2,625次完整标量图重提树和层次检查，包含TMTM、ST、X-only、Dual-X、Dual-Y；X-only与Dual-X相同，各记录一次，实际不同视图共2,100幅，不能重复计为独立证据。每轴每帧检查宽度、预算、叶序、LP候选τ、QP间隙、固定像素映射。单元测试用独立左端点变量LP验证τ，检查方向非有限/零值、换序/出生消失、渲染身份和零运动。旧一维回归通过210项检查及92帧三方法完整图验证。18原序列×3方法的anchor与历史数组最大差为0，记录见 canonical_regression.json。

## 14. 论文图推荐

1. **figure1_method**：方法总览，centroid/measure→X/Y投影→共用约束solver→对齐时间图→二维重构。灰底完整scalar map，实线anchor、虚线真实投影、填色绝对宽度。
2. **figure2_translation_invariance**：核心动机理论图，三个点共同平移(15,20)，距离逐项不变而qx/qy变化；明确是解析示意。
3. **figure3_translations**：pure-X、pure-Y、diagonal完整场，两个方向固定轴与一致身份。
4. **figure4_crowding**：same-X/same-Y互补性，同时暴露拥挤方向误差。
5. **figure5_hierarchy_conflict**：实际提取层次 `((A,B),(C,D))`，q、anchor、区间、预算及不同τ。
6. **figure6_comparison**：7新增+7原canonical，不筛场景；初始Y oracle读出与几何代价同时显示。

主文优先1、2、3、5、6；4可依篇幅放主文或补充。完整25条比较图为 supplementary_all_sequences。每图提供300dpi PNG与矢量SVG/PDF。

## 文件目录

- **新增文件**：`src/ramtm/dual_evaluation.py`、`tests/test_dual_reference.py`、`experiments/dual_reference/{datasets,run_experiment,exact_mechanisms,verify,figures,finalize,manifest}.py`、该目录README及baseline_snapshot.json、本报告。
- **修改文件**：`src/ramtm/__init__.py`、`src/ramtm/error_budget.py`、`src/ramtm/reference_anchored.py`、`README.md`、`docs/EXPERIMENT_REPORT.md`、`scripts/run_all.py`。此前工作区改动另保留。
- **正式结果**：`results/dual_reference/tables/{metrics,rendered_metrics,budgets,trajectories,topology,all_case_comparison}.csv`、`main_results.md`、`main_results.tex`。
- **正式图**：`results/dual_reference/figures/figure1_method.*` 至 `figure6_comparison.*`（见上方准确文件名）。
- **Supplementary**：`figures/supplementary_all_sequences.*`、`records/*_x_view.json`和`*_y_view.json`全部LP/QP证书、`*_input.json`、`exact_mechanisms.json`、`validation.json`、`canonical_regression.json`、`legacy_verification.json`、包级`manifest.json`。
- **本地可再生数组**：`results/dual_reference/arrays/*.npz`，包括原场、标量图、布局与真值，不纳入Git；原 `results/supplementary/` 保持完整。

独立manifest只认证新增dual依赖闭包，不追认旧ERA5/Ring共享代码版本。复现入口见 `experiments/dual_reference/README.md`，全项目runner也已加入双轴阶段。
