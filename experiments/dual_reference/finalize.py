"""Publish every declared result; do not select winners or alter historical tables."""
from pathlib import Path
import csv,json,shutil
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results/dual_reference'
rows=list(csv.DictReader((OUT/'tables/metrics.csv').open()))
methods=['TMTM','ST-MTM','X-only RA-MTM','Dual-Reference RA-MTM']
names=list(dict.fromkeys(r['scene'] for r in rows))
primary=[r for r in rows if r['readout']!='first_frame_2d_affine']
assert len(names)==25 and len(primary)==100 and len(rows)==175
summary=[]
for protocol in ['initial_y_oracle','first_frame_2d_affine']:
 for method in methods[:-1]:
  for key in ['position_2d_nrmse','trajectory_2d_nmae']:
   dif=[]
   for name in names:
    b=next(r for r in rows if r['scene']==name and r['method']==method and r['readout']==protocol)
    d=next(r for r in primary if r['scene']==name and r['method']==methods[-1])
    dif.append(float(d[key])-float(b[key]))
   summary.append(dict(readout=protocol,baseline=method,metric=key,dual_lower=sum(v<-1e-6 for v in dif),tie=sum(abs(v)<=1e-6 for v in dif),dual_higher=sum(v>1e-6 for v in dif)))
with (OUT/'tables/all_case_comparison.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(summary[0]),lineterminator="\n");w.writeheader();w.writerows(summary)
keys=['scene','method','position_2d_nrmse','trajectory_2d_nmae','motion_magnitude_2d_nmae','direction_error_radians','distance_x_nrmse','distance_y_nrmse','growth_log_mae','tau_x','tau_y']
labels=['Scene','Method','Position 2D','Trajectory 2D','Magnitude 2D','Direction rad','Geometry X','Geometry Y','Growth','Max tau X','Max tau Y']
def fmt(v):return '--' if v=='' else f'{float(v):.6f}'
lines=['# All 25 declared cases','Single-view 2D: native calibrated X + true initial Y held fixed (oracle); Dual: native anchors. Geometry uses original 2D distances.','| '+' | '.join(labels)+' |','|'+'|'.join(['---']*len(keys))+'|']
for r in primary:lines.append('| '+' | '.join(r[k] if k in ['scene','method'] else fmt(r[k]) for k in keys)+' |')
(OUT/'tables/main_results.md').write_text('\n\n'.join(lines[:2])+'\n\n'+'\n'.join(lines[2:])+'\n')
# ASCII LaTeX, literal backslashes, no dependence on TeX for generation.
b=chr(92);tex=[b+'begin{tabular}{llrrrr}', 'Scene & Method & Position & Trajectory & Geometry X & Geometry Y '+b*2,b+'hline']
for r in primary:
 tex.append(' & '.join([r['scene'].replace('_',b+'_'),r['method']]+[fmt(r[k]) for k in ['position_2d_nrmse','trajectory_2d_nmae','distance_x_nrmse','distance_y_nrmse']])+' '+b*2)
tex.append(b+'end{tabular}');(OUT/'tables/main_results.tex').write_text('\n'.join(tex)+'\n')
# Optional direct historical regression, explicitly records availability.
old=ROOT/'results/supplementary/gaussian_2d/arrays';reg=[]
for p in old.glob('*_RA-MTM.npz'):
 name=p.name.removesuffix('_RA-MTM.npz')
 if not (OUT/'arrays'/(name+'.npz')).exists():continue
 d=np.load(OUT/'arrays'/(name+'.npz'))
 for m,k in [('TMTM','TMTM'),('ST-MTM','ST-MTM'),('RA-MTM','X-only RA-MTM')]:
  prior=np.load(old/(name+'_'+m+'.npz'));error=float(np.max(abs(prior['x']-d[k+'_x'])))
  assert error<1e-7
  reg.append(dict(scene=name,method=m,max_anchor_difference=error))
if reg:(OUT/'records/canonical_regression.json').write_text(json.dumps(reg,indent=2))
for p in [ROOT/'results/synthetic_1d/records/verification.json',ROOT/'results/supplementary/synthetic_1d/records/verification.json']:
 if p.exists():shutil.copyfile(p,OUT/'records/legacy_verification.json');break
print('PASS tables: 25 sequences, 175 rows; historical comparisons available:',len(reg))
