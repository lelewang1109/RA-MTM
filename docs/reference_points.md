# 参考点语义

主线参考点为同一叶特征的极值采样位置：Ring split tree 使用最大值位置，ERA5 join tree 使用最小值位置。支撑域质心用于二维距离项，并作为参考点消融。

Ring 的叶支撑域在早期可覆盖大部分画布，因此质心可能接近域中心；叶峰位置不一定接近质心。采用极值参考解决的是参考对象语义问题，不能等同于恢复环中心。

固定世界原点、极值参考、支撑质心和优化 anchor 是不同对象。两轴均使用同一个固定坐标变换；优化结果允许在可行预算内偏离目标。不能逐帧移动原点或调整缩放来使图看起来更接近目标。

ERA5 使用固定 `pressure_soft` 红蓝色卡，显示 MSLP−1013.25 hPa、范围 ±35 hPa；红蓝表示压力，不表示特征身份。具体实现见 `experiments/public.py::plot`，其色卡源于项目历史中原 ERA5 图形协议。

跨帧匹配基于支撑域重叠，不是物理对象真值；极值采样跳变、边界及低重叠可能影响运动评价。对应诊断在 `results/{ring,era5}/tracking_robustness.csv`，极值/质心对照在 `metrics_by_target.csv`。

复现入口：`python scripts/run_experiments.py --dataset both`。完整方法见 [method.md](method.md)，实验结论见 [results.md](results.md)。
