"""Mechanism ablations: retain the same hierarchy solver and LP budget protocol."""
import dataclasses,time
import numpy as np
from datasets import datasets
from methods.error_budget import Parameters,solve_sequence
from run_initial import pack,metrics,write_csv,OUT
rows=[];trajectories=[]
for sc in datasets():
    if sc['name'] not in ['translation','growth','collective_growth','translation_growth']:continue
    for mode in ['Full','RelativeWidth','OldTime','NoTime']:
        p=Parameters();measure=sc['area'].copy().astype(float)
        if mode=='RelativeWidth':measure*=sc['area'][0].sum()/sc['area'].sum(axis=1,keepdims=True)
        if mode=='OldTime':p=dataclasses.replace(p,temporal_mode='stationary')
        if mode=='NoTime':p=dataclasses.replace(p,motion_weight=0.)
        start=time.perf_counter();detail=solve_sequence(sc['centers'],measure,sc['hierarchies'],p);r=pack(detail)
        r['tau']=np.array([d['tau'] for d in detail]);r['budget']=np.array([d['budget'] for d in detail])
        rows.append(metrics(sc,r,mode,time.perf_counter()-start))
        for t in range(len(r['x'])):
            for i in range(r['x'].shape[1]):trajectories.append(dict(scene=sc['name'],mode=mode,t=t,feature=i,
                q=sc['centers'][t,i,0],x=r['x'][t,i],width=r['w'][t,i],true_measure=sc['area'][t,i]))
write_csv(OUT/'ablation.csv',rows);write_csv(OUT/'ablation_trajectories.csv',trajectories)
print('ablation complete:',len(rows),'runs')
