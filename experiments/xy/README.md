# 当前 XY 公共数据协议

主线定义：[XY_METHOD.md](../../docs/XY_METHOD.md)。

```sh
.venv/bin/python scripts/run_all.py --dataset both
.venv/bin/python experiments/xy/verify.py --verify
```

直接 `run.py` 只运行数据；`verify.py` 校验并生成统一报告与manifest。
两套数据均采用极值参考，质心只作 geometry 与消融；复用既有 solver 和 baseline。
固定原参数、三次重复，输出到 `results/xy`。只运行 Ring 可用 `--dataset ring`。
ERA5 文件必须预先放在 README 指定路径；缺失时明确失败，不合成替代数据。
图中无循环配色身份散点；三条示例轨迹按存活长度选择并明确ID，所有轨迹指标仍纳入表格。
