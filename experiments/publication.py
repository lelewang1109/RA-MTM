"""Build the paper evidence package from completed runs, then categorize artifacts.

This is the only publication step. It never optimizes layouts or selects seeds.
"""
from pathlib import Path
import sys,csv,json,shutil,platform
import numpy as np
import scipy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from ramtm.evaluation import task_metrics
OUT=ROOT/'results'
S=OUT/'synthetic_1d';G=OUT/'gaussian_2d'
if not S.exists():S=OUT/'supplementary/synthetic_1d'
if not G.exists():G=OUT/'supplementary/gaussian_2d'
METHODS=['TMTM','ST-MTM','RA-MTM']
COLORS=['#687888','#d67e25','#16846c']
KEYS=['reference_nmae','trajectory_nmae','growth_log_mae','distance_nrmse']
LABELS=['Reference error / domain','Trajectory error / domain','Absolute growth log error','2-D distance NRMSE']
def read(p):return list(csv.DictReader(p.open()))
def write(p,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys,lineterminator='\n');w.writeheader();w.writerows(rows)
def number(v):return float(v) if v not in ('',None) else np.nan
def normalized(rows):
    for r in rows:r['method']={'Budget':'RA-MTM','STMTM':'ST-MTM'}.get(r['method'],r['method'])
    return rows
syn=normalized(read(S/'tables/metrics.csv'));gau=read(G/'tables/metrics.csv')
canonical=[r for r in gau if r['seed']=='0' and r['grid']=='65']
for folder in ['main/figures','auxiliary','ablation','sensitivity','validity','supplementary']:(OUT/folder).mkdir(parents=True,exist_ok=True)
write(OUT/'main/metrics.csv',[{k:r[k] for k in ['scene','method','frames']+KEYS+['common_motion_nmae','total_growth_log_mae','reference_p95']} for r in canonical])
write(OUT/'main/synthetic_mechanisms.csv',[r for r in syn if r['scene'] in ['translation','growth','collective_growth','translation_growth','topology_change','crowding']])
write(OUT/'auxiliary/sanity_and_applicability.csv',[r for r in syn if r['scene'] in ['static','hierarchy_conflict','summary_only']])
# All realizations, including unfavorable results, stay in the supplement.
write(OUT/'supplementary/replicate_metrics.csv',[r for r in gau if r not in canonical])
abl=normalized(read(S/'tables/ablation.csv'))+read(G/'tables/ablation.csv')
write(OUT/'ablation/metrics.csv',abl)
shutil.copy2(S/'tables/ablation_trajectories.csv',OUT/'ablation/synthetic_trajectories.csv')
for src in [S,G]:
    for name in ['sensitivity','centroid_perturbation','baseline_sensitivity','objective_balance']:
        p=src/'tables'/(name+'.csv')
        if p.exists():shutil.copy2(p,OUT/'sensitivity'/(src.name+'_'+p.name))
    for name in ['topology_checks','boundary_checks','direct_projection_validity','lp_lower_bounds','raster_errors','baseline_variant_topology']:
        p=src/'tables'/(name+'.csv')
        if p.exists():shutil.copy2(p,OUT/'validity'/(src.name+'_'+p.name))
# Independent readout calibration sensitivity: give each baseline a best affine
# fit at t=0 only. All later frames remain unseen; native solvers are unchanged.
cal=[]
for suite,rows in [(S,syn),(G,gau)]:
    for r in rows:
        if r['method']=='RA-MTM':continue
        scene=r['scene'].removeprefix('gaussian2d_') if suite==G else r['scene']
        method=r['method']
        arr=np.load(suite/'arrays'/(scene+'_'+method+'.npz'))
        inp=np.load(ROOT/'data/generated'/suite.name/(scene+'.npz'))
        c=inp['centroids' if suite==G else 'centers'];a=inp['leaf_area' if suite==G else 'measure']
        x=arr['x'];q=c[0,:,0];u=x[0]-x[0].mean()
        scale=max(1e-12,float(np.dot(u,q-q.mean())/np.dot(u,u)))
        shift=float(q.mean()-scale*x[0].mean())
        distances=np.linalg.norm(c[:,:,None,:]-c[:,None,:,:],axis=-1)
        mapped=abs(scale*x[:,:,None]-scale*x[:,None,:])
        geometry=float(np.sqrt(np.sum((distances-mapped)**2)/np.sum(distances**2)))
        cal.append(dict(distance_nrmse=geometry,scene=r['scene'],method=r['method'],first_frame_scale=scale,
            **task_metrics(c,a,scale*x+shift,scale*arr['w'],120.)))
write(OUT/'sensitivity/first_frame_affine_calibration.csv',cal)
write(OUT/'main/calibration_robustness.csv',[r for r in cal if r['scene'] in {v['scene'] for v in canonical}]+[{k:r[k] for k in ['scene','method']+KEYS} for r in canonical if r['method']=='RA-MTM'])
# Seed-level paired differences. Frames/features are not independent replicates.
paired=[]
for family in ['hierarchy_change','crowding','advection_diffusion']:
    for baseline in METHODS[:2]:
        for key in KEYS:
            diffs=[]
            for seed in ['1','2','3']:
                rr=[r for r in gau if r['family']==family and r['seed']==seed]
                ra=next(r for r in rr if r['method']=='RA-MTM');ba=next(r for r in rr if r['method']==baseline)
                diffs.append(number(ra[key])-number(ba[key]))
            paired.append(dict(family=family,baseline=baseline,metric=key,realizations=3,
                median_difference=float(np.median(diffs)),min_difference=min(diffs),max_difference=max(diffs),
                ra_better=sum(v<-1e-6 for v in diffs),ties=sum(abs(v)<=1e-6 for v in diffs)))
write(OUT/'supplementary/paired_seed_differences.csv',paired)
# Compact native-vs-raster evidence, in identical physical units.
write(OUT/'validity/rendered_metrics.csv',[{k:v for k,v in r.items() if k in ['scene','method']+KEYS or k.startswith('rendered_')} for r in syn+gau])
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
families=list(dict.fromkeys(r['family'] for r in canonical))
fig,axs=plt.subplots(1,4,figsize=(16,5.2),layout='constrained',sharey=True)
for ax,key,label in zip(axs,KEYS,LABELS):
    for j,m in enumerate(METHODS):
        values=[number(next(r for r in canonical if r['family']==f and r['method']==m)[key]) for f in families]
        ax.scatter(values,np.arange(len(families))+.17*(j-1),s=36,color=COLORS[j],label=m)
    ax.set_xscale('symlog',linthresh=1e-5);ax.set_xlabel(label+' (lower is better)');ax.grid(axis='x',alpha=.2)
    ax.set_yticks(range(len(families)),[f.replace('_',' ') for f in families])
axs[0].invert_yaxis()
axs[0].legend(loc='lower left',fontsize=8)
fig.suptitle('Task fidelity and geometric tradeoff | all seven canonical 2-D fields\nNo composite score; symlog axes retain numerical zeros')
for ext in ['png','svg']:fig.savefig(OUT/'main/figures'/('evidence_overview.'+ext),dpi=180)
plt.close(fig)
for name in ['translation_growth','hierarchy_change','crowding','advection_diffusion']:
    shutil.copy2(G/'figures'/(name+'_comparison.png'),OUT/'main/figures'/(name+'.png'))
shutil.copy2(S/'figures/comparison.png',OUT/'main/figures/synthetic_mechanisms.png')
# Ablation figure includes optional temporal terms and reference/geometry tradeoff.
fig,axs=plt.subplots(1,3,figsize=(16,5.7),layout='constrained')
modes=['Full','NoTime','OldTime','NoReferencePenalty','ReferenceOnly','LegacyObjective','RelativeWidth','TightBudget']
for ax,name in zip(axs,['hierarchy_change','crowding','advection_diffusion']):
    rr=[r for r in abl if r['scene']=='gaussian2d_'+name]
    for j,key in enumerate(['reference_nmae','trajectory_nmae','distance_nrmse']):
        vals=[number(next(r for r in rr if r['method']==m)[key]) for m in modes]
        ax.scatter(vals,np.arange(len(modes))+.14*(j-1),s=28,label=key)
    ax.set_yticks(range(len(modes)),modes);ax.invert_yaxis();ax.set_xscale('symlog',linthresh=1e-5)
    ax.set(title=name.replace('_',' '),xlabel='Error (lower is better)');ax.set_xlim(0,1);ax.grid(alpha=.15)
axs[0].legend(fontsize=8)
fig.savefig(OUT/'ablation/difficult_fields.png',dpi=180);plt.close(fig)
# A directly includable LaTeX table, values are dimensionless, no winner hiding.
tex=['\\begin{tabular}{llrrrr}','Scenario & Method & Reference & Trajectory & Growth & Geometry \\\\','\\hline']
for r in canonical:
    tex.append(r['family'].replace('_','\\_')+' & '+r['method']+' & '+' & '.join(f'{number(r[k]):.4f}' for k in KEYS)+' \\\\')
tex.append('\\end{tabular}')
(OUT/'main/metrics.tex').write_text('\n'.join(tex)+'\n')
ver=json.loads((S/'records/verification.json').read_text());gv=json.loads((G/'records/validation.json').read_text())
checks=read(S/'tables/topology_checks.csv');direct=read(G/'tables/direct_projection_validity.csv')
assert all(r[k]=='True' for r in checks for k in ['tmtm_equal','stmtm_equal','ramtm_equal'])
assert gv['topology_passed']==gv['full_map_checks']
from ramtm.error_budget import solve_frame,Parameters
analytic=solve_frame(np.array([[40.,0.],[60.,15.]]),[20.,20.],(0,1),p=Parameters(extra_budget=10.))
assert np.allclose(analytic['x'],[38.,62.],atol=1e-5)
summary=dict(normalized_objective_analytic_check=True,baseline_variant_topology_checks=len(read(G/'tables/baseline_variant_topology.csv')),python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
    canonical_2d_scenarios=len(families),gaussian_runs=len(gau),gaussian_topology_checks=gv['full_map_checks'],
    synthetic_topology_checks=3*len(checks),regression_checks=len(ver['checks']),ablation_runs=len(abl),
    direct_projection_invalid=sum(any(r[k]!='True' for k in ['hierarchy_legal','nonoverlap','inside_canvas']) for r in direct))
(OUT/'validity/summary.json').write_text(json.dumps(summary,indent=2))
# Generate the numerical section only; prose protocol is maintained as one report.
table=['| 场景 | 方法 | 参考 NMAE | 轨迹 NMAE | 增长 log MAE | 距离 NRMSE |','|---|---|---:|---:|---:|---:|']
for r in canonical:table.append('| '+r['family']+' | '+r['method']+' | '+' | '.join(f'{number(r[k]):.5f}' for k in KEYS)+' |')
report=ROOT/'docs/EXPERIMENT_REPORT.md'
s=report.read_text();start=s.index('<!-- GENERATED RESULTS START -->');end=s.index('<!-- GENERATED RESULTS END -->')
generated='<!-- GENERATED RESULTS START -->\n\n'+f"本次正式运行：二维 {len(gau)} 组方法运行、{gv['full_map_checks']} 次完整图拓扑检查；一维 {3*len(checks)} 次三方法完整图拓扑检查；{len(ver['checks'])} 项解析/回归检查；{len(abl)} 组消融。所有拓扑检查通过。直接投影在 63 个二维困难场景帧中有 {summary['direct_projection_invalid']} 帧违反至少一项合法性要求。\n\n"+'\n'.join(table)+'\n\n'
s=s[:start]+generated+s[end:];report.write_text(s)
# Raw reproducibility records are explicitly supplementary, not another version.
if S.parent==OUT:shutil.move(str(S),str(OUT/'supplementary/synthetic_1d'))
if G.parent==OUT:shutil.move(str(G),str(OUT/'supplementary/gaussian_2d'))
(OUT/'README.md').write_text('''# Formal evidence package

One complete run only. `run_status.json` must say `complete`; verify with
`python scripts/manifest.py --verify`. Full reproduction: `./scripts/run_all.sh`.

- `main/`: seven canonical 2-D fields, 1-D mechanisms, paper tables and figures.
- `auxiliary/`: static/scope sanity checks; not baseline superiority evidence.
- `ablation/`: component tests on simple and difficult fields.
- `sensitivity/`: parameter, centroid perturbation, baseline settings and first-frame calibration.
- `validity/`: topology, feasibility, lower bounds and raster metric checks.
- `supplementary/`: every declared replicate/resolution, paired differences, and complete raw suite artifacts.

Raw suite tables duplicate the same current run for traceability; no historical
versions are retained here. Previous runs are local-only under `archive/`.
The sole experiment report is `docs/EXPERIMENT_REPORT.md`.
''')
print('Published evidence package:',summary,flush=True)
