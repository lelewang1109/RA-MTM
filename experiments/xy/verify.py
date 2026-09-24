"""Audit the canonical XY evidence; publish the report and scoped source hashes."""
from pathlib import Path
import sys,json,csv,hashlib,argparse
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from ramtm.error_budget import leaf_orders
from ramtm.reference_points import reconstruct_xy
from experiments.dual_reference.public_data import ep,execution_sources
OUT=ROOT/'results/xy'
def read(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dataset',choices=['ring','era5','both'],default='both');ap.add_argument('--verify',action='store_true');args=ap.parse_args()
    if args.verify:
        m=read(OUT/'manifest.json');bad=[k for k,v in m['sha256'].items() if not (ROOT/k).is_file() or digest(ROOT/k)!=v]
        if bad:raise RuntimeError('XY manifest mismatch: '+str(bad))
        print('PASS XY manifest',len(m['sha256']),'files');return
    datasets=['ring','era5'] if args.dataset=='both' else [args.dataset]
    baseline=read(ROOT/'experiments/dual_reference/baseline_snapshot.json')
    assert all(digest(ROOT/k)==v for k,v in baseline.items())
    audits=[]
    for name in datasets:
        folder=OUT/name;shared=read(folder/'shared_features.json');assert shared['reference_kind']=='extremum'
        assert read(folder/'status.json')['status']=='complete'
        assert read(folder/'protocol.json')['execution_sources']==execution_sources(), 'source changed since execution; rerun this dataset'
        records={};maps_checked=0;regressions={};max_gap=0.
        for method in ['TMTM','ST-MTM','X-only RA-MTM','Dual-Y','Centroid-X','Centroid-Y']:
            r=read(folder/(method+'_records.json'));records[method]=r['rows']
            maps=np.load(folder/(method+'_map.npz'))['values']
            assert maps.shape[1]==len(shared['centers']) and np.isfinite(maps).all()
            for t,row in enumerate(r['rows']):
                x,z,w=[np.asarray(row[k]) for k in ['x','z','w']];o=np.asarray(row['order'])
                assert all(np.isfinite(v).all() for v in [x,z,w])
                assert tuple(o) in leaf_orders(shared['hierarchies'][t])
                assert r['checks'][t]['topology_equal']
                if method not in ['TMTM','ST-MTM']:
                    p=r['records']['parameters'];q=np.asarray((shared['centers'] if method.startswith('Centroid') else shared['reference_points'])[t])
                    axis=0 if method in ['X-only RA-MTM','Centroid-X'] else 1
                    np.testing.assert_array_equal(row['reference'],q[:,axis])
                    assert row['feature_ids']==shared['tracks'][t]
                    np.testing.assert_allclose(w,p['width_scale']*np.asarray(shared['areas'][t]),atol=1e-12,rtol=0)
                    assert np.min(z-w/2)>=-1e-6 and np.max(z+w/2)<=p['canvas']+1e-6
                    assert np.all(abs(x-z)<=p['rho']*w/2+1e-6)
                    assert np.all(np.diff(z[o])-(w[o[:-1]]+w[o[1:]])/2>=p['gap']-1e-6)
                    assert np.max(abs(x-q[:,axis]))<=row['budget']+1e-6
                    assert abs(row['tau']-min(v['tau'] for v in row['lp_orders'] if v['tau'] is not None))<1e-8
                    assert {tuple(v['order']) for v in row['lp_orders']}==set(leaf_orders(shared['hierarchies'][t]))
                    assert row['global_gap_bound']<.01;max_gap=max(max_gap,row['global_gap_bound'])
                maps_checked+=1
            if method in ['TMTM','ST-MTM']:
                old=read(ROOT/'results/dual_public'/name/(method+'_records.json'))['rows']
                delta=max(float(np.max(abs(np.asarray(a['x'])-b['x']))) for a,b in zip(r['rows'],old))
                assert delta<1e-8;regressions[method]=delta
        reconstruct_xy(records['X-only RA-MTM'],records['Dual-Y'])
        reconstruct_xy(records['Centroid-X'],records['Centroid-Y'])
        audits.append(dict(dataset=name,status='pass',scalar_maps=maps_checked,max_global_gap=max_gap,baseline_anchor_change=regressions))
        ep.save(folder/'validation.json',audits[-1])
    # Report any completed datasets, but never silently certify an unverified one.
    names=datasets
    lines=['# XY RA-MTM 当前实验报告','',
        '当前主线：固定世界坐标中的叶极值参考（Ring 为最大值点，ERA5 join tree 为最小值点）；质心只定义 geometry，并作为参考点消融。',
        '完整定义见 [方法流程](XY_METHOD.md)，旧单轴报告见 [历史报告](history/SINGLE_AXIS_REPORT.md)。','',
        '## 协议','',
        '共享输入、树、支撑域与 correspondence；baseline 源码与历史一致。保留原参数 rho=.5、beta=4、gamma=1、lambda=.5、eta=.1，固定面积到宽度比例，不针对结果调参。',
        '每方法三次循环顺序重跑，表中运行时间为 layout/render/validation 中位数；Dual 时间含 X+Y。',
        '位置与运动以叶极值为真值，按固定方形域对角线归一化；全部方法也保留质心目标评价。单视图二维读出给予真实 birth-Y 固定的 oracle，不能称为原生二维恢复。另保存首帧二维 affine calibration 敏感性。',
        '方向角只在真实运动大于 0.001 倍固定轴范围时统计；近零预测方向按 pi 计入。边界 feature 及 IoU 分层见 tracking_robustness.csv。','',
        '## 所有结果','']
    for name in names:
        rows=list(csv.DictReader((OUT/name/'metrics.csv').open()))
        lines += ['### '+name.upper(),'','| 方法 | 2D位置 NRMSE | 轨迹 NMAE | 方向误差(rad) | 距离误差X / Y | 时间(s) |','|---|---:|---:|---:|---:|---:|']
        for r in rows:
            f=lambda k: f'{float(r[k]):.5f}' if r[k] else '—'
            lines.append('| '+' | '.join([r['method'],f('position_2d_nrmse'),f('trajectory_2d_nmae'),f('direction_error_radians'),f('distance_nrmse_x')+' / '+f('distance_nrmse_y'),f('runtime_seconds')])+' |')
        lines += ['',f'![{name} maps](../results/xy/{name}/comparison_maps.png)',f'![{name} targets and anchors](../results/xy/{name}/longest_tracks.png)','']
    lines += ['## 解释与限制','',
        '主要回答增加 Y 参考是否能表达第二个位置/运动分量，以及参考点语义是否符合任务。不得用改变真值后降低的误差声称全面优越。ST-MTM 的相对几何仍可能更好；tau、参考预算和 geometry error 必须一起阅读。',
        'Ring 前期支撑质心覆盖近全域，改用叶峰参考解决从域中心起步的语义问题。峰/谷不是环中心，也不是经过气象验证的气旋中心。网格极值跳跃、支撑变化和匹配歧义仍会污染运动。',
        '当前保留小树合法叶序枚举，不承诺大规模性能；只逐帧因果求解，不是全时空联合最优。两个视图不恢复完整二维标量场。',
        'ERA5 极值 X 参考第110帧触发原独立QP误差界0.01检查。求解器增加按证书触发的同目标二次精化，没有放宽约束或检查阈值。当前平台 NumPy matmul 警告保存在运行日志；输出 finite、约束与证书均单独检查。','',
        '## 图例与文件','',
        'comparison_maps：背景是标量值，不叠加身份点。longest_tracks：每列明确 track ID，虚线是目标参考点，实线是优化 anchor；三条轨迹按存活长度选择，不按表现筛选。ERA5 使用原 pressure_soft 红蓝卡，固定1013.25±35 hPa，非气候距平。',
        '`results/xy/{ring,era5}/metrics.csv` 为当前主表；`metrics_by_target.csv` 为两套真值；`*_records.json` 为完整证书；`protocol.json` 为参数与数据来源；`validation.json` 和根 `manifest.json` 为审计。','',
        '复现：`.venv/bin/python scripts/run_all.py`；仅验证已发布文件：`.venv/bin/python experiments/xy/verify.py --verify`。']
    (ROOT/'docs/EXPERIMENT_REPORT.md').write_text('\n'.join(lines)+'\n')
    ep.save(OUT/'validation.json',dict(status='pass',datasets=[read(OUT/n/'validation.json') for n in names]))
    files=[p for name in names for p in (OUT/name).rglob('*') if p.is_file() and p.name!='.DS_Store' and p.suffix!='.npz']
    files += [OUT/'validation.json']
    if (OUT/'README.md').exists():files.append(OUT/'README.md')
    if (OUT/'execution.txt').exists():files.append(OUT/'execution.txt')
    for folder in ['src/ramtm','experiments/xy','tests']:
        files += [p for p in (ROOT/folder).rglob('*') if p.suffix in ('.py','.json') and '__pycache__' not in p.parts]
    files += [ROOT/p for p in ['experiments/dual_reference/public_data.py','experiments/real_era5/run_experiment.py','experiments/ring/dataset.py','experiments/ring/source/SpreadingRingGeneration.py','experiments/dual_reference/baseline_snapshot.json','scripts/run_all.py','docs/XY_METHOD.md','docs/EXPERIMENT_REPORT.md','pyproject.toml']]
    ep.save(OUT/'manifest.json',dict(scope='Current extremum-reference XY public validation',datasets=names,sha256={str(p.relative_to(ROOT)):digest(p) for p in sorted(set(files))}))
    print('PASS XY',audits)
if __name__=='__main__':main()
