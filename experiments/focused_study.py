"""Focused paper tests: temporal identifiability, calibration failures, crowding.

All sweeps are declared here; all results are retained. New field crowding runs
are separate from the original 18-sequence stability set. Reference-axis probes
are skeleton diagnostics using unchanged extracted features, not new fields.
"""
from pathlib import Path
from dataclasses import replace,asdict
import sys,json,csv,time
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'experiments/gaussian_2d')]
from run_experiment import make_scene,P,L,run_b1,run_b2,b2,pack,save_json,write_csv,signature,render_sequence
from ramtm.error_budget import solve_sequence,solve_frame,Parameters
from ramtm.evaluation import task_metrics
from ramtm.diagnostics import hierarchy_signature,target_error_lower_bound,geometry_diagnostics,project_reference
import matplotlib.pyplot as plt
OUT=ROOT/'results';DATA=ROOT/'data/generated/focused'
for path in [DATA,OUT/'ablation',OUT/'main/figures',OUT/'sensitivity',OUT/'validity',OUT/'supplementary/focused']:
    path.mkdir(parents=True,exist_ok=True)
RAW=OUT/'supplementary/focused'

def source(name,kind='arrays'):
    a=OUT/'gaussian_2d'/kind/name
    return a if a.exists() else OUT/'supplementary/gaussian_2d'/kind/name

def metric(c,a,r,span=120.):
    x=r['x'];d=np.linalg.norm(c[:,:,None,:]-c[:,None,:,:],axis=-1)
    return dict(**task_metrics(c,a,x,r['w'],span),
        distance_nrmse=float(np.sqrt(np.sum((d-abs(x[:,:,None]-x[:,None,:]))**2)/np.sum(d*d))),
        error_step_rms=float(np.sqrt(np.mean(np.diff(x-c[:,:,0],axis=0)**2))),
        error_step_max=float(np.max(abs(np.diff(x-c[:,:,0],axis=0)))))

def solve(c,a,h,p):
    detail=solve_sequence(c,a,h,p)
    assert min(d['min_constraint_slack'] for d in detail)>-1e-6
    assert max(d['global_gap_bound'] for d in detail)<.01
    r=pack(detail)
    return r,detail

def canonical_data(name):
    data=np.load(ROOT/'data/generated/gaussian_2d'/(name+'.npz'))
    h=json.loads((ROOT/'data/generated/gaussian_2d'/(name+'_trees.json')).read_text())['hierarchies']
    return data['centroids'],data['leaf_area'],h

def affine(x,q0):
    # Reflection as well as scale is a first-frame gauge; no future truth used.
    u=x[0]-x[0].mean();s=float(u@(q0-q0.mean())/(u@u))
    return s*x+q0.mean()-s*x[0].mean(),s

protocol=dict(temporal_weights=[0.,.1,.5,2.,8.],crowding_scales=[3.,2.,1.5,1.,.6,.3,.1],
    extra_budgets=[0.,1.,4.],reference_angles=[0.,30.,60.,90.],reference_weights=[.25,1.,4.],
    policy='No per-scene selected weights/axes. All variants retained. Skeleton probes explicitly separate from complete field comparisons.')
save_json(RAW/'protocol.json',protocol)

# 1. Temporal term: all 18 fields paired with NoTime, plus isolated mechanisms.
temporal=[];pairing=[];priority=[]
with source('metrics.csv','tables').open() as f:base=list(csv.DictReader(f))
names=list(dict.fromkeys(r['scene'].removeprefix('gaussian2d_') for r in base))
for name in names:
    c,a,h=canonical_data(name)
    full=np.load(source(name+'_RA-MTM.npz'))
    no,_=solve(c,a,h,replace(P,motion_weight=0.))
    fm=metric(c,a,full);nm=metric(c,a,no)
    old,_=solve(c,a,h,replace(P,reference_weight=1.))
    om=metric(c,a,old)
    priority.append(dict(scene=name,**{'reference_priority_'+k:v for k,v in fm.items()},**{'equal_weight_'+k:v for k,v in om.items()}))
    pairing.append(dict(scene=name,**{'full_'+k:v for k,v in fm.items()},**{'no_time_'+k:v for k,v in nm.items()},
        max_anchor_difference=float(np.max(abs(full['x']-no['x'])))))
for case in ['common_translation','cross_axis_oscillation','cross_axis_step']:
    t=np.arange(21);c=np.tile(np.array([[30.,30.],[60.,45.],[90.,30.]]),(21,1,1))
    c[:,:,0]+=.5*t[:,None]
    if case=='cross_axis_oscillation':c[:,1,1]+=10*np.sin(2*np.pi*t/3)
    if case=='cross_axis_step':c[t>=10,1,1]+=15
    a=np.full((21,3),500.);h=[((0,1),2)]*21
    for weight in protocol['temporal_weights']:
        p=replace(P,motion_weight=weight,extra_budget=4.)
        r,d=solve(c,a,h,p)
        temporal.append(dict(case=case,mode='residual',motion_weight=weight,**metric(c,a,r)))
        np.savez_compressed(RAW/f'temporal_{case}_{weight}.npz',centers=c,area=a,x=r['x'],w=r['w'])
    r,d=solve(c,a,h,replace(P,motion_weight=.5,extra_budget=4.,temporal_mode='stationary'))
    temporal.append(dict(case=case,mode='stationary',motion_weight=.5,**metric(c,a,r)))
write_csv(OUT/'ablation/temporal_isolation.csv',temporal)
write_csv(OUT/'ablation/temporal_all_sequences.csv',pairing)
write_csv(OUT/'sensitivity/reference_priority_all_sequences.csv',priority)
print('Temporal isolation complete',flush=True)

# 2. Counterexamples: decompose e_t-e_0 and compute conditional LP lower bounds.
frames=[];calibration=[];bounds=[]
for name in ['hierarchy_change','advection_diffusion','translation_growth']:
    c,a,h=canonical_data(name);q=c[:,:,0]
    detail=json.loads(source(name+'_ramtm_intermediates.json','records').read_text())['certificates']
    ref=np.load(source(name+'_RA-MTM.npz'));e=ref['x']-q
    for t in range(len(c)):
        budget=detail[t]['budget'];switched=t>0 and hierarchy_signature(h[t])!=hierarchy_signature(h[t-1])
        box=float(np.max(np.maximum(abs(e[0])-budget,0)))
        universal=max(0.,detail[0]['tau']-budget)
        cumulative=target_error_lower_bound(c[t],a[t],h[t],budget,q[t]+e[0],P)
        step=0. if t==0 else target_error_lower_bound(c[t],a[t],h[t],budget,q[t]+e[t-1],P)
        actual=float(np.max(abs(e[t]-e[0])));actual_step=0. if t==0 else float(np.max(abs(e[t]-e[t-1])))
        assert cumulative<=actual+1e-6 and step<=actual_step+1e-6
        assert cumulative+1e-6>=box and box+1e-6>=universal
        bounds.append(dict(scene=name,t=t,hierarchy_switch=switched,tau=detail[t]['tau'],budget=budget,
            reference_max=float(np.max(abs(e[t]))),any_initial_layout_bound=universal,initial_error_box_bound=box,
            cumulative_motion_lower_bound=cumulative,cumulative_motion_max=actual,
            step_motion_lower_bound=step,step_motion_max=actual_step))
    for method in ['TMTM','ST-MTM','RA-MTM']:
        r=np.load(source(name+'_'+method+'.npz'));x=r['x'];w=r['w']
        for convention in (['native'] if method=='RA-MTM' else ['native','first_frame_affine']):
            s=1.
            if convention=='first_frame_affine':x,s=affine(r['x'],q[0]);w=abs(s)*r['w']
            err=x-q
            calibration.append(dict(scene=name,method=method,calibration=convention,scale=s,
                initial_reference_mae=float(np.mean(abs(err[0]))),**metric(c,a,dict(x=x,w=w))))
            for t in range(len(c)):
                for i in range(len(q[0])):
                    frames.append(dict(scene=name,method=method,calibration=convention,t=t,feature=i,q=q[t,i],x=x[t,i],
                        reference_error=err[t,i],initial_error=err[0,i],cumulative_motion_error=err[t,i]-err[0,i]))
write_csv(OUT/'main/calibration_conditions.csv',calibration)
write_csv(OUT/'validity/motion_feasibility_bounds.csv',bounds)
write_csv(RAW/'calibration_frames.csv',frames)
print('Calibration bounds complete',flush=True)

# 3. Field-based crowding sweep: regenerate the same family with seven x scales.
# Three budget settings use identical field/tree/truth per level. Baselines are
# solved unchanged once per level. Every output is re-extracted for topology.
crowd=[];crowdframes=[];checks=[]
for scale in protocol['crowding_scales']:
    print('Crowding scale',scale,flush=True)
    sc=make_scene('crowding',crowding_scale=scale);c=sc['centers'];a=sc['area'];h=sc['hierarchies']
    np.savez_compressed(DATA/f'crowding_{scale}.npz',values=sc['values'],centers=c,area=a,coords=sc['coords'])
    save_json(DATA/f'crowding_{scale}.json',dict(scale=scale,hierarchies=h,controls=sc['controls']))
    runs=[('TMTM',None),('ST-MTM',None)]+[('RA-MTM',b) for b in protocol['extra_budgets']]
    for method,budget in runs:
        if method=='TMTM':r=run_b1(sc);detail=None
        elif method=='ST-MTM':
            pars=b2.LayoutParameters('uniform',float(P.width_scale*a[0].sum()),.95,.5,L,0,min_spacing_delta=.01,optimizer_tolerance=1e-11)
            r=run_b2(sc,pars);detail=None
        else:
            pars=replace(P,extra_budget=budget);r,detail=solve(c,a,h,pars)
            r['scalar_map'],_,_=render_sequence(sc['frames'],sc['ids'],detail,pars.canvas,L)
        row=dict(scale=scale,crowding=1-scale/3,method=method,extra_budget=budget,**metric(c,a,r))
        row.update(tau_mean=None if detail is None else float(np.mean([d['tau'] for d in detail])),
                   tau_max=None if detail is None else max(d['tau'] for d in detail),
                   projection_distortion=float(np.sqrt(np.sum((np.linalg.norm(c[:,:,None,:]-c[:,None,:,:],axis=-1)-abs(c[:,:,None,0]-c[:,None,:,0]))**2)/np.sum(np.linalg.norm(c[:,:,None,:]-c[:,None,:,:],axis=-1)**2))))
        dmat=np.linalg.norm(c[:,:,None,:]-c[:,None,:,:],axis=-1)
        budgets=np.array([d['budget'] for d in detail]) if detail is not None else None
        row['geometry_lower_bound_nrmse']=None if detail is None else float(np.sqrt(np.sum(np.maximum(dmat-abs(c[:,:,None,0]-c[:,None,:,0])-2*budgets[:,None,None],0.)**2)/np.sum(dmat*dmat)))
        if detail is not None:assert row['distance_nrmse']>=row['geometry_lower_bound_nrmse']-1e-7
        crowd.append(row)
        for t,tree in enumerate(sc['trees']):
            v=r['scalar_map'][:,t];v=v[np.r_[True,abs(np.diff(v))>1e-12]]
            valid=signature(v)==signature(tree);assert valid
            checks.append(dict(scale=scale,method=method,extra_budget=budget,t=t,topology_equal=valid))
            if detail is not None:
                d=detail[t];projection,lower=geometry_diagnostics(c[t],d['budget'])
                dist=np.linalg.norm(c[t,:,None,:]-c[t,None,:,:],axis=-1)
                actual=float(np.sqrt(np.sum((dist-abs(r['x'][t,:,None]-r['x'][t,None,:]))**2)/np.sum(dist**2)))
                assert actual>=lower-1e-7
                crowdframes.append(dict(scale=scale,crowding=1-scale/3,extra_budget=budget,t=t,tau=d['tau'],budget=d['budget'],
                    reference_max=float(np.max(abs(r['x'][t]-c[t,:,0]))),projection_distortion=projection,geometry_lower_bound=lower,distance_nrmse=actual,
                    global_gap_bound=d['global_gap_bound']))
        np.savez_compressed(RAW/f'crowding_{scale}_{method}_{budget}.npz',x=r['x'],w=r['w'],scalar_map=r['scalar_map'])
write_csv(OUT/'main/crowding_tradeoff.csv',crowd)
write_csv(OUT/'validity/crowding_bounds.csv',crowdframes)
write_csv(OUT/'validity/crowding_topology.csv',checks)

# 4. Axis/parameter stability: declared skeleton probes, with no best-axis choice.
axes=[]
for name in ['hierarchy_change','crowding','advection_diffusion']:
    c,a,h=canonical_data(name)
    for angle in protocol['reference_angles']:
        rotated,span=project_reference(c,angle)
        for beta in protocol['reference_weights']:
            pars=replace(P,canvas=span,reference_weight=beta)
            r,d=solve(rotated,a,h,pars)
            axes.append(dict(scene=name,angle=angle,reference_weight=beta,method='RA-MTM',calibration='fixed_reference',
                projection_span=span,tau_max=max(v['tau'] for v in d),**metric(rotated,a,r,span)))
        for method in ['TMTM','ST-MTM']:
            r=np.load(source(name+'_'+method+'.npz'));x,scale=affine(r['x'],rotated[0,:,0])
            axes.append(dict(scene=name,angle=angle,reference_weight=None,method=method,calibration='first_frame_affine',
                projection_span=span,tau_max=None,**metric(rotated,a,dict(x=x,w=abs(scale)*r['w']),span)))
write_csv(OUT/'sensitivity/reference_direction.csv',axes)

# Independent diagnostics checks (analytic box-bound, invariance, endpoint identity).
assert hierarchy_signature(((0,1),2))==hierarchy_signature((2,(1,0)))
c=np.array([[40.,0.],[60.,15.]])
rot,span=project_reference(c,30)
assert np.allclose(np.linalg.norm(c[0]-c[1]),np.linalg.norm(rot[0]-rot[1]))
pars=Parameters(extra_budget=0.)
lower=target_error_lower_bound(c,[20,20],(0,1),0.,np.array([45.,65.]),pars)
assert abs(lower-5)<1e-9
assert geometry_diagnostics(c,0.)[0]==geometry_diagnostics(c,0.)[1]
summary=dict(temporal_field_pairs=len(pairing),temporal_isolated_runs=len(temporal),
    crowding_full_map_checks=len(checks),crowding_method_runs=len(crowd),
    direction_parameter_runs=len(axes),motion_bound_frames=len(bounds),diagnostic_checks=4,
    temporal_max_anchor_change=max(r['max_anchor_difference'] for r in pairing),
    reference_priority_max_geometry_increase=max(r['reference_priority_distance_nrmse']-r['equal_weight_distance_nrmse'] for r in priority),
    reference_priority_reference_improved=sum(r['reference_priority_reference_nmae']<r['equal_weight_reference_nmae']-1e-6 for r in priority))
save_json(OUT/'validity/focused_summary.json',summary)

# Three compact figures correspond one-to-one to the priority research questions.
fig,axs=plt.subplots(1,3,figsize=(13,3.8),layout='constrained')
for ax,case in zip(axs,['common_translation','cross_axis_oscillation','cross_axis_step']):
    rr=[r for r in temporal if r['case']==case and r['mode']=='residual']
    ax.plot([r['motion_weight'] for r in rr],[r['error_step_rms'] for r in rr],'o-',label='step error RMS')
    ax.plot([r['motion_weight'] for r in rr],[r['reference_nmae']*120 for r in rr],'s-',label='reference MAE')
    ax.set(xscale='symlog',xlabel='Temporal weight',ylabel='World-coordinate error',title=case.replace('_',' '));ax.grid(alpha=.15)
axs[0].legend(fontsize=8);fig.savefig(OUT/'ablation/temporal_isolation.png',dpi=180);plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(14,3.8),layout='constrained')
rr=[r for r in bounds if r['scene']=='hierarchy_change']
axs[0].plot([r['t'] for r in rr],[r['tau'] for r in rr],label='tau*')
axs[0].plot([r['t'] for r in rr],[r['reference_max'] for r in rr],label='achieved reference max')
axs[1].plot([r['t'] for r in rr],[r['cumulative_motion_lower_bound'] for r in rr],label='conditional LP lower bound')
axs[1].plot([r['t'] for r in rr],[r['any_initial_layout_bound'] for r in rr],':',label='bound for any initial layout')
axs[1].plot([r['t'] for r in rr],[r['cumulative_motion_max'] for r in rr],label='actual cumulative max')
for method in ['TMTM','ST-MTM','RA-MTM']:
    conv='native' if method=='RA-MTM' else 'first_frame_affine'
    rr=[r for r in frames if r['scene']=='hierarchy_change' and r['method']==method and r['calibration']==conv]
    axs[2].plot(range(21),[np.mean([abs(r['cumulative_motion_error']) for r in rr if r['t']==t]) for t in range(21)],label=method)
for ax,title in zip(axs,['Changing reference feasibility','Motion cannot always remain exact','Mean motion error: strong calibration']):
    ax.set(title=title,xlabel='Time',ylabel='World-coordinate error');ax.legend(fontsize=7);ax.grid(alpha=.15)
fig.savefig(OUT/'main/figures/calibration_boundary.png',dpi=180);plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(14,4),layout='constrained')
for method,color in [('TMTM','#687888'),('ST-MTM','#d67e25')]:
    rr=[r for r in crowd if r['method']==method]
    for ax,key in zip(axs[:2],['reference_nmae','distance_nrmse']):ax.plot([r['crowding'] for r in rr],[r[key] for r in rr],label=method,color=color)
for budget,style in zip(protocol['extra_budgets'],[':','-','--']):
    rr=[r for r in crowd if r['method']=='RA-MTM' and r['extra_budget']==budget]
    for ax,key in zip(axs[:2],['reference_nmae','distance_nrmse']):ax.plot([r['crowding'] for r in rr],[r[key] for r in rr],style,marker='o',ms=3,label=f'RA-MTM delta={budget:g}',color='#16846c')
rr=[r for r in crowd if r['method']=='RA-MTM' and r['extra_budget']==1.]
axs[1].plot([r['crowding'] for r in rr],[r['projection_distortion'] for r in rr],':',color='black',label='exact projection (may be illegal)')
axs[1].plot([r['crowding'] for r in rr],[r['geometry_lower_bound_nrmse'] for r in rr],'--',color='#999999',label='budget-box lower bound (delta=1)')
axs[2].plot([r['crowding'] for r in rr],[r['tau_max'] for r in rr],'o-',color='#16846c',label='max tau* over time')
for ax,label in zip(axs,['Reference NMAE','Distance NRMSE','Minimum feasible max error (world units)']):
    ax.set(xlabel='Crowding: 1 - x-spacing scale / 3',ylabel=label);ax.grid(alpha=.15);ax.legend(fontsize=7)
fig.suptitle('Crowding exposes a reference-geometry tradeoff; all methods receive the same fields')
fig.savefig(OUT/'main/figures/crowding_tradeoff.png',dpi=180);plt.close(fig)
print('Focused study complete',summary,flush=True)
