"""Audit saved dual evidence independently of solver constraint construction."""
from pathlib import Path
import sys,csv,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from ramtm.error_budget import leaf_orders
OUT=ROOT/'results/dual_reference'
tracks=list(csv.DictReader((OUT/'tables/trajectories.csv').open()))
lookup={(r['scene'],int(r['t']),int(r['feature'])):r for r in tracks}
count=0;max_gap=0.;max_raster=0.
for inp in sorted((OUT/'records').glob('*_input.json')):
 name=inp.name.removesuffix('_input.json');source=json.loads(inp.read_text())
 axis_rows=[]
 for axis in ['x','y']:
  data=json.loads((OUT/'records'/f'{name}_{axis}_view.json').read_text());p=data['parameters']
  assert len(data['certificates'])==len(source['hierarchies'])==len(source['feature_ids'])
  axis_rows.append(data['certificates'])
  for t,row in enumerate(data['certificates']):
   x,z,w,q=[np.array(row[k]) for k in ['x','z','w','reference']];order=row['order'];o=np.array(order)
   assert row['feature_ids']==source['feature_ids'][t]
   assert tuple(order) in leaf_orders(source['hierarchies'][t])
   assert {tuple(v['order']) for v in row['lp_orders']}==set(leaf_orders(source['hierarchies'][t]))
   assert abs(row['tau']-min(v['tau'] for v in row['lp_orders'] if v['tau'] is not None))<1e-8
   assert np.min(z-w/2)>=p['canvas_origin']-1e-6
   assert np.max(z+w/2)<=p['canvas_origin']+p['canvas']+1e-6
   assert np.all(z[o[1:]]-w[o[1:]]/2-(z[o[:-1]]+w[o[:-1]]/2)>=p['gap']-1e-6)
   assert np.all(abs(x-z)<=p['rho']*w/2+1e-6)
   assert np.max(abs(x-q))<=row['tau']+p['extra_budget']+1e-6
   assert row['global_gap_bound']<.01;max_gap=max(max_gap,row['global_gap_bound'])
   for i in range(len(x)):
    truth=lookup[name,t,i]
    assert abs(q[i]-float(truth['q_'+axis]))<1e-12
    assert abs(x[i]-float(truth[axis]))<1e-12
    assert abs(w[i]-p['width_scale']*float(truth['area']))<1e-12
   err=data['raster'][t]['anchor_error'];max_raster=max(max_raster,err)
   assert err<=120/2047/2+1e-10
   count+=1
 for x,y in zip(*axis_rows):assert x['feature_ids']==y['feature_ids']
assert count==1050
baseline=json.loads((ROOT/'experiments/dual_reference/baseline_snapshot.json').read_text())
assert all(hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==v for k,v in baseline.items())
checks=list(csv.DictReader((OUT/'tables/topology.csv').open()))
assert len(checks)==2625 and all(r['topology']=='True' and r['hierarchy']=='True' for r in checks)
report=dict(status='pass',axis_frames=count,scalar_checks=len(checks),max_global_qp_gap=max_gap,
            max_raster_anchor_error=max_raster,baseline_unchanged=True)
(OUT/'records/independent_audit.json').write_text(json.dumps(report,indent=2))
print('PASS independent audit',report)
