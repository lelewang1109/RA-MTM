"""Difficult-field ablations and baseline robustness; no per-scene tuning."""
from dataclasses import replace
import time
import numpy as np
from run_experiment import make_scene,P,L,TABLES,RECORDS,save_json,write_csv,pack,metrics,run_b2,b2,solve_sequence
rows=[];baselines=[];direct=[];topology=[]
for name in ['hierarchy_change','crowding','advection_diffusion']:
    sc=make_scene(name)
    for mode in ['Full','NoTime','OldTime','NoReferencePenalty','ReferenceOnly','LegacyObjective','RelativeWidth','TightBudget']:
        p=P;measure=sc['area'].copy()
        if mode=='NoTime':p=replace(p,motion_weight=0.)
        if mode=='OldTime':p=replace(p,temporal_mode='stationary')
        if mode=='NoReferencePenalty':p=replace(p,reference_weight=0.)
        if mode=='ReferenceOnly':p=replace(p,geometry_weight=0.)
        if mode=='LegacyObjective':p=replace(p,reference_weight=0.,normalize_terms=False)
        if mode=='RelativeWidth':measure*=measure[0].sum()/measure.sum(1,keepdims=True)
        if mode=='TightBudget':p=replace(p,extra_budget=0.)
        start=time.perf_counter();d=solve_sequence(sc['centers'],measure,sc['hierarchies'],p);r=pack(d)
        r['tau']=np.array([v['tau'] for v in d]);r['budget']=np.array([v['budget'] for v in d])
        rows.append(metrics(sc,r,mode,time.perf_counter()-start))
        assert min(v['min_constraint_slack'] for v in d)>-1e-6
        assert max(v['qp_gap_bound'] for v in d)<.01
    for mode,weight,lam in [('base','uniform',0.),('temporal','uniform',2.),('temporal','inverse',.5)]:
        p=b2.LayoutParameters(weight,float(P.width_scale*sc['area'][0].sum()),.95,lam,L,0,mode=mode,min_spacing_delta=.01,optimizer_tolerance=1e-11)
        start=time.perf_counter();r=run_b2(sc,p)
        from run_experiment import signature
        for t,tree in enumerate(sc['trees']):
            values=r['scalar_map'][:,t];values=values[np.r_[True,abs(np.diff(values))>1e-12]]
            equal=signature(tree)==signature(values)
            topology.append(dict(scene=name,mode=mode,weight=weight,temporal_lambda=lam,t=t,topology_equal=equal))
            assert equal
        baselines.append(dict(mode=mode,weight=weight,temporal_lambda=lam,**metrics(sc,r,'ST-MTM',time.perf_counter()-start)))
    from ramtm.error_budget import leaf_orders
    for t,(c,a,h) in enumerate(zip(sc['centers'],sc['area'],sc['hierarchies'])):
        q=c[:,0];w=P.width_scale*a;o=tuple(np.argsort(q));ix=list(o)
        direct.append(dict(scene=name,t=t,hierarchy_legal=o in leaf_orders(h),
            nonoverlap=bool(np.all(np.diff(q[ix])-(w[ix[:-1]]+w[ix[1:]])/2>=P.gap-1e-9)),
            inside_canvas=bool(np.all(q-w/2>=0) and np.all(q+w/2<=P.canvas))))
write_csv(TABLES/'ablation.csv',rows)
write_csv(TABLES/'baseline_sensitivity.csv',baselines)
write_csv(TABLES/'direct_projection_validity.csv',direct)
write_csv(TABLES/'baseline_variant_topology.csv',topology)
print('Gaussian validation:',len(rows),'ablations;',len(baselines),'baseline settings;',len(direct),'direct projection probes')
