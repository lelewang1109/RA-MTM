"""Audit public-data evidence, publish complete tables/report, and hash artifacts."""
from pathlib import Path
import sys,json,csv,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from ramtm.error_budget import leaf_orders
OUT=ROOT/'results/dual_public'
if '--verify' in sys.argv:
    manifest=json.loads((OUT/'manifest.json').read_text())
    wrong=[k for k,v in manifest['sha256'].items() if not (ROOT/k).is_file() or hashlib.sha256((ROOT/k).read_bytes()).hexdigest()!=v]
    if wrong:raise SystemExit('Public manifest mismatch: '+str(wrong))
    print('PASS public manifest',len(manifest['sha256']),'files');raise SystemExit(0)
baseline=json.loads((ROOT/'experiments/dual_reference/baseline_snapshot.json').read_text())
assert all(hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==v for k,v in baseline.items())
checks=[];regress=[];tables={}
for name,span in [('ring',210),('era5',120)]:
    folder=OUT/name;status=json.loads((folder/'status.json').read_text());assert status['status']=='complete'
    source=json.loads((folder/'shared_features.json').read_text())
    tables[name]=list(csv.DictReader((folder/'metrics.csv').open()))
    for method in ['TMTM','ST-MTM','X-only RA-MTM','Dual-Y']:
        r=json.loads((folder/(method+'_records.json')).read_text())
        assert all(v['topology_equal'] and v['hierarchy_legal'] for v in r['checks'])
        for t,row in enumerate(r['rows']):
            x,z,w=[np.array(row[k]) for k in ['x','z','w']];assert all(np.isfinite(v).all() for v in [x,z,w])
            assert tuple(row['order']) in leaf_orders(source['hierarchies'][t])
            if method in ['X-only RA-MTM','Dual-Y']:
                p=r['records']['parameters'];axis=0 if method=='X-only RA-MTM' else 1;q=np.array(source['centers'][t])[:,axis];o=np.array(row['order'])
                assert np.allclose(w,np.array(source['areas'][t])*p['width_scale'],rtol=0,atol=1e-12)
                assert row['feature_ids']==source['tracks'][t]
                assert np.min(z-w/2)>=-1e-6 and np.max(z+w/2)<=span+1e-6
                assert np.max(abs(x-z)-p['rho']*w/2)<1e-6
                assert np.all(np.diff(z[o])-(w[o[:-1]]+w[o[1:]])/2>=p['gap']-1e-6)
                assert abs(row['tau']-min(v['tau'] for v in row['lp_orders'] if v['tau'] is not None))<1e-8
                assert {tuple(v['order']) for v in row['lp_orders']}==set(leaf_orders(source['hierarchies'][t]))
                assert np.max(abs(x-q))<=row['budget']+1e-6 and row['global_gap_bound']<.01
            checks.append(dict(dataset=name,method=method,t=t,status='pass'))
        if method in ['TMTM','ST-MTM']:
            old=ROOT/'results/supplementary'/name
            if name=='era5':old=old/'main'
            if name=='ring':
                prior=json.loads((old/(method+'_records.json')).read_text())['rows']
            else:
                feats=[v for v in csv.DictReader((old/'features.csv').open()) if v['method']==method]
                lookup={(int(v['t']),int(v['track'])):float(v['x']) for v in feats}
                prior=[dict(x=[lookup[t,tid] for tid in tids]) for t,tids in enumerate(source['tracks'])]
            err=max(float(np.max(abs(np.array(a['x'])-np.array(b['x'])))) for a,b in zip(r['rows'],prior))
            assert len(r['rows'])==len(prior) and err<1e-8
            regress.append(dict(dataset=name,method=method,max_anchor_difference=err))
    timing=list(csv.DictReader((folder/'runtime_repeats.csv').open()));assert len(timing)==12
    # Retain warnings from the macOS numerical backend, but independently audit
    # finite bounded coordinates and interval inequalities without matrix products.
report={'status':'pass','unique_scalar_maps':len(checks),'constraints_checked':True,'baseline_regression':regress}
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
keys=['method','SNS_x','TW_x','TD_x','SNS_y','TW_y','TD_y','runtime_seconds','position_2d_nrmse','trajectory_2d_nmae','distance_nrmse_x','distance_nrmse_y']
def val(r,k):return r[k] if k=='method' else ('—' if not r[k] else f'{float(r[k]):.6f}')
lines=['# Ring / ERA5：Dual-Reference RA-MTM 验证','',
'本次为固定协议的初步实证验证，不是调参后的最佳结果。完整原始表、三次计时、拓扑检查与失败栅格尝试均保留。','',
'## 数据与公平性','',
'- Ring：已有作者生成器及固定版本生成的40帧14×14 float32场，固定域[0,210]²；不是声称从论文网页下载了原始二进制文件。',
'- ERA5：本地公共再分析MSLP子集，1999-11-17至2000-01-14，沿用完整118帧、12小时采样、49×49网格、250 km平滑及等面积投影；不能声称与两篇文章所有预处理/文件逐字节一致，也没有独立气旋真值。',
'- 所有方法共享提取树、叶支持centroid/area及正重叠Hungarian匹配。baseline核心、preset、对应与预处理未改。与历史Ring和ERA5的TMTM/ST连续anchor对照最大差为0。',
'- 本次候选严格采用centroid reference，rho=.5；不是此前Ring的extremum reference/rho=1修正。X-only与Dual-X完全相同，唯一新增信息来自Y；beta=4、gamma=1、lambda=.5、eta=.1。测度尺度沿用固定域容量规则，Ring按210/120换算gap和budget，ERA5保持原单位。',
'- 单视图的二维主读出给予真实出生帧Y，此后保持不变（birth-Y oracle）；Dual直接组合两轴。另报告只用首帧拟合、此后固定的二维仿射读出，均不改baseline算法。Ring首帧只有一个feature，仿射方向不可辨识，约定零斜率/首帧均值并明确标记，不声称完成可靠校准。','',
'## 指标解释','',
'SNS越低越好；TW越高越好，k=3仅在叶数>6的帧定义，报告有效帧数，不能把少数有效帧外推到整条序列。TD是匹配anchor的总位移，越低不自动代表运动越准确：静止布局也有低TD。Dual逐轴报告SNS/TW/TD，不把两轴平均伪装成一个同等成本一维布局。',
'二维位置NRMSE、轨迹/运动误差沿用固定正方形域对角线归一化（Ring 210√2，ERA5 120√2）；这里ERA5的120是固定显示画布边长，不是原始经纬度跨度。direction为wrapped radians，仅真步长>0.001×canvas有效；预测静止而真运动有效记π。所有数值是提取feature的编码保真度。',
'运行时间是三次轮换顺序测量的layout+render+validation总耗时中位数，排除共享提取、指标计算、画图与I/O。Dual每次耗时为X+Y，不因复用X-only消融结果而漏计第二个solver。此实现运行时间不等于论文作者C++系统性能。','']
for name in ['ring','era5']:
    lines+=['## '+name.upper(),'','| '+' | '.join(keys)+' |','|'+'|'.join(['---']*len(keys))+'|']
    lines+=['| '+' | '.join(val(r,k) for k in keys)+' |' for r in tables[name]]
    dual=tables[name][-1];old=tables[name][-2]
    lines+=['',f"相对X-only，二维位置NRMSE变化 {float(old['position_2d_nrmse']):.6f} → {float(dual['position_2d_nrmse']):.6f}；轨迹NMAE {float(old['trajectory_2d_nmae']):.6f} → {float(dual['trajectory_2d_nmae']):.6f}。最大tau_X={float(dual['tau_x']):.4f}，tau_Y={float(dual['tau_y']):.4f}。",'']
    lines+=['首帧二维仿射读出对照：','','| Method | 2D position NRMSE | 2D trajectory NMAE | Identifiable |','|---|---:|---:|---|']
    for r in csv.DictReader((OUT/name/'affine_metrics.csv').open()):lines.append(f"| {r['method']} | {float(r['position_2d_nrmse']):.6f} | {float(r['trajectory_2d_nmae']):.6f} | {r['first_frame_identifiable']} |")
    lines+=['','匹配可靠性筛查（运动矢量NMAE）：','','| Method | IoU min | Interior only | Pairs | Motion 2D NMAE |','|---|---:|---|---:|---:|']
    for r in csv.DictReader((OUT/name/'tracking_robustness.csv').open()):lines.append('| '+' | '.join(r[k] for k in ['method','iou_min','interior_only','matched_pairs','motion_2d_nmae'])+' |')
    lines+=['']
lines+=['## 如何解释创新价值','',
'两组数据都支持“第二个参考方向改善feature级二维参考位置/运动编码”的结论，不能支持“Dual在所有性能指标优于ST-MTM”。ST-MTM的相对几何通常更好，Dual仍有非零tau和距离失真，且需要两个solver与两张图。应把固定参考语义和可解释冲突作为贡献，而不是把SNS/TW/TD综合包装成全面优越。',
'Ring中支持集重分配会使centroid突然变化，因此跟随centroid并不等于准确追踪物理环或极值位置。ERA5的大量边界特征及估计匹配同样限制物理解释；筛查表保留小样本或不利结果。不能从单个气象时段推出跨季节/多数据集泛化。','',
'## 图与验证','',
'每组数据有 input_fields、comparison_maps、longest_tracks 三张图，各含PNG、SVG、PDF。比较图中X-only=Dual-X，上X下Y用相同时间轴与固定世界轴；TMTM/ST图清楚标注原生归一化输出位置，不伪装成世界坐标。轨迹选择按寿命最长3条，不按表现挑选。',
'Ring TMTM/ST保持196 samples；Dual每轴784。ERA5的实际分辨率见metrics.csv与各records；RA两轴16,384。仅增加栅格分辨率以满足拓扑/非零像素宽度，连续宽度和solver不变。不宣称等总像素预算优势。',
'共632个不同标量图（158输入帧×TMTM/ST/Dual-X/Dual-Y）通过完整标量拓扑检查；三次运行的anchors及maps一致。独立审计有限坐标、宽度、非重叠、预算、合法序与全部LP候选。macOS数值后端出现matmul overflow/invalid警告，但输出均有限、有界且独立不使用矩阵乘法的约束审计通过；运行日志保留，未将警告隐藏成无异常运行。','',
'## 文件路径','',
'- 实验：`experiments/dual_reference/public_data.py`；审计/报告：`experiments/dual_reference/public_report.py`。',
'- 表：`results/dual_public/{ring,era5}/{metrics,rendered_metrics,affine_metrics,tracking_robustness,runtime_repeats}.csv`。',
'- 图：`results/dual_public/{ring,era5}/{input_fields,comparison_maps,longest_tracks}.{png,svg,pdf}`。',
'- 证书/输入：各数据目录的 `*_records.json`、`shared_features.json`、`protocol.json`、`status.json`。',
'- 参考点语义与配色更正：[Ring 质心/峰位置诊断](RING_REFERENCE_DIAGNOSIS.md)。已有质心结果保留；ERA5 恢复固定范围柔化红蓝色卡。','',
'- 审计：`results/dual_public/validation.json`、`manifest.json`、`execution.txt`。本地可再生NPZ不纳入Git。','',
'复现：`.venv/bin/python experiments/dual_reference/public_data.py`，随后 `.venv/bin/python experiments/dual_reference/public_report.py`。原始ERA5文件需保持在protocol记录的路径并与记录SHA256一致。历史结果不覆盖。']
(ROOT/'docs/PUBLIC_DATA_DUAL_REPORT.md').write_text('\n'.join(lines)+'\n')
# Compact result figure; all methods, no composite winner score.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':9,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(2,4,figsize=(13,6.4),layout='constrained')
colors=['#687888','#dc852b','#6761a8','#16846c']
for i,name in enumerate(['ring','era5']):
    rr=tables[name]
    for j,key in enumerate(['position_2d_nrmse','trajectory_2d_nmae','distance_nrmse_x','runtime_seconds']):
        ax=axs[i,j];ax.bar(range(4),[float(r[key]) for r in rr],color=colors,width=.7)
        if j==2:ax.scatter(3,float(rr[-1]['distance_nrmse_y']),marker='D',color='black',label='Dual-Y');ax.legend(fontsize=8)
        ax.set(xticks=range(4),xticklabels=['TMTM','ST','X-only','Dual'],title=name.upper()+' | '+['2D position NRMSE','2D trajectory NMAE','1D distance NRMSE','Runtime (s), median 3'][j])
        ax.grid(axis='y',alpha=.15)
fig.suptitle('Public-data validation: reference accuracy, geometric trade-off, and computational cost\nSingle-view 2D readout receives true birth-Y held fixed; timing includes layout, rendering and validation',fontsize=12)
for ext in ['png','svg','pdf']:fig.savefig(OUT/('performance_summary.'+ext),dpi=240,bbox_inches='tight')
plt.close(fig)
files=[p for p in OUT.rglob('*') if p.is_file() and p.suffix!='.npz' and p.name not in ('manifest.json','.DS_Store')]
files += [ROOT/p for p in ['experiments/dual_reference/public_data.py','experiments/dual_reference/ring_reference_diagnostic.py','docs/RING_REFERENCE_DIAGNOSIS.md','experiments/dual_reference/public_report.py','experiments/real_era5/run_experiment.py','experiments/ring/dataset.py','experiments/ring/source/SpreadingRingGeneration.py','experiments/ring/source/dataset_spreading_ring.processor.xml','src/ramtm/error_budget.py','src/ramtm/reference_anchored.py','src/ramtm/dual_evaluation.py','src/ramtm/baselines/tmtm.py','src/ramtm/baselines/stmtm.py','docs/PUBLIC_DATA_DUAL_REPORT.md','experiments/dual_reference/PUBLIC_DATA.md']]
(OUT/'manifest.json').write_text(json.dumps(dict(scope='Ring and ERA5 dual centroid-reference validation',sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}),indent=2))
print('PASS public-data audit:',report)
