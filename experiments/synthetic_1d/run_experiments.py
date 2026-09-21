"""Run the initial mechanism study; artifacts only, one separately maintained report."""
from pathlib import Path
import sys, json, csv, time, platform
from dataclasses import asdict
import numpy as np
import scipy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from datasets import datasets, ROOT, S
sys.path.insert(0, str(ROOT / 'src'))
from ramtm.baselines import tmtm as b1
from ramtm.baselines import stmtm as b2
from ramtm.reference_anchored import render_sequence
from ramtm.evaluation import task_metrics, orient_once
from ramtm.error_budget import Parameters, solve_sequence, leaf_orders, InfeasibleLayout

OUT = ROOT / 'results/synthetic_1d'
FIGURES = OUT / 'figures'
TABLES = OUT / 'tables'
RECORDS = OUT / 'records'
ARRAYS = OUT / 'arrays'
DATA = ROOT / 'data/generated/synthetic_1d'
for directory in (FIGURES, TABLES, RECORDS, ARRAYS, DATA):
    directory.mkdir(parents=True, exist_ok=True)
P=Parameters()
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
COLORS=['#1476AD','#DA8125','#29957D','#9B58A0']

def encode(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    raise TypeError(type(x).__name__)

def save_json(p,obj):p.write_text(json.dumps(obj,default=encode,indent=2,ensure_ascii=False,allow_nan=False))
def write_csv(p,rows):
    if not rows:return
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def pack(frames):
    return {k:np.array([f[k] for f in frames]) for k in ('x','z','w')} | {'order':[tuple(f['order']) for f in frames]}

def run_b1(scene):
    decisions,layouts,energy=b1.optimize_temporal_order(scene['trees'])
    rows=[]; scale=120/(scene['trees'][0].sample_count-1)
    for tree,lin,leaves in zip(scene['trees'],layouts,scene['ids']):
        xs=np.array([lin.position_of_vertex[k] for k in leaves],float)
        bychild={a.child:a.id for a in tree.arcs.values()}
        ints=[lin.subtree_intervals[bychild[k]] for k in leaves]
        widths=np.array([e-s+1 for s,e in ints])*scale
        rows.append(dict(x=xs*scale,z=np.array([(s+e)/2 for s,e in ints])*scale,w=widths,order=tuple(np.argsort(xs))))
        assert np.array_equal(np.sort(lin.vertex_at_position),np.arange(tree.sample_count))
        for a in tree.arcs:
            indices=lin.position_of_vertex[list(tree.subtree_vertices(a))]
            assert indices.max()-indices.min()+1==len(indices)
    r=pack(rows);shift=scene['centers'][0,:,0].mean()-r['x'][0].mean();r['x']+=shift;r['z']+=shift
    r['scalar_map']=np.column_stack([tree.values[lin.vertex_at_position] for tree,lin in zip(scene['trees'],layouts)])
    r['energy']=energy;r['decisions']=decisions;r['shift']=shift
    r['pixel_x']=r['x'].copy();r['pixel_z']=r['z'].copy();r['pixel_w']=r['w'].copy()
    r['sample_positions']=np.array([lin.position_of_vertex for lin in layouts])
    return orient_once(scene,r)

def run_b2(scene,parameters=None):
    if scene['summary_only']:
        # Section 4.1 needs only hierarchy, centroids and sizes. Do not deny
        # STMTM its skeleton just because Section 4.2 lacks scalar arc samples.
        from types import SimpleNamespace
        scene=dict(scene)
        frames=[];ids=[]
        for t,(c,area,h) in enumerate(zip(scene['centers'],scene['area'],scene['hierarchies'])):
            children={};n=len(c);counter=[n]
            def visit(node):
                if isinstance(node,int):children[node]=();return node
                key=counter[0];counter[0]+=1
                children[key]=tuple(visit(v) for v in node);return key
            root=visit(h)
            frames.append(SimpleNamespace(timestep=t,root=root,children=children,leaves=tuple(range(n)),
                leaf_centroid=lambda leaf,c=c:c[leaf],leaf_size=lambda leaf,area=area:int(area[leaf])))
            ids.append(list(range(n)))
        scene.update(frames=frames,ids=ids)
    if parameters is None:
        parameters=b2.LayoutParameters('uniform',float(P.width_scale*scene['area'][0].sum()),.95,.5,2048,0,
                                      min_spacing_delta=.01,optimizer_tolerance=1e-11)
    parameters.validate(len(scene['frames']))
    if parameters.start_timestep!=0:raise ValueError('this experiment adapter fixes Start=0; use the baseline API for other starts')
    # Use the paper's optional supplied correspondences, known by construction.
    # OLO, concordance, both optimizations and all filling use the audited module.
    sk=[];rows=[];records=[]
    for t,(frame,leaves) in enumerate(zip(scene['frames'],scene['ids'])):
        if not t or parameters.mode=='base':
            order=b2.optimal_hierarchical_leaf_order(frame);temporal=None;matches={}
        else:
            matches=dict(zip(leaves,scene['ids'][t-1]))
            order=b2.choose_temporal_order(frame,sk[-1].ordering,matches,parameters.reorder_threshold_r)
            temporal=b2._temporal_positions(order,matches,sk[-1])
        x=b2.project_leaf_anchors(frame,order,parameters,temporal)
        if not t:initial_offset=scene['centers'][0,:,0].mean()-x.mean()
        if not t or parameters.mode=='base':x+=initial_offset
        starts,ends=b2.allocate_leaf_intervals(frame,order,x,parameters)
        sk.append(b2.ContinuousSkeleton(order,x,starts,ends))
        pos={leaf:i for i,leaf in enumerate(order)};ix=[pos[k] for k in leaves]
        rank={leaf:i for i,leaf in enumerate(leaves)}
        rows.append(dict(x=x[ix],z=((starts+ends)/2)[ix],w=(ends-starts)[ix],order=tuple(rank[k] for k in order)))
        sizes=np.array([frame.leaf_size(k) for k in order],float)**parameters.alpha
        target=parameters.total_leaf_extent_k*sizes/sizes.sum()
        records.append(dict(t=t,order=order,anchors=x,starts=starts,ends=ends,matches=matches,
                            equation2=float(np.sum(((ends-starts-target)/target)**2))))
    if scene['summary_only']:
        r=pack(rows);r.update(parameters=asdict(parameters),records=records,continuous=sk,discrete=[],padding=None)
        return orient_once(scene,r)
    ds,padding=b2.discretize_skeletons(scene['frames'],sk,parameters.layout_length)
    r=pack(rows);r['scalar_map']=np.column_stack([b2.fill_frame(f,s,parameters.layout_length) for f,s in zip(scene['frames'],ds)])
    lo=min(float(s.starts.min()) for s in sk);hi=max(float(s.ends.max()) for s in sk)
    units=(hi-lo)/(parameters.layout_length-padding-1);offset=int(np.ceil(padding/2))
    pixels=[]
    for leaves,d in zip(scene['ids'],ds):
        ix=[d.ordering.index(k) for k in leaves]
        pixels.append(((d.anchors[ix]-offset)*units+lo,((d.starts[ix]+d.ends[ix])/2-offset)*units+lo,(d.ends[ix]-d.starts[ix])*units))
    r['pixel_x'],r['pixel_z'],r['pixel_w']=(np.array([v[k] for v in pixels]) for k in range(3))
    r['discrete']=ds;r['continuous']=sk;r['padding']=padding;r['parameters']=asdict(parameters);r['records']=records
    return orient_once(scene,r)

def metrics(scene,r,method,elapsed):
    x,z,w=r['x'],r['z'],r['w'];q=scene['centers'][:,:,0]
    delta=np.diff(x,axis=0)-np.diff(q,axis=0)
    d=np.linalg.norm(scene['centers'][:,:,None,:]-scene['centers'][:,None,:,:],axis=-1)
    dh=np.abs(x[:,:,None]-x[:,None,:]);overlaps=[]
    for t,o in enumerate(r['order']):
        ii=list(o);overlaps.extend((w[t,ii[:-1]]/2+w[t,ii[1:]]/2-np.diff(z[t,ii])).tolist())
    static=np.ptp(q,axis=0)<1e-9
    out=dict(scene=scene['name'],method=method,status='defined',frames=len(x),
        reference_mae=float(np.mean(np.abs(x-q))),motion_mae=float(np.mean(np.abs(delta))),
        center_motion_mae=float(np.mean(np.abs(np.diff(z,axis=0)-np.diff(q,axis=0)))),
        size_ratio_mae=float(np.mean(np.abs(w/w[0]-scene['area']/scene['area'][0]))),
        distance_nrmse=float(np.sqrt(np.sum((d-dh)**2)/np.sum(d*d))),
        sns=float(np.mean([b2.scale_normalized_stress(dt,xt) for dt,xt in zip(d,x)])),
        static_drift_max=float(np.max(np.ptp(x[:,static],axis=0))) if static.any() else None,
        hierarchy_violations=sum(tuple(o) not in leaf_orders(h) for o,h in zip(r['order'],scene['hierarchies'])),
        max_overlap=max(0.,max(overlaps)),max_eccentricity=float(np.max(abs(x-z))),
        max_tau=float(np.max(r['tau'])) if 'tau' in r else None,
        max_budget_violation=float(np.max(np.abs(x-q)-r['budget'][:,None])) if 'budget' in r else None,
        seconds=elapsed)
    out.update(task_metrics(scene['centers'],scene['area'],x,w,120.))
    pixel=task_metrics(scene['centers'],scene['area'],r.get('pixel_x',x),r.get('pixel_w',w),120.)
    out.update({'rendered_'+k:v if 'pixel_x' in r else None for k,v in pixel.items()})
    assert out['hierarchy_violations']==0 and out['max_overlap']<1e-6
    assert all(np.isfinite(a).all() for a in (x,z,w))
    return out

def input_plot(scenes):
    fig,ax=plt.subplots(2,3,figsize=(14,7.5),layout='constrained')
    for a,sc in zip(ax.flat,scenes[:6]):
        a.plot(S,sc['values'][0],color='#808080',label='scalar, first')
        a.plot(S,sc['values'][-1],color='#242F42',ls='--',label='scalar, last')
        for i in range(len(sc['ids'][0])):
            a.scatter([S[sc['ids'][0][i]]],[sc['values'][0,sc['ids'][0][i]]],color=COLORS[i],s=35)
        a.set(title=sc['name'].replace('_',' '),xlabel='source parameter s (fixed adjacency)',ylabel='scalar value')
        a.grid(alpha=.15)
    ax.flat[0].legend(fontsize=8)
    fig.suptitle('Constructed scalar fields: trees and leaf measures are extracted from these inputs')
    fig.savefig(FIGURES/'inputs.png',dpi=180);fig.savefig(FIGURES/'inputs.svg');plt.close(fig)

def comparison_plot(scenes,results):
    chosen=['translation','growth','collective_growth','translation_growth']
    fig,axes=plt.subplots(3,4,figsize=(17,10),sharex='col',layout='constrained')
    for col,name in enumerate(chosen):
        sc=next(s for s in scenes if s['name']==name);tt=np.arange(len(sc['values']))
        for row,method in enumerate(['TMTM','ST-MTM','RA-MTM']):
            a=axes[row,col];r=results[(name,method)]
            for i in range(len(sc['ids'][0])):
                a.fill_between(tt,r['z'][:,i]-r['w'][:,i]/2,r['z'][:,i]+r['w'][:,i]/2,color=COLORS[i],alpha=.20)
                a.plot(tt,r['x'][:,i],color=COLORS[i],lw=1.8)
                a.plot(tt,sc['centers'][:,i,0],color=COLORS[i],ls='--',lw=1,alpha=.75)
            a.set_ylim(-5,125);a.grid(alpha=.13)
            if row==0:a.set_title(name.replace('_',' '))
            if col==0:a.set_ylabel({'TMTM':'TMTM','ST-MTM':'ST-MTM','RA-MTM':'RA-MTM'}[method]+'\ncalibrated layout coordinate')
            if row==2:a.set_xlabel('time step')
    fig.suptitle('Controlled mechanism study | solid: anchor; shading: actual leaf interval; dashed: fixed spatial reference\nTMTM uses one initial alignment and a fixed sample scale; STMTM shows continuous Eq. (1)/(2), before pixel scaling.',fontsize=12)
    fig.savefig(FIGURES/'comparison.png',dpi=180);fig.savefig(FIGURES/'comparison.svg');plt.close(fig)

def diagnostic_plot(scenes,results):
    fig,ax=plt.subplots(2,3,figsize=(14,8),layout='constrained')
    sc=next(s for s in scenes if s['name']=='growth')
    for m,color in zip(['TMTM','ST-MTM','RA-MTM'],['#637282','#D7822A','#208F79']):
        r=results[('growth',m)]
        ax[0,0].plot(r['w'][:,0]/r['w'][0,0],label=m,color=color)
    ax[0,0].axhline(1,color='black',ls='--',label='true left-leaf measure')
    ax[0,0].set(title='Unchanged feature under other-feature growth',ylabel='width / first width',xlabel='time');ax[0,0].legend(fontsize=8)
    for name,col in [('topology_change',1),('crowding',2)]:
        sc=next(s for s in scenes if s['name']==name);r=results[(name,'RA-MTM')]
        ax[0,col].plot(r['tau'],label='minimum max-error tau*',color='#D7822A')
        ax[0,col].plot(r['budget'],label='allowed tau* + 1',ls='--',color='#757575')
        ax[0,col].plot(np.max(abs(r['x']-sc['centers'][:,:,0]),axis=1),label='achieved max-error',color='#208F79')
        ax[0,col].set(title=name.replace('_',' '),xlabel='time',ylabel='reference error');ax[0,col].legend(fontsize=8)
    sc=next(s for s in scenes if s['name']=='topology_change')
    for col,m in enumerate(['TMTM','ST-MTM','RA-MTM']):
        r=results[('topology_change',m)];a=ax[1,col]
        top=120. if m=='RA-MTM' else r['scalar_map'].shape[0]-1
        im=a.imshow(r['scalar_map'],origin='lower',aspect='auto',cmap='viridis',vmin=0,vmax=10,interpolation='nearest',extent=[-.5,r['scalar_map'].shape[1]-.5,0,top])
        a.set(title={'TMTM':'TMTM','ST-MTM':'ST-MTM','RA-MTM':'RA-MTM'}[m]+' scalar-filled map',xlabel='time',ylabel='output sample' if m!='RA-MTM' else 'world reference coordinate')
    fig.suptitle('Mechanisms, error lower bounds, and three complete scalar maps')
    fig.colorbar(im,ax=list(ax[1,:2]),label='original scalar value',fraction=.025,pad=.02)
    fig.savefig(FIGURES/'diagnostics.png',dpi=180);fig.savefig(FIGURES/'diagnostics.svg');plt.close(fig)

def geometry_plot(scenes):
    fig,axes=plt.subplots(2,3,figsize=(14,8),layout='constrained')
    for ax,sc in zip(axes.flat,scenes[:6]):
        xy=sc['coords'];ax.plot(xy[:,0],xy[:,1],color='#C8CDD5',lw=1,zorder=1)
        for i,leaf in enumerate(sc['ids'][0]):
            support=sc['frames'][0].leaf_feature_vertices(leaf)
            ax.scatter(xy[support,0],xy[support,1],s=9,color=COLORS[i],alpha=.5,zorder=2)
            c=sc['centers'][:,i]
            ax.plot(c[:,0],c[:,1],color=COLORS[i],lw=2,zorder=3)
            ax.scatter(c[0,0],c[0,1],marker='o',facecolor='white',edgecolor=COLORS[i],s=50,zorder=4)
            ax.scatter(c[-1,0],c[-1,1],marker='x',color=COLORS[i],s=50,zorder=5)
            ax.annotate(chr(65+i),(c[0,0],c[0,1]),xytext=(3,6),textcoords='offset points')
        ax.set(title=sc['name'].replace('_',' '),xlabel='world x = reference q',ylabel='world y')
        ax.set_xlim(-3,123);ax.set_ylim(-4,48);ax.grid(alpha=.15)
    fig.suptitle('Fixed spatial domains: gray = sampled curve; colored = first leaf supports; circle / cross = first / last centroid\nThe fold creates a genuine hierarchy versus reference-order conflict. Width encodes sample measure, not 2-D area.',fontsize=12)
    fig.savefig(FIGURES/'geometry.png',dpi=180);fig.savefig(FIGURES/'geometry.svg');plt.close(fig)

def main():
    scenes=datasets();results={};rows=[];tr=[];statuses=[];lp=[];timings={}
    for sc in scenes:
        name=sc['name'];print('running',name,flush=True)
        # Summary-only deliberately exports no scalar field or augmented tree.
        payload=dict(centers=sc['centers'],measure=sc['area'],hierarchies=json.dumps(sc['hierarchies']))
        if not sc['summary_only']:payload.update(scalar_values=sc['values'],coordinates=sc['coords'],edges=np.c_[np.arange(len(S)-1),np.arange(1,len(S))])
        np.savez_compressed(DATA/(name+'.npz'),**payload)
        if not sc['summary_only']:
            save_json(DATA/(name+'_trees.json'),{'frames':[dict(timestep=f.timestep,root=f.root,children=f.children,
                arcs=[dict(id=a.id,child=a.child,parent=a.parent,regular_vertices=a.regular_vertices) for a in f.arcs.values()],
                values=f.values,coordinates=f.coordinates,domain_min=f.domain_min,domain_max=f.domain_max,sample_ids=f.sample_ids) for f in sc['frames']]})
        for method in ['TMTM','ST-MTM','RA-MTM']:
            if sc['summary_only'] and method=='TMTM':
                statuses.append(dict(scene=name,method=method,status='missing_required_input',reason='No scalar values, augmented arcs, or original-domain sample supports supplied. Full paper pipeline is undefined; not imputed.'))
                continue
            start=time.perf_counter()
            if method=='TMTM':r=run_b1(sc)
            elif method=='ST-MTM':r=run_b2(sc)
            else:
                detail=solve_sequence(sc['centers'],sc['area'],sc['hierarchies'],P);r=pack(detail)
                r['tau']=np.array([d['tau'] for d in detail]);r['budget']=np.array([d['budget'] for d in detail])
                save_json(RECORDS/(name+'_budget_certificates.json'),detail)
                if not sc['summary_only']:
                    r['scalar_map'],ds,er=render_sequence(sc['frames'],sc['ids'],detail,P.canvas,2048)
                    save_json(RECORDS/(name+'_raster.json'),er)
                    pixels=[]
                    for ids,d in zip(sc['ids'],ds):
                        ix=[d.ordering.index(k) for k in ids]
                        pixels.append((d.anchors[ix]*P.canvas/2047,(d.ends[ix]-d.starts[ix])*P.canvas/2047))
                    r['pixel_x']=np.array([v[0] for v in pixels]);r['pixel_w']=np.array([v[1] for v in pixels])
                for t,d in enumerate(detail):
                    for cand in d['lp_orders']:lp.append(dict(scene=name,t=t,order=str(cand['order']),tau=cand['tau'],selected_order=str(d['order'])))
            elapsed=time.perf_counter()-start;results[(name,method)]=r
            metric=metrics(sc,r,method,elapsed)
            status='skeleton_only' if sc['summary_only'] else 'defined'
            metric['status']=status
            rows.append(metric);statuses.append(dict(scene=name,method=method,status=status,
                reason='Section 4.1 skeleton defined; Section 4.2 scalar filling lacks arc samples' if status=='skeleton_only' else ''))
            for t in range(len(r['x'])):
                for i in range(r['x'].shape[1]):tr.append(dict(scene=name,method=method,t=t,feature=i,q=sc['centers'][t,i,0],measure=sc['area'][t,i],x=r['x'][t,i],center=r['z'][t,i],width=r['w'][t,i],order=str(r['order'][t])))
            arrays={k:v for k,v in r.items() if isinstance(v,np.ndarray)}
            np.savez_compressed(ARRAYS/(name+'_'+method+'.npz'),**arrays)
            if method=='ST-MTM':save_json(RECORDS/(name+'_stmtm_intermediates.json'),dict(parameters=r['parameters'],padding=r['padding'],continuous=r['records'],discrete=[asdict(s) for s in r['discrete']],reflection=r['display_reflection'],translation=r['display_translation']))
            if method=='TMTM':save_json(RECORDS/(name+'_tmtm_intermediates.json'),dict(decisions=r['decisions'],energy=r['energy'],initial_shift=r['shift'],reflection=r['display_reflection'],translation=r['display_translation']))
    write_csv(TABLES/'metrics.csv',rows);write_csv(TABLES/'trajectories.csv',tr);write_csv(TABLES/'applicability.csv',statuses);write_csv(TABLES/'lp_lower_bounds.csv',lp)
    input_plot(scenes);geometry_plot(scenes);comparison_plot(scenes,results);diagnostic_plot(scenes,results)
    save_json(RECORDS/'summary.json',dict(parameters=asdict(P),python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,metrics=rows,statuses=statuses))
    print('completed',len(rows),'defined runs;',len(statuses),'statuses')

if __name__=='__main__':main()
