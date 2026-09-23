"""Additive dual-reference evidence; leaves all historical results untouched."""
from pathlib import Path
import sys,json,hashlib,time
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments/gaussian_2d')]
from run_experiment import make_scene,run_b1,run_b2,b2,pack,save_json,write_csv,signature,P
# The legacy imports use a module named datasets; load this local file explicitly.
import importlib.util
spec=importlib.util.spec_from_file_location('dual_datasets',Path(__file__).with_name('datasets.py'))
ds=importlib.util.module_from_spec(spec);spec.loader.exec_module(ds)
import numpy as np
from ramtm.error_budget import solve_sequence,solve_dual_reference_sequence,leaf_orders
from ramtm.reference_anchored import render_sequence
from ramtm.dual_evaluation import position_motion_metrics
from ramtm.evaluation import task_metrics
OUT=ROOT/'results/dual_reference'
for p in [OUT/'tables',OUT/'records',OUT/'arrays',OUT/'figures']:p.mkdir(parents=True,exist_ok=True)
CANONICAL=['translation','growth','translation_growth','local_growth','hierarchy_change','crowding','advection_diffusion']
PROTOCOL=[(n,0,65) for n in CANONICAL]+[(n,s,65) for n in ['hierarchy_change','crowding','advection_diffusion'] for s in [1,2,3]]+[('translation_growth',0,g) for g in [49,81]]

def geometry(c,x):
    d=np.linalg.norm(c[:,:,None,:]-c[:,None,:,:],axis=-1)
    return float(np.sqrt(np.sum((d-abs(x[:,:,None]-x[:,None,:]))**2)/np.sum(d*d)))

def main():
    start=time.time();rows=[];checks=[];frame_rows=[];tracks=[];rendered_rows=[]
    save_json(OUT/'records/protocol.json',dict(canonical=PROTOCOL,mechanisms=ds.CASES,parameters=asdict(P),
        baseline='existing Gaussian adapters and preset unchanged',minimum_motion=.12,
        readout='single-view primary: native calibrated x plus per-feature initial true y held fixed (oracle); not native 2-D output',
        affine='secondary: fit both coordinates to the single anchor at t=0 only, then freeze',
        fixed_domain=[120,120],scalar_raster=2048,failures='fail fast; never omit a declared case'))
    jobs=[(n,'mechanism',lambda n=n:ds.make_mechanism(n)) for n in ds.CASES]
    jobs += [(n+(f'_seed{s}' if s else '')+(f'_grid{g}' if g!=65 else ''),'canonical',lambda n=n,s=s,g=g:make_scene(n,s,g)) for n,s,g in PROTOCOL]
    for name,group,source in jobs:
        print('DUAL',name,flush=True);sc=source();c,a,h=sc['centers'],sc['area'],sc['hierarchies'];n=c.shape[1]
        identities=[list(range(n)) for _ in c]
        dual=solve_dual_reference_sequence(c,a,h,P,feature_ids=identities)
        # Independent legacy call checks compatibility, not merely the same array twice.
        old=solve_sequence(c,a,h,P)
        assert all(np.allclose(v['x'],w['x'],atol=1e-8) for v,w in zip(old,dual['x_view']))
        pars=b2.LayoutParameters('uniform',float(P.width_scale*a[0].sum()),.95,.5,2048,0,min_spacing_delta=.01,optimizer_tolerance=1e-11)
        runs={'TMTM':run_b1(sc),'ST-MTM':run_b2(sc,pars),'X-only RA-MTM':pack(old)}
        for axis,key in enumerate(['x_view','y_view']):
            detail=dual[key];r=pack(detail)
            scalar,skeletons,raster=render_sequence(sc['frames'],sc['ids'],detail,P.canvas,2048)
            r['pixel_x']=np.array([sk.anchors[[sk.ordering.index(i) for i in ids]]*120/2047 for sk,ids in zip(skeletons,sc['ids'])])
            r['scalar_map']=scalar;r['tau']=np.array([v['tau'] for v in detail]);r['budget']=np.array([v['budget'] for v in detail])
            runs['Dual-'+('X' if axis==0 else 'Y')]=r
            save_json(OUT/'records'/f'{name}_{key}.json',dict(certificates=detail,raster=raster,parameters=asdict(P)))
            for t,(row,sk) in enumerate(zip(detail,skeletons)):
                assert tuple(row['order']) in leaf_orders(h[t])
                assert np.allclose(row['w'],P.width_scale*a[t],rtol=0,atol=1e-12)
                assert abs(row['tau']-min(v['tau'] for v in row['lp_orders'] if v['tau'] is not None))<1e-8
                assert row['global_gap_bound']<.01 and row['min_constraint_slack']>-1e-6
                assert np.max(abs(row['x']-c[t,:,axis]))<=row['budget']+1e-6
                assert np.array_equal(sk.anchors,np.rint(row['x'][list(row['order'])]*(2047/120)).astype(int))
                frame_rows.append(dict(scene=name,t=t,axis='xy'[axis],tau=row['tau'],budget=row['budget'],achieved=float(np.max(abs(row['x']-c[t,:,axis]))),global_gap=row['global_gap_bound']))
        runs['X-only RA-MTM']['scalar_map']=runs['Dual-X']['scalar_map']
        runs['X-only RA-MTM']['pixel_x']=runs['Dual-X']['pixel_x']
        for t in range(len(c)):
            for i in range(n):
                tracks.append(dict(scene=name,t=t,feature=i,q_x=c[t,i,0],q_y=c[t,i,1],area=a[t,i],
                    x=runs['Dual-X']['x'][t,i],y=runs['Dual-Y']['x'][t,i],width_x=runs['Dual-X']['w'][t,i],width_y=runs['Dual-Y']['w'][t,i]))
        for method,r in runs.items():
            for t,tr in enumerate(sc['trees']):
                v=r['scalar_map'][:,t];v=v[np.r_[True,abs(np.diff(v))>1e-12]]
                ok=signature(v)==signature(tr)
                checks.append(dict(scene=name,method=method,t=t,topology=ok,hierarchy=tuple(r['order'][t]) in leaf_orders(h[t])))
                assert ok and checks[-1]['hierarchy']
        for method in ['TMTM','ST-MTM','X-only RA-MTM','Dual-Reference RA-MTM']:
            dual_method=method=='Dual-Reference RA-MTM';r=runs['Dual-X'] if dual_method else runs[method]
            pos=np.array(dual['positions']) if dual_method else np.stack([r['x'],np.broadcast_to(c[0,:,1],r['x'].shape)],axis=-1)
            primary=position_motion_metrics(c,pos,identities)
            grow=task_metrics(c,a,r['x'],r['w'],120)['growth_log_mae']
            base=dict(scene=name,group=group,method=method,readout='dual_native' if dual_method else 'initial_y_oracle',**primary,
                distance_x_nrmse=geometry(c,r['x']),distance_y_nrmse=geometry(c,runs['Dual-Y']['x']) if dual_method else None,
                growth_log_mae=grow,tau_x=float(max(v['tau'] for v in old)) if 'RA-MTM' in method else None,
                tau_y=float(max(v['tau'] for v in dual['y_view'])) if dual_method else None)
            rows.append(base)
            pixelpos=np.stack([runs['Dual-X']['pixel_x'],runs['Dual-Y']['pixel_x']],axis=-1) if dual_method else np.stack([r['pixel_x'],np.broadcast_to(c[0,:,1],r['x'].shape)],axis=-1)
            rendered_rows.append(dict(scene=name,method=method,readout=base['readout'],**position_motion_metrics(c,pixelpos,identities)))
            if not dual_method:
                design=np.c_[r['x'][0],np.ones(n)];coef=np.linalg.lstsq(design,c[0],rcond=None)[0]
                affine=r['x'][...,None]*coef[0]+coef[1]
                rows.append(dict(base,readout='first_frame_2d_affine',**position_motion_metrics(c,affine,identities)))
        payload=dict(centers=c,area=a,values=sc['values'],dual_positions=np.array(dual['positions']))
        for m,r in runs.items():
            for k in ['x','z','w','scalar_map','tau','budget']:
                if k in r:payload[m+'_'+k]=r[k]
        np.savez_compressed(OUT/'arrays'/f'{name}.npz',**payload)
        save_json(OUT/'records'/f'{name}_input.json',dict(hierarchies=h,feature_ids=identities,scalar_leaf_ids=sc['ids']))
        write_csv(OUT/'tables/trajectories.csv',tracks);write_csv(OUT/'tables/rendered_metrics.csv',rendered_rows)
        write_csv(OUT/'tables/metrics.csv',rows);write_csv(OUT/'tables/topology.csv',checks);write_csv(OUT/'tables/budgets.csv',frame_rows)
    before=json.loads((ROOT/'experiments/dual_reference/baseline_snapshot.json').read_text())
    assert all(hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==v for k,v in before.items())
    save_json(OUT/'records/validation.json',dict(status='complete',sequences=len(jobs),scalar_topology_checks=len(checks),
        all_passed=all(v['topology'] and v['hierarchy'] for v in checks),baseline_unchanged=before,seconds=time.time()-start))
    print('PASS dual evidence',len(jobs),len(checks),flush=True)

if __name__=='__main__':main()
