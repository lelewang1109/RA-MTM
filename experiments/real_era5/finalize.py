"""Assemble ERA5 publication evidence from completed outputs, without selecting runs."""
from pathlib import Path
import csv,json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results';RAW=OUT/'supplementary/era5'
def read(p):return list(csv.DictReader(p.open()))
def write(p,rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def native(rows):return [r for r in rows if r['calibration']=='native' and r['rendered']=='False']
def f(r,k):return float(r[k])
for stage in ['main','sensitivity']:
    assert json.loads((RAW/('status_'+stage+'.json')).read_text())['status']=='complete',stage
main=read(OUT/'main/era5_metrics.csv');abl=native(read(OUT/'ablation/era5_core.csv'));sens=read(OUT/'sensitivity/era5_protocol.csv')
checks=sum([read(OUT/'validity'/('era5_'+s+'.csv')) for s in ['main','ablation','sensitivity']],[])
assert all(r['topology_equal']=='True' and r['hierarchy_legal']=='True' and float(r['max_overlap'])<=1e-5 for r in checks)
assert all(r['collapsed_intervals']=='0' for r in main+sens)
protocol=json.loads((RAW/'main/protocol.json').read_text());src=json.loads((RAW/'source.json').read_text())
scene_diagnostics=read(OUT/'auxiliary/era5_scene_diagnostics.csv')
methods=['TMTM','ST-MTM','RA-MTM'];keys=['reference_nmae','motion_step_nmae','trajectory_nmae','growth_step_log_mae','distance_nrmse']
selected=[r for r in main if r['rendered']=='False' and (r['calibration']=='native' or r['method']!='RA-MTM')]
tex=[r'\begin{tabular}{llrrrrr}',r'Calibration & Method & Reference & Step motion & Trajectory & Growth & Geometry \\',r'\hline']
for row in selected:tex.append(row['calibration'].replace('_',r'\_')+' & '+row['method']+' & '+' & '.join(f'{f(row,k):.5f}' for k in keys)+r' \\')
tex.append(r'\end{tabular}');(OUT/'main/era5_metrics.tex').write_text('\n'.join(tex)+'\n')
# All eight declared input/direction variants: report comparisons, never only wins.
summary=[]
for cal in ['native','first_frame_affine']:
    cases=sorted({r['run'] for r in sens if r['method']=='TMTM'})
    for baseline in methods[:2]:
        for key in keys:
            delta=[]
            for case in cases:
                rr=[r for r in sens if r['run']==case and r['calibration']==cal and r['rendered']=='False']
                a=next(r for r in rr if r['method']=='RA-MTM');b=next(r for r in rr if r['method']==baseline)
                delta.append(f(a,key)-f(b,key))
            summary.append(dict(calibration=cal,baseline=baseline,metric=key,protocols=len(cases),ra_better=sum(d<-1e-5 for d in delta),ties=sum(abs(d)<=1e-5 for d in delta),ra_worse=sum(d>1e-5 for d in delta),worst_ra_minus_baseline=max(delta)))
write(OUT/'sensitivity/era5_stability_summary.csv',summary)
# Parameter and ablation trade-offs; units and variants are kept separate.
fig,ax=plt.subplots(1,3,figsize=(15,4.5),layout='constrained')
for r in abl:
    ax[0].scatter(f(r,'reference_nmae'),f(r,'distance_nrmse'),s=60)
    offset={'main':(-40,60),'RelativeWidth':(-125,30),'NoTime':(-58,12),'ReferenceOnly':(8,-10)}[r['run']]
    ax[0].annotate('Full' if r['run']=='main' else r['run'],(f(r,'reference_nmae'),f(r,'distance_nrmse')),xytext=offset,textcoords='offset points',fontsize=8,arrowprops=dict(arrowstyle='-',color='.6',lw=.7))
ax[0].margins(.12)
ax[0].set(xlabel='Reference NMAE',ylabel='Geometry NRMSE',title='12-hour full-period ablations')
params=[r for r in native(sens) if r['method']=='RA-MTM' and r['run'] in ['daily','beta1','beta8','budget0','budget4']]
for r in params:
    ax[1].scatter(f(r,'reference_nmae'),f(r,'distance_nrmse'),s=60)
    label={'daily':'Default (beta=4, budget=1)'}.get(r['run'],r['run'])
    ax[1].annotate(label,(f(r,'reference_nmae'),f(r,'distance_nrmse')),xytext=(-36,8) if r['run'] in ['beta1','budget4'] else (4,5),textcoords='offset points',fontsize=8)
ax[1].margins(.12)
ax[1].set(xlabel='Reference NMAE',ylabel='Geometry NRMSE',title='Daily full-period parameter trade-off')
for m in methods:
    rows=[r for r in native(sens) if r['method']==m and r['run'] in ['daily','direction45','direction90']];rows.sort(key=lambda r:['daily','direction45','direction90'].index(r['run']))
    ax[2].plot([0,45,90],[f(r,'reference_nmae') for r in rows],marker='o',label=m)
ax[2].set(xlabel='Reference direction (degrees)',ylabel='Reference NMAE',title='Fixed area and distance units');ax[2].legend()
fig.savefig(OUT/'sensitivity/era5_tradeoffs.png',dpi=180);plt.close(fig)
# Longest extracted tracks, selected by lifetime only. No meteorological IDs.
features=read(RAW/'main/features.csv');counts={}
for r in features:
    if r['method']=='RA-MTM':counts[r['track']]=counts.get(r['track'],0)+1
chosen=sorted(counts,key=lambda k:(-counts[k],int(k)))[:3]
fig,axes=plt.subplots(3,2,figsize=(12,10),layout='constrained')
for i,tid in enumerate(chosen):
    truth=sorted([r for r in features if r['track']==tid and r['method']=='RA-MTM'],key=lambda r:int(r['t']))
    days=np.array([int(r['t']) for r in truth])*.5
    axes[i,0].plot(days,[f(r,'q') for r in truth],color='black',lw=2,label='Derived reference')
    axes[i,1].plot(days,[f(r,'area')/f(truth[0],'area') for r in truth],color='black',lw=2,label='Derived leaf area')
    for m in methods:
        rr=sorted([r for r in features if r['track']==tid and r['method']==m],key=lambda r:int(r['t']))
        axes[i,0].plot(days,[f(r,'x') for r in rr],label=m)
        axes[i,1].plot(days,[f(r,'width')/f(rr[0],'width') for r in rr],label=m,ls='--')
    axes[i,0].set(title=f'Extracted track {tid} ({len(truth)} frames)',xlabel='Days since 1999-11-17',ylabel='Fixed reference coordinate')
    axes[i,1].set(xlabel='Days since 1999-11-17',ylabel='Size / track-birth size',yscale='log')
axes[0,0].legend(fontsize=8);axes[0,1].legend(fontsize=8)
fig.suptitle('Three longest overlap-linked leaf tracks — no selection by method performance')
fig.savefig(OUT/'main/figures/era5_tracks.png',dpi=180);plt.close(fig)
validation=dict(full_map_checks=len(checks),topology_passed=len(checks),nominal_topology_failures=sum(r['nominal_topology_failed']=='True' for r in checks),nominal_collapsed_width_frames=sum(r['nominal_width_collapsed']=='True' for r in checks),maximum_raster_length=max(int(r['raster_length']) for r in checks),maximum_root_level_error_hPa=max((float(r['root_level_error_hPa']) for r in checks if 'root_level_error_hPa' in r),default=None),source_sha256=src['sha256'],main_protocol=protocol)
(OUT/'validity/era5_summary.json').write_text(json.dumps(validation,indent=2))
ra=next(r for r in native(main) if r['method']=='RA-MTM');nt=next(r for r in abl if r['run']=='NoTime')
tracking=read(OUT/'auxiliary/era5_tracking_robustness.csv');interior=next(r for r in tracking if r['method']=='RA-MTM' and r['iou_min']=='0.0' and r['interior_only']=='True')
text='''\n## 9. ERA5 真实再分析案例（完整周期）\n\n'''
text+=f"输入为 ERA5 MSLP 再分析场（并非独立气旋观测真值），原始范围 {src['first']} 至 {src['last']}，形状 {src['shape']}，全文件缺测 {src['missing_values']}。完整 SHA-256 与 NetCDF 属性见 `supplementary/era5/source.json`；数据说明来自 [ECMWF](https://www.ecmwf.int/en/forecasts/dataset/ecmwf-reanalysis-v5)。保留原始 Pa 数据，以 hPa 处理，使用全部空间范围；主实验从 00 UTC 起每 12 小时采样，共 {protocol['frames']} 帧，不筛日期或气象事件。末次主实验为 2000-01-14 12 UTC；未声称逐小时运行全部 1,416 帧。\n\n"
text+='''共同预处理：球面 Lambert 圆柱等面积投影（R=6371 km、标准纬线52.5°），49×49等面积单元中心双线性插值，投影空间250 km高斯平滑、reflect边界。树是平滑场的join tree，不做持久性取消、逐帧选峰或按结果剪枝。面积为叶端点及相邻弧常规顶点的单元数×单元面积，不是完整气旋流域，更不是气压质量。质心、面积和层级来自同一个提取结果；真实数据不存在已知对象身份。空间统一按域对角线缩放到120，绕域中心旋转，所有方向保持距离与面积单位不变。平滑改变量逐帧保存于 `preprocessing.csv`，这些特征不代表未平滑原场的全部结构。\n\n三种方法使用相同输入。TMTM保持网格样本双射和子树连续性；ST-MTM原生重排阈值0.95、λ=0.5、均匀距离权重、首帧固定K；RA-MTM使用既有β=4、λ=0.5、Δ=1，固定 c=60/120²。该面积比例对全域容量给出保守上界，不由某帧输出调节。baseline只有首帧反射/平移，另报告首帧最小二乘仿射校准，不使用未来真值。两种baseline仍是论文方法的Python复现，未宣称作者官方实现。\n\n动态对应统一使用相邻帧叶支持集交集计数的Hungarian一对一最大匹配，零交集不匹配。出生特征不施加时间项；时间残差仅在匹配集M上求均值：λ/|M| Σ[(xᵢ−xⱼ,prev)−(qᵢ−qⱼ,prev)]²，空集取0。该扩展没有改变原固定身份序列的目标。位置误差对全部特征求均值；单步运动为匹配对的|Δx−Δq|/120；轨迹为各轨道出生时残差到当前残差的变化/120；面积增长为匹配对|log(wₜ/wₜ₋₁)−log(Aₜ/Aₜ₋₁)|。总面积变化包含出生和消失。它们验证提取特征的编码保真度，不能表述为气旋预报或物理运动识别准确率。\n\n'''
text+=f"主实验包含 {protocol['total_features']} 个特征实例、{protocol['tracks']} 条提取轨道、{protocol['matched_pairs']} 个匹配对，叶数 {protocol['leaves_min']}–{protocol['leaves_max']}。{protocol['boundary_features']} 个实例接触空间边界；严格排除两帧任一边界接触后仅剩 {interior['matched_pairs']} 个匹配对。内部筛查对单步指标要求匹配的两端均不接触边界，累计轨迹仍参照原轨道出生帧，不表示整条气象轨道都在域内。主表全部保留，并补充IoU≥0、0.1、0.25、0.5和内部特征分析；不可把大量边界特征解释为完整气旋。\n\n"
text+=f"其中 {sum(f(r,'tau')>1e-6 for r in scene_diagnostics)} 帧存在非零最小参考冲突，最大τ*={max(f(r,'tau') for r in scene_diagnostics):.4f}。相邻帧共有至少3个匹配叶时，对共同叶诱导子树比较簇集合：{sum(r['induced_hierarchy_changed']=='True' for r in scene_diagnostics)}/{sum(r['induced_hierarchy_changed']!='' for r in scene_diagnostics)} 个可评价转移发生层级变化。出生/消失、直接参考排序合法性、投影区间冲突对数和QP证书逐帧记录于 `auxiliary/era5_scene_diagnostics.csv`。\n\n"
text+='| 校准 | 方法 | 位置 NMAE ↓ | 单步运动 NMAE ↓ | 轨迹 NMAE ↓ | 增长 log MAE ↓ | 几何 NRMSE ↓ |\n|---|---|---:|---:|---:|---:|---:|\n'
for row in selected:text+='| '+row['calibration']+' | '+row['method']+' | '+' | '.join(f'{f(row,k):.6f}' for k in keys)+' |\n'
text+=f"\n时间项相对NoTime的单步运动误差下降 {(1-f(ra,'motion_step_nmae')/f(nt,'motion_step_nmae'))*100:.2f}%，仍定位为残差正则项。ReferenceOnly与RelativeWidth消融和每日β=1/4/8、Δ=0/1/4扫描公开展示参考、几何及面积目标的取舍，不用单个最优数替换默认方法。TMTM的绝对面积增长基本保留，RA-MTM不能据此宣称优于TMTM的增长编码；ST-MTM的原生几何更好。强校准单步运动结果接近，需逐项比较，不能声称全面或稳定显著领先。\n\n"
text+='''稳定性按固定7日块汇总（9块，末块较短），先在帧内平均、再在块内平均、最后等权汇总各块，并给出配对块bootstrap区间；它不是主表特征加权均值的置信区间，未把帧/特征当作独立重复。该区间是本段序列的探索性波动描述，不是气候总体置信保证。敏感性全部覆盖完整59日：6/12/24小时，200/250/300 km平滑，41/49/61网格，0/45/90°参考方向；其中输入和方向对照有8组，每组重跑全部baseline，参数组与每日默认组比较。采样间隔不同的单步指标不跨组直接排优劣。主张仅限这一真实再分析区域与时段，不能替代多数据集/多季节验证。\n\n| 校准 | baseline | 指标 | RA胜 / 平 / 负（8个输入或方向协议） |\n|---|---|---|---|\n'''
for row in summary:
    if row['metric'] in ['reference_nmae','motion_step_nmae','trajectory_nmae','growth_step_log_mae']:
        text+=f"| {row['calibration']} | {row['baseline']} | {row['metric']} | {row['ra_better']} / {row['ties']} / {row['ra_worse']} |\n"
text+=f"\n共完成 {len(checks)} 个标量地图叶极值—分支合并事件及层级检查，全部通过（合并标量精度1e-7 hPa，收缩单支根延伸，逐图另记根标量误差；不声称所有标量样本或根延伸长度完全重建）。名义8192像素下共有 {validation['nominal_topology_failures']} 个拓扑失败、{validation['nominal_collapsed_width_frames']} 个零宽帧（含消融/参数重复）；均保留在records和validity中。采用固定倍增策略，仅增加栅格分辨率直至拓扑正确且无零宽，最大 {validation['maximum_raster_length']}；连续坐标、baseline优化和面积不变。空常规顶点弧的插值已修正为使用该弧自身端点，避免整条路径插值跨越相邻弧数值范围引入伪极值；ST-MTM与RA-MTM共同使用同一修正。TMTM保持原网格样本数长度。主指标来自连续表示；像素指标与各自预算独立报告，不能作等像素预算的感知优势结论。全部候选LP/QP、匹配与栅格尝试可审计。\n\n"
text+='''投稿建议：主文放 `main/era5_metrics.tex`（含强校准）、`main/figures/era5_evidence.png`、必要时放 `era5_tracks.png`（按轨道寿命选最长3条，不按效果选例）。其余方向/参数取舍图、9块统计、IoU/边界筛查、预处理改变量、完整记录放补充材料。该案例补上真实复杂场、可变叶数和非已知对应；仍不支持独立气象目标真值、匹配正确性保证、大规模树复杂度或普遍几何最优。\n'''
report=ROOT/'docs/EXPERIMENT_REPORT.md';content=report.read_text();start='<!-- GENERATED ERA5 START -->';end='<!-- GENERATED ERA5 END -->';block=start+'\n'+text+'\n'+end
if start in content:content=content[:content.index(start)]+block+content[content.index(end)+len(end):]
else:content+='\n'+block+'\n'
report.write_text(content)
readme=OUT/'README.md';s=readme.read_text();marker='<!-- ERA5 -->'
if marker in s:s=s[:s.index(marker)]
s+='\n'+marker+'\nERA5 full-period evidence: `main/era5_metrics.csv`, `main/era5_metrics.tex`, `main/figures/era5_evidence.png`, and `main/figures/era5_tracks.png`. Ablation, sensitivity, auxiliary and validity files use the `era5_` prefix; all protocols, source hash, matching and solver records are in `supplementary/era5/`. See report §9 for boundaries and raster budgets.\n';readme.write_text(s)
print('PASS ERA5 publication assembly:',len(checks),'maps')
