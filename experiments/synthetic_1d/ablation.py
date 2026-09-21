"""Mechanism ablations: retain the same hierarchy solver and LP budget protocol."""
import dataclasses,time
import numpy as np
from datasets import datasets
from ramtm.error_budget import Parameters,solve_sequence
from run_experiments import pack,metrics,write_csv,TABLES
rows=[];trajectories=[]
for sc in datasets():
    if sc['name'] not in ['translation','growth','collective_growth','translation_growth','hierarchy_conflict','topology_change','crowding']:continue
    for mode in ['Full','RelativeWidth','OldTime','NoTime','NoReferencePenalty','ReferenceOnly','LegacyObjective','TightBudget','LooseBudget']:
        p=Parameters();measure=sc['area'].copy().astype(float)
        if mode=='RelativeWidth':measure*=sc['area'][0].sum()/sc['area'].sum(axis=1,keepdims=True)
        if mode=='OldTime':p=dataclasses.replace(p,temporal_mode='stationary')
        if mode=='NoReferencePenalty':p=dataclasses.replace(p,reference_weight=0.)
        if mode=='ReferenceOnly':p=dataclasses.replace(p,geometry_weight=0.)
        if mode=='LegacyObjective':p=dataclasses.replace(p,reference_weight=0.,normalize_terms=False)
        if mode=='TightBudget':p=dataclasses.replace(p,extra_budget=0.)
        if mode=='LooseBudget':p=dataclasses.replace(p,extra_budget=120.)
        if mode=='NoTime':p=dataclasses.replace(p,motion_weight=0.)
        start=time.perf_counter();detail=solve_sequence(sc['centers'],measure,sc['hierarchies'],p);r=pack(detail)
        r['tau']=np.array([d['tau'] for d in detail]);r['budget']=np.array([d['budget'] for d in detail])
        rows.append(metrics(sc,r,mode,time.perf_counter()-start))
        for t in range(len(r['x'])):
            for i in range(r['x'].shape[1]):trajectories.append(dict(scene=sc['name'],mode=mode,t=t,feature=i,
                q=sc['centers'][t,i,0],x=r['x'][t,i],width=r['w'][t,i],true_measure=sc['area'][t,i]))
write_csv(TABLES/'ablation.csv',rows);write_csv(TABLES/'ablation_trajectories.csv',trajectories)
print('ablation complete:',len(rows),'runs')
