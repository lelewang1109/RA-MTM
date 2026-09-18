"""Deterministic parameter and centroid-perturbation checks for the budget model."""
import dataclasses, itertools, time
import numpy as np
from datasets import datasets, ROOT
from methods.error_budget import Parameters, solve_sequence
from run_initial import pack, metrics, write_csv, save_json, OUT
rows=[];noise=[]
scenes={s['name']:s for s in datasets()}
for name in ['translation','topology_change','crowding']:
    sc=scenes[name]
    for rho,budget,lam in itertools.product([0.,.5,1.],[0.,1.,3.],[0.,.5,2.]):
        print(name,rho,budget,lam,flush=True)
        p=Parameters(rho=rho,extra_budget=budget,motion_weight=lam)
        start=time.perf_counter();d=solve_sequence(sc['centers'],sc['area'],sc['hierarchies'],p);r=pack(d)
        r['tau']=np.array([f['tau'] for f in d]);r['budget']=np.array([f['budget'] for f in d])
        m=metrics(sc,r,'Budget',time.perf_counter()-start)
        assert m['max_budget_violation']<1e-6
        rows.append(dict(rho=rho,extra_budget=budget,motion_weight=lam,**m))
    base=pack(solve_sequence(sc['centers'],sc['area'],sc['hierarchies']))
    for sigma,seed in itertools.product([.01,.1,1.],range(5)):
        rng=np.random.default_rng(seed)
        perturbed=sc['centers']+rng.normal(0,sigma,sc['centers'].shape)
        d=solve_sequence(perturbed,sc['area'],sc['hierarchies']);r=pack(d)
        noise.append(dict(scene=name,sigma=sigma,seed=seed,max_input_change=float(np.max(abs(perturbed-sc['centers']))),
            max_anchor_change=float(np.max(abs(r['x']-base['x']))),
            changed_order_frames=sum(a!=b for a,b in zip(r['order'],base['order'])),
            max_budget_violation=max(float(np.max(abs(v['x']-c[:,0]))-v['budget']) for v,c in zip(d,perturbed))))
        assert noise[-1]['max_budget_violation']<1e-6
write_csv(OUT/'sensitivity.csv',rows);write_csv(OUT/'centroid_perturbation.csv',noise)
save_json(OUT/'sensitivity_summary.json',dict(parameter_runs=len(rows),perturbation_runs=len(noise),
    max_budget_violation=max(r['max_budget_violation'] for r in rows),
    max_noise_anchor_change=max(r['max_anchor_change'] for r in noise),
    changed_order_frames=sum(r['changed_order_frames'] for r in noise)))
print('sensitivity complete:',len(rows),'parameter runs,',len(noise),'perturbation runs')
