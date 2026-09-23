"""Regression checks for matched temporal terms and dynamic-frame metrics."""
import sys
from pathlib import Path
import numpy as np
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
import ramtm.error_budget as eb
from run_experiment import extract, evaluate, save, signature, b1
from ramtm.baselines import stmtm as b2
from types import SimpleNamespace
records=[]
def check(name,ok):
    assert ok,name
    records.append(dict(check=name,status='pass'))
for sign in [1,-1]:
    frame=SimpleNamespace(values=sign*np.array([0.,1.,100.,2.]))
    arcs=[b2.TreeArc(0,0,1,np.array([],int)),b2.TreeArc(1,1,2,np.array([3]))]
    for upward in [True,False]:
        v=b2._sample_path(frame,arcs,20,upward=upward,fallback_start=0. if upward else sign*100.,fallback_end=sign*100. if upward else 0.)
        check(f'empty arc monotone sign={sign}, upward={upward}',np.all(sign*(1 if upward else -1)*np.diff(v)>=0))
for seed in range(5):
    v=np.random.default_rng(seed).normal(size=201)
    check(f'monotone contraction preserves tree {seed}',signature(v)==signature(b1.build_augmented_merge_tree(v,'join')))
c=np.array([[25.,20.],[55.,60.],[85.,30.]])
a=np.array([120.,200.,160.]);h=((0,1),2);p=eb.Parameters()
r=eb.solve_frame(c,a,h)
v=eb.solve_frame(c+1,a,h,r['x'],c[:,0],p)
u=eb.solve_frame(c+1,a,h,r['x'],c[:,0],p,matched=[True]*3)
check('all-matched API backward compatibility',np.allclose(u['x'],v['x'],atol=1e-10) and abs(u['objective']-v['objective'])<1e-10)
b=eb.solve_frame(c,a,h,np.full(3,np.nan),np.full(3,np.nan),p,matched=[False]*3)
check('births have no artificial temporal target',np.allclose(b['x'],r['x'],atol=1e-10))
# Check analytical gradients against finite differences inside actual QP calls.
original=eb.minimize
errors=[]
def checked_minimize(fun,x,jac,**kw):
    eps=1e-4;eye=np.eye(len(x));fd=np.array([(fun(x+eps*d)-fun(x-eps*d))/(2*eps) for d in eye])
    errors.append(float(np.max(abs(fd-jac(x)))))
    return original(fun,x,jac=jac,**kw)
eb.minimize=checked_minimize
prev=np.array([22.,np.nan,81.]);pq=np.array([24.,np.nan,84.])
r=eb.solve_frame(c,a,h,prev,pq,p,matched=[True,False,True])
eb.minimize=original
check('masked temporal objective gradient',max(errors)<1e-6)
check('dynamic optimum certificate',r['global_gap_bound']<.01 and r['min_constraint_slack']>=-1e-6)
sc=extract(step=168);rot=extract(step=168,angle=45)
check('reference rotation keeps absolute area units',all(np.allclose(a,b,atol=1e-10) for a,b in zip(sc['areas'],rot['areas'])))
check('rotation keeps Euclidean geometry',all(np.allclose(np.linalg.norm(a[:,None]-a[None,:],axis=-1),np.linalg.norm(b[:,None]-b[None,:],axis=-1),atol=1e-10) for a,b in zip(sc['centers'],rot['centers'])))
truth=dict(rows=[dict(x=c[:,0],w=a*.01,pixel_x=c[:,0],pixel_w=a*.01) for c,a in zip(sc['centers'],sc['areas'])],seconds=0)
m,_,_=evaluate(sc,truth,'RA-MTM')
check('perfect dynamic encoding zero errors',max(m[k] for k in ['reference_nmae','motion_step_nmae','trajectory_nmae','growth_step_log_mae','total_growth_log_mae'])<1e-12)
check('matching coverage excludes births',m['matched_pairs']==len(sc['tracking']))
# Independent contraction validates matrix products on this local BLAS runtime.
rng=np.random.default_rng(41);worst=0.
for n in range(2,26):
    A=rng.normal(size=(n*4,n));B=rng.normal(size=(n,n*2));actual=A@B;expected=np.einsum('ij,jk->ik',A,B,optimize=False)
    worst=max(worst,float(np.max(abs(actual-expected))))
check('matrix products agree with independent contractions',worst<1e-12)
save(ROOT/'results/validity/era5_regression.json',dict(checks=records,max_gradient_error=max(errors),max_matrix_error=worst))
print('PASS',len(records),'ERA5 regression checks')
