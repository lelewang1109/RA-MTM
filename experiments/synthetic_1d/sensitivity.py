"""Deterministic parameter and centroid-perturbation checks for the budget model."""
import dataclasses, itertools, time
import numpy as np
from datasets import datasets, ROOT
from ramtm.error_budget import Parameters, solve_sequence
from run_experiments import pack, metrics, write_csv, save_json, TABLES, RECORDS
rows=[];noise=[]
scenes={s['name']:s for s in datasets()}
for name in ['translation','topology_change','crowding']:
    sc=scenes[name]
    for rho,budget,lam in itertools.product([0.,.5,1.],[0.,1.,3.],[0.,.5,2.]):
        print(name,rho,budget,lam,flush=True)
        p=Parameters(rho=rho,extra_budget=budget,motion_weight=lam)
        start=time.perf_counter();d=solve_sequence(sc['centers'],sc['area'],sc['hierarchies'],p);r=pack(d)
        r['tau']=np.array([f['tau'] for f in d]);r['budget']=np.array([f['budget'] for f in d])
        m=metrics(sc,r,'RA-MTM',time.perf_counter()-start)
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
write_csv(TABLES/'sensitivity.csv',rows);write_csv(TABLES/'centroid_perturbation.csv',noise)
save_json(RECORDS/'sensitivity_summary.json',dict(parameter_runs=len(rows),perturbation_runs=len(noise),
    max_budget_violation=max(r['max_budget_violation'] for r in rows),
    max_noise_anchor_change=max(r['max_anchor_change'] for r in noise),
    changed_order_frames=sum(r['changed_order_frames'] for r in noise)))
print('sensitivity complete:',len(rows),'parameter runs,',len(noise),'perturbation runs')

# Baseline settings are varied without modifying its objectives or constraints.
from run_experiments import run_b2, b2
baseline=[]
for name in ['translation','translation_growth','topology_change','crowding']:
    sc=scenes[name]
    for mode,weight,lam in [('base','uniform',0.),('temporal','uniform',.5),('temporal','uniform',2.),('temporal','inverse',.5)]:
        p=b2.LayoutParameters(weight,float(.06*sc['area'][0].sum()),.95,lam,2048,0,mode=mode,min_spacing_delta=.01,optimizer_tolerance=1e-11)
        start=time.perf_counter();r=run_b2(sc,p)
        baseline.append(dict(mode=mode,weight=weight,temporal_lambda=lam,**metrics(sc,r,'ST-MTM',time.perf_counter()-start)))
write_csv(TABLES/'baseline_sensitivity.csv',baseline)
# Objective balance: one-factor sweep, all other parameters fixed.
balance=[]
for name in ['topology_change','crowding']:
    sc=scenes[name]
    for weight in [.25,1.,4.]:
        p=Parameters(reference_weight=weight)
        start=time.perf_counter();d=solve_sequence(sc['centers'],sc['area'],sc['hierarchies'],p);r=pack(d)
        r['tau']=np.array([v['tau'] for v in d]);r['budget']=np.array([v['budget'] for v in d])
        balance.append(dict(reference_weight=weight,**metrics(sc,r,'RA-MTM',time.perf_counter()-start)))
write_csv(TABLES/'objective_balance.csv',balance)
