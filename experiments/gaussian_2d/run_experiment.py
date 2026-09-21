"""2-D Gaussian controlled mechanism study; all trees extracted from scalar grids.
Run: python experiments/gaussian_2d/run_experiment.py
"""
from pathlib import Path
import sys,json,time
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'experiments/synthetic_1d'))
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
from scipy.optimize import linear_sum_assignment
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation,PillowWriter
from ramtm.baselines import tmtm as b1
from ramtm.baselines import stmtm as b2
from ramtm.error_budget import leaf_orders
from ramtm.reference_anchored import Parameters,solve_sequence,render_sequence
from run_experiments import run_b1,run_b2,pack,metrics,save_json,write_csv
OUT = ROOT / 'results/gaussian_2d'
FIGURES = OUT / 'figures'
TABLES = OUT / 'tables'
RECORDS = OUT / 'records'
ARRAYS = OUT / 'arrays'
DATA = ROOT / 'data/generated/gaussian_2d'
for directory in (FIGURES, TABLES, RECORDS, ARRAYS, DATA):
    directory.mkdir(parents=True, exist_ok=True)
GRID=65;T=21;L=2048;C=120.;CELL=(C/(GRID-1))**2
P=Parameters(width_scale=.012,extra_budget=1.,motion_weight=.5)
COLORS=['#1476ad','#de7f26','#9b57a1','#29957d'];METHODS=['TMTM','ST-MTM','RA-MTM']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})

def make_scene(name,seed=0,grid=GRID):
    cell=(C/(grid-1))**2
    axis=np.linspace(0,C,grid);X,Y=np.meshgrid(axis,axis);coords=np.c_[X.ravel(),Y.ravel()]
    base=np.array([[27.3,36.7],[57.7,42.3],[78.1,70.9]])
    amplitudes=np.array([1.,.8,.65]);sig0=np.array([9.,8.,7.]);pivot=np.array([55.,50.])
    if name in ('hierarchy_change','advection_diffusion'):
        base=np.array([[25.3,28.7],[38.7,78.3],[78.1,31.9],[92.7,81.3]])
        amplitudes=np.array([1.,.87,.73,.61]);sig0=np.array([6.,6.5,5.5,6.])
    if name=='crowding':
        base=np.array([[48.3,24.7],[59.7,58.3],[70.1,94.9]])
    if seed:
        rng=np.random.default_rng(seed)
        base=base+rng.uniform(-1.2,1.2,base.shape)
        sig0=sig0*rng.uniform(.95,1.05,len(sig0))
    vals=[];trees=[];frames=[];ids=[];centers=[];area=[];hierarchies=[];controls=[]
    for t in range(T):
        shift=.6*t if name in ('translation','translation_growth') else 0.
        dilation=1+.015*t if name in ('growth','translation_growth') else 1.
        mu=pivot+dilation*(base-pivot)+[shift,0];sigma=dilation*sig0
        if name=='local_growth':
            sigma=sig0*np.array([1.,1.+.02*t,1.])
        if name=='hierarchy_change':
            mu[1,1]-=1.8*t
            mu[2,1]+=.8*t
            mu[:,0]+=.2*t
        if name=='crowding':
            mu[:,0]+=.35*t
            mu[:,0]=mu[:,0].mean()+(mu[:,0]-mu[:,0].mean())*(1-.018*t)
            sigma=sig0*(1+.005*t)
        if name=='advection_diffusion':
            # Exact free-space constant-velocity, isotropic diffusion solution:
            # variance=sigma0^2+2Dt; amplitude rescales to conserve each mass.
            mu=base+np.array([.4*t,.12*t])
            sigma=np.sqrt(sig0**2+2*.6*t)
        amp=amplitudes*(sig0/sigma)**2 if name=='advection_diffusion' else amplitudes
        g=np.array([a*np.exp(-((X-cx)**2+(Y-cy)**2)/(2*s*s)) for (cx,cy),s,a in zip(mu,sigma,amp)])
        # Upper envelope of positive Gaussian hills. No synthetic tree or hand-set sizes.
        field=np.sum(g,axis=0) if name=='advection_diffusion' else np.max(g,axis=0)
        tr=b1.build_augmented_merge_tree(field,'split')
        leaves=[k for k,n in tr.nodes.items() if not n.child_arcs]
        if len(leaves)!=len(base):raise RuntimeError((name,t,'unexpected maxima',len(leaves)))
        rr,cc=linear_sum_assignment(np.linalg.norm(mu[:,None,:]-coords[leaves][None,:,:],axis=-1))
        leaves=[leaves[cc[list(rr).index(i)]] for i in range(len(base))]
        assert max(np.linalg.norm(coords[k]-mu[i]) for i,k in enumerate(leaves))<C/grid*1.5
        children={k:tuple(tr.arcs[a].child for a in n.child_arcs) for k,n in tr.nodes.items()}
        arcs={a:b2.TreeArc(a,e.child,e.parent,np.array(e.regular_vertices[::-1],int)) for a,e in tr.arcs.items()}
        f=b2.AugmentedMergeTreeFrame(t,tr.root,children,arcs,tr.values,coords,coords.min(0),coords.max(0))
        rank={k:i for i,k in enumerate(leaves)}
        def h(k):
            ch=children[k]
            if not ch:return rank[k]
            if len(ch)==1:return h(ch[0])
            return tuple(h(c) for c in ch)
        trees.append(tr);frames.append(f);ids.append(leaves);vals.append(field)
        centers.append([f.leaf_centroid(k) for k in leaves]);area.append([f.leaf_size(k)*cell for k in leaves]);hierarchies.append(h(tr.root))
        controls.append(dict(t=t,shift=shift,dilation=dilation,gaussian_centers=mu,sigma=sigma,amplitudes=amp))
    return dict(name='gaussian2d_'+name,values=np.array(vals),coords=coords,trees=trees,frames=frames,ids=ids,
        centers=np.array(centers),area=np.array(area),hierarchies=hierarchies,summary_only=False,controls=controls,cell_area=cell,grid=grid,seed=seed)

def signature(v,kind='split'):
    tr=v if isinstance(v,b1.AugmentedMergeTree) else b1.build_augmented_merge_tree(v,kind)
    branches=[]
    def walk(k):
        arcs=tr.nodes[k].child_arcs
        if not arcs:return (round(float(tr.values[k]),7),)
        leaves=tuple(sorted(a for arc in arcs for a in walk(tr.arcs[arc].child)))
        if len(arcs)>1:branches.append((round(float(tr.values[k]),7),leaves))
        return leaves
    leaves=walk(tr.root)
    if len(set(leaves))!=len(leaves):raise ValueError('scalar-value topology signature requires distinct leaf values')
    return sorted(branches),sorted(leaves)

def figures(name,sc,res):
    # Requested paper-like plate: real 2-D fields, three scalar maps, mechanism diagnostics.
    fig=plt.figure(figsize=(16,11.2),layout='constrained');gs=fig.add_gridspec(3,6,height_ratios=[1,1.65,1.1])
    for j,t in enumerate([0,4,8,12,16,20]):
        ax=fig.add_subplot(gs[0,j]);im=ax.imshow(sc['values'][t],extent=[0,C,0,C],origin='lower',vmin=0,vmax=1,cmap='viridis',interpolation='nearest')
        for i,k in enumerate(sc['ids'][t]):
            pt=sc['coords'][k];ax.annotate(chr(65+i),pt,xytext=(4,5),textcoords='offset points',color='white',weight='bold',fontsize=12)
        ax.set(title=f't = {t}',xlabel='world x');ax.set_xticks([0,60,120]);ax.set_yticks([0,60,120])
        if j==0:ax.set_ylabel('world y')
    maps=[]
    for j,m in enumerate(METHODS):
        r=res[m];ax=fig.add_subplot(gs[1,2*j:2*j+2]);maps.append(ax)
        top=C if m=='RA-MTM' else 1.
        ax.imshow(r['scalar_map'],origin='lower',aspect='auto',extent=[-.5,T-.5,0,top],cmap='viridis',vmin=0,vmax=1,interpolation='nearest')
        if m=='RA-MTM':
            for i in range(sc['centers'].shape[1]):ax.plot(range(T),sc['centers'][:,i,0],color='white',ls='--',lw=.9,alpha=.75)
        ax.set(title=m+(' | fixed reference' if m=='RA-MTM' else ' | native map'),xlabel='time',ylabel='world x (dashed: true centroid x)' if m=='RA-MTM' else 'normalized output index')
        for t in [0,4,8,12,16,20]:ax.axvline(t,color='white',ls=':',lw=.6,alpha=.4)
    fig.colorbar(im,ax=maps,label='original scalar value',shrink=.8,pad=.015)
    ax=fig.add_subplot(gs[2,:2]);meanq=sc['centers'][:,:,0].mean(1);ax.plot(meanq-meanq[0],color='black',ls='--',label='True centroid motion',lw=2.3)
    for m,color in zip(METHODS,['#6d7b87','#dc852b','#208f79']):
        y=res[m]['x'].mean(1);ax.plot(y-y[0],color=color,label=m,lw=1.8)
    ax.set(title='Common-motion signal',xlabel='time',ylabel='mean anchor displacement');ax.legend(fontsize=8);ax.grid(alpha=.15)
    ax=fig.add_subplot(gs[2,2:4]);truth=sc['area'].sum(1)/sc['area'][0].sum();ax.plot(truth,color='black',ls='--',label='True total leaf area',lw=2.3)
    for m,color in zip(METHODS,['#6d7b87','#dc852b','#208f79']):
        y=res[m]['w'].sum(1);ax.plot(y/y[0],color=color,label=m,lw=1.8)
    ax.set(title='Absolute-area signal',xlabel='time',ylabel='total interval width / initial');ax.legend(fontsize=8);ax.grid(alpha=.15)
    ax=fig.add_subplot(gs[2,4:]);r=res['RA-MTM'];ax.plot(r['tau'],color='#dc852b',label='Minimum feasible error')
    ax.plot(r['budget'],color='#777777',ls='--',label='Allowed error')
    ax.plot(np.max(abs(r['x']-sc['centers'][:,:,0]),1),color='#208f79',label='Achieved error')
    ax.set(title='RA-MTM: certified reference error',xlabel='time',ylabel='max position error');ax.legend(fontsize=8);ax.grid(alpha=.15)
    fig.suptitle('2-D Gaussian evolution: '+name.replace('_',' ')+'\nSame input trees and scalar values; complete scalar-filled outputs; baseline layouts unchanged',fontsize=15)
    fig.savefig(FIGURES/(name+'_comparison.png'),dpi=180);fig.savefig(FIGURES/(name+'_comparison.svg'));plt.close(fig)
    # Actual input segmentation, hierarchy and intervals make the visual claim auditable.
    fig,axes=plt.subplots(2,3,figsize=(13,8),layout='constrained')
    from matplotlib.patches import Rectangle
    for col,t in enumerate([0,10,20]):
        ax=axes[0,col];ax.imshow(sc['values'][t],extent=[0,C,0,C],origin='lower',cmap='Greys',vmin=0,vmax=1,alpha=.4)
        for i,k in enumerate(sc['ids'][t]):
            xy=sc['coords'][sc['frames'][t].leaf_feature_vertices(k)];ax.scatter(xy[:,0],xy[:,1],s=3,color=COLORS[i],alpha=.45)
            q=sc['centers'][t,i];ax.scatter(*q,color=COLORS[i],marker='x');ax.annotate(chr(65+i),q)
        ax.set(title=f't={t}: extracted leaf supports',xlabel='world x',ylabel='world y')
        ax=axes[1,col]
        for row,m in enumerate(METHODS):
            r=res[m]
            for i in range(sc['centers'].shape[1]):
                ax.add_patch(Rectangle((r['z'][t,i]-r['w'][t,i]/2,row-.18),r['w'][t,i],.36,color=COLORS[i],alpha=.4))
                ax.scatter(r['x'][t,i],row,color=COLORS[i],marker='|',s=100)
                ax.scatter(sc['centers'][t,i,0],row+.23,color=COLORS[i],marker='x',s=24)
        ax.set_yticks(range(3),METHODS);ax.set_xlim(-10,130);ax.set_ylim(-.4,2.6);ax.set_xlabel('one-time calibrated coordinate; x = reference')
    fig.suptitle('Extracted supports, not Gaussian parameters, determine centroids and absolute areas')
    fig.savefig(FIGURES/(name+'_intermediates.png'),dpi=160);plt.close(fig)

def animation(sc,res):
    fig,axs=plt.subplots(2,2,figsize=(10,7),layout='constrained')
    def draw(t):
        for ax in axs.flat:ax.clear()
        ax=axs[0,0];ax.imshow(sc['values'][t],extent=[0,C,0,C],origin='lower',vmin=0,vmax=1,cmap='viridis')
        for i,k in enumerate(sc['ids'][t]):ax.annotate(chr(65+i),sc['coords'][k],color='white',xytext=(4,5),textcoords='offset points')
        ax.set(title=f'Original 2-D scalar field | t={t}',xlabel='world x',ylabel='world y')
        for ax,m in zip([axs[0,1],axs[1,0],axs[1,1]],METHODS):
            a=res[m]['scalar_map'].copy();a[:,t+1:]=np.nan;top=C if m=='RA-MTM' else 1
            ax.imshow(a,origin='lower',aspect='auto',extent=[-.5,T-.5,0,top],vmin=0,vmax=1,cmap='viridis',interpolation='nearest')
            ax.axvline(t,color='#e95c41',lw=1)
            if m=='RA-MTM':
                for i in range(sc['centers'].shape[1]):ax.plot(range(t+1),sc['centers'][:t+1,i,0],color='white',ls='--',lw=.8)
            ax.set(title=m,xlabel='time',ylabel='fixed world x' if m=='RA-MTM' else 'normalized output index')
        fig.suptitle('Translation + growth | same extracted trees, different spatial / size semantics')
    anim=FuncAnimation(fig,draw,frames=T,interval=250)
    anim.save(FIGURES/'translation_growth.gif',writer=PillowWriter(fps=4),dpi=100);plt.close(fig)

def geometry_diagnostics(allsc,allres):
    fig,axs=plt.subplots(2,4,figsize=(17,7.8),layout='constrained')
    for ax,(name,sc) in zip(axs.flat,allsc.items()):
        d=np.linalg.norm(sc['centers'][:,:,None,:]-sc['centers'][:,None,:,:],axis=-1)
        for m,color in zip(METHODS,['#6d7b87','#dc852b','#208f79']):
            ax.plot([b2.scale_normalized_stress(dt,x) for dt,x in zip(d,allres[name][m]['x'])],label=m,color=color)
        ax.set(title=name.replace('_',' '),xlabel='time',ylabel='scale-normalized stress');ax.grid(alpha=.15)
    axs.flat[0].legend();axs.flat[-1].axis('off');fig.suptitle('Companion geometry metric: fixed x-reference does not preserve all 2-D distances')
    fig.savefig(FIGURES/'geometry_stress.png',dpi=180);plt.close(fig)

def main():
    rows=[];checks=[];trajectories=[];allsc={};allres={};raster=[]
    canonical=['translation','growth','translation_growth','local_growth','hierarchy_change','crowding','advection_diffusion']
    protocol=[(n,0,GRID) for n in canonical]
    protocol += [(n,s,GRID) for n in ['hierarchy_change','crowding','advection_diffusion'] for s in [1,2,3]]
    protocol += [('translation_growth',0,g) for g in [49,81]]
    save_json(RECORDS/'protocol.json',dict(scenarios=protocol,parameters=asdict(P),note='All declared runs retained; seeds are controlled perturbations, not real data or independent validation.'))
    for family,seed,grid in protocol:
        name=family+(f'_seed{seed}' if seed else '')+(f'_grid{grid}' if grid!=GRID else '')
        print('extract',name,flush=True);sc=make_scene(family,seed,grid);sc['name']='gaussian2d_'+name;res={}
        np.savez_compressed(DATA/(name+'.npz'),scalar_values=sc['values'],coordinates=sc['coords'],centroids=sc['centers'],leaf_area=sc['area'],feature_ids=sc['ids'])
        save_json(DATA/(name+'_trees.json'),dict(cell_area=sc['cell_area'],controls=sc['controls'],hierarchies=sc['hierarchies'],frames=[dict(root=f.root,children=f.children,arcs=[asdict(a) for a in f.arcs.values()]) for f in sc['frames']]))
        for m in METHODS:
            print('run',name,m,flush=True);start=time.perf_counter()
            if m=='TMTM':
                r=run_b1(sc);save_json(RECORDS/(name+'_tmtm_intermediates.json'),dict(decisions=r['decisions'],energy=r['energy'],initial_shift=r['shift'],reflection=r['display_reflection'],translation=r['display_translation']))
            elif m=='ST-MTM':
                p=b2.LayoutParameters('uniform',float(P.width_scale*sc['area'][0].sum()),.95,.5,L,0,min_spacing_delta=.01,optimizer_tolerance=1e-11)
                r=run_b2(sc,p);save_json(RECORDS/(name+'_stmtm_intermediates.json'),dict(parameters=asdict(p),records=r['records'],discrete=[asdict(d) for d in r['discrete']],padding=r['padding'],reflection=r['display_reflection'],translation=r['display_translation']))
            else:
                detail=solve_sequence(sc['centers'],sc['area'],sc['hierarchies'],P);r=pack(detail)
                r['tau']=np.array([d['tau'] for d in detail]);r['budget']=np.array([d['budget'] for d in detail])
                r['scalar_map'],ds,er=render_sequence(sc['frames'],sc['ids'],detail,P.canvas,L)
                save_json(RECORDS/(name+'_ramtm_intermediates.json'),dict(parameters=asdict(P),certificates=detail,discrete=[asdict(d) for d in ds],raster_errors=er))
                for t,(d,e) in enumerate(zip(ds,er)):
                    assert np.allclose(r['scalar_map'][d.anchors,t],sc['frames'][t].values[list(d.ordering)],atol=1e-12)
                    raster.append(dict(scene=name,t=t,**e))
                pixels=[]
                for ids,d in zip(sc['ids'],ds):
                    ix=[d.ordering.index(k) for k in ids]
                    pixels.append((d.anchors[ix]*C/(L-1),(d.ends[ix]-d.starts[ix])*C/(L-1)))
                r['pixel_x']=np.array([v[0] for v in pixels]);r['pixel_w']=np.array([v[1] for v in pixels])
                assert min(d['min_constraint_slack'] for d in detail)>=-1e-6
                assert max(d['qp_gap_bound'] for d in detail)<.01
                assert max(d['global_gap_bound'] for d in detail)<.01
                assert np.max(abs(r['x']-sc['centers'][:,:,0])-r['budget'][:,None])<1e-6
            elapsed=time.perf_counter()-start;res[m]=r
            row=metrics(sc,r,m,elapsed);row.update(family=family,seed=seed,grid=grid);row['total_area_ratio_final']=float(r['w'][-1].sum()/r['w'][0].sum());row['true_total_area_ratio_final']=float(sc['area'][-1].sum()/sc['area'][0].sum());row['mean_displacement_final']=float(np.mean(r['x'][-1]-r['x'][0]));row['true_mean_displacement_final']=float(np.mean(sc['centers'][-1,:,0]-sc['centers'][0,:,0]));rows.append(row)
            np.savez_compressed(ARRAYS/(name+'_'+m+'.npz'),**{k:v for k,v in r.items() if isinstance(v,np.ndarray)})
            for t,tr in enumerate(sc['trees']):
                v=r['scalar_map'][:,t];v=v[np.r_[True,np.abs(np.diff(v))>1e-12]]
                actual=signature(v);truth=signature(tr)
                checks.append(dict(scene=name,method=m,t=t,scalar_topology_equal=actual==truth,source_leaf_count=len(truth[1]),output_leaf_count=len(actual[1]),hierarchy_legal=tuple(r['order'][t]) in leaf_orders(sc['hierarchies'][t])))
                for i in range(sc['centers'].shape[1]):trajectories.append(dict(scene=name,method=m,t=t,feature=chr(65+i),q=sc['centers'][t,i,0],area=sc['area'][t,i],x=r['x'][t,i],z=r['z'][t,i],width=r['w'][t,i]))
        if seed==0 and grid==GRID:
            figures(name,sc,res)
            allsc[name]=sc;allres[name]=res
    geometry_diagnostics(allsc,allres)
    animation(allsc['translation_growth'],allres['translation_growth'])
    write_csv(TABLES/'metrics.csv',rows);write_csv(TABLES/'topology_checks.csv',checks);write_csv(TABLES/'trajectories.csv',trajectories)
    write_csv(TABLES/'raster_errors.csv',raster)
    save_json(RECORDS/'validation.json',dict(frames=T*len(protocol),full_map_checks=len(checks),topology_passed=sum(c['scalar_topology_equal'] for c in checks),parameters=asdict(P),grid=GRID,cell_area=CELL,layout_length=L,max_raster_anchor_error=max(e['anchor_error'] for e in raster),max_raster_interval_extent_error=max(e['interval_extent_error'] for e in raster)))
    assert all(c['scalar_topology_equal'] and c['hierarchy_legal'] for c in checks),'See topology_checks.csv; do not claim full topology preservation'
    print('PASS',len(checks),'full scalar topology checks',flush=True)
    for row in rows:print(row['scene'],row['method'],'motion',round(row['motion_mae'],4),'size',round(row['size_ratio_mae'],4),'position',round(row['reference_mae'],4),flush=True)
if __name__=='__main__':main()
