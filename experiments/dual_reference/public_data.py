"""Dual centroid-reference validation on author Ring and local ERA5; no baseline edits."""
from pathlib import Path
import sys,time,json,hashlib,argparse
from dataclasses import replace,asdict
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'src')]
from experiments.real_era5 import run_experiment as ep
from experiments.ring.dataset import generate,persistence_audit
from ramtm.error_budget import solve_sequence,leaf_orders
from ramtm.reference_anchored import render_sequence
from ramtm.dual_evaluation import position_motion_metrics
OUT=ROOT/'results/dual_public'


def solve_view(sc,p,axis,nominal,reference_points=None):
    start=time.perf_counter();run_start=start
    rows=solve_sequence(sc['centers'],sc['areas'],sc['hier'],p,reference_axis=axis,feature_ids=sc['tracks'],reference_points=reference_points)
    layout_seconds=time.perf_counter()-start;length=nominal;attempts=[];render_seconds=0
    while True:
        start=time.perf_counter()
        try:maps,ds,errors=render_sequence(sc['frames'],sc['ids'],rows,p.canvas,length)
        except ValueError as error:
            render_seconds+=time.perf_counter()-start
            if 'increase resolution' not in str(error) or length>=131072:raise
            attempts.append(dict(length=length,reason=str(error)));length*=2;continue
        render_seconds+=time.perf_counter()-start
        bad=[t for t,tr in enumerate(sc['trees']) if ep.signature(maps[:,t],tr.kind)!=ep.signature(tr)]
        collapsed=[t for t,d in enumerate(ds) if np.any(d.ends-d.starts<=0)]
        attempts.append(dict(length=length,topology_failed=bad,collapsed=collapsed))
        if not bad and not collapsed:break
        if length>=131072:raise RuntimeError('unresolved topology/raster failure')
        length*=2
    checks=[]
    for t,(r,d,ids,c,a,h) in enumerate(zip(rows,ds,sc['ids'],sc['centers'],sc['areas'],sc['hier'])):
        ix=[d.ordering.index(k) for k in ids];o=np.array(r['order'])
        r['pixel_x']=d.anchors[ix]*p.canvas/(length-1);r['pixel_w']=(d.ends[ix]-d.starts[ix])*p.canvas/(length-1)
        assert all(np.isfinite(r[key]).all() for key in ['x','z','w','reference'])
        assert r['feature_ids']==sc['tracks'][t]
        assert np.min(r['z']-r['w']/2)>=-1e-6 and np.max(r['z']+r['w']/2)<=p.canvas+1e-6
        assert np.all(abs(r['x']-r['z'])<=p.rho*r['w']/2+1e-6)
        assert tuple(o) in leaf_orders(h) and np.allclose(r['w'],p.width_scale*a,rtol=0,atol=1e-12)
        assert np.all(np.diff(r['z'][o])-(r['w'][o[:-1]]+r['w'][o[1:]])/2>=p.gap-1e-6)
        assert np.max(abs(r['x']-r['reference']))<=r['budget']+1e-6 and r['global_gap_bound']<.01
        checks.append(dict(t=t,axis=axis,topology_equal=True,hierarchy_legal=True,tau=r['tau'],budget=r['budget'],qp_gap=r['global_gap_bound'],raster_error=errors[t]['anchor_error']))
    return dict(rows=rows,maps=maps,compute_seconds=layout_seconds+render_seconds,checks=checks,
                records=dict(parameters=asdict(p),raster_attempts=attempts,raster_errors=errors),seconds=time.perf_counter()-run_start)


def quality(sc,rows):
    sns=[];tw=[];td=0.;sse=den=0.;growth=[]
    for t,(c,r) in enumerate(zip(sc['centers'],rows)):
        x=r['x'];d=np.linalg.norm(c[:,None]-c[None,:],axis=-1)
        sns.append(ep.b2.scale_normalized_stress(d,x))
        if len(c)>6:tw.append(ep.b2.trustworthiness(c,x,3))
        sse+=np.sum((d-abs(x[:,None]-x[None,:]))**2);den+=np.sum(d*d)
        if t:
            prev={k:i for i,k in enumerate(sc['tracks'][t-1])}
            for i,k in enumerate(sc['tracks'][t]):
                if k in prev:
                    j=prev[k];td+=abs(x[i]-rows[t-1]['x'][j])
                    growth.append(abs(np.log(r['w'][i]/rows[t-1]['w'][j])-np.log(sc['areas'][t][i]/sc['areas'][t-1][j])))
    return dict(SNS=float(np.mean(sns)),TW=float(np.mean(tw)) if tw else None,TW_valid_frames=len(tw),
                TD=float(td),distance_nrmse=float(np.sqrt(sse/den)) if den else None,growth_step_log_mae=float(np.mean(growth)))


def positions(sc,x,y=None,pixel=False):
    key='pixel_x' if pixel else 'x';birth={};out=[]
    for t,(c,ids,row) in enumerate(zip(sc['centers'],sc['tracks'],x)):
        for i,k in enumerate(ids):birth.setdefault(k,c[i,1])
        yy=y[t][key] if y is not None else np.array([birth[k] for k in ids])
        out.append(np.c_[row[key],yy])
    return out


def plot(name,sc,runs,span,folder,metrics):
    plt=ep.plt;plt.rcParams.update({'font.size':9,'pdf.fonttype':42})
    def save(fig,n):
        for ext in ['png','pdf','svg']:fig.savefig(folder/(n+'.'+ext),dpi=240,bbox_inches='tight')
        plt.close(fig)
    times=np.arange(len(sc['frames']));lo,hi=np.quantile(sc['fields'],[0,1]);cmap='magma';datum=0.
    label='Scalar';extension='neither'
    if name=='era5':
        # Exact palette and fixed pressure datum of real_era5/paper_figure.py.
        from matplotlib.colors import LinearSegmentedColormap
        ramp=np.linspace(0,1,1024);colors=plt.get_cmap('RdBu_r')(.08+.84*ramp)
        white=.22*(1-abs(2*ramp-1))**.7
        colors[:,:3]=colors[:,:3]*(1-white[:,None])+white[:,None]
        cmap=LinearSegmentedColormap.from_list('pressure_soft',colors)
        datum=1013.25;lo,hi=-35.,35.;label='MSLP − 1013.25 (hPa)';extension='both'
        ep.save(folder/'color_style.json',dict(palette='pressure_soft',source='experiments/real_era5/paper_figure.py',
            datum_hpa=datum,range_hpa=[lo,hi],meaning='Fixed datum offset, not climatological anomaly',
            saturation={key:dict(below=float(np.mean(values-datum<lo)),above=float(np.mean(values-datum>hi)))
                        for key,values in [('input',sc['fields'])]+[(k,r['maps']) for k,r in runs.items()]}))
    fig,axs=plt.subplots(1,5,figsize=(13,3.3),layout='constrained')
    for ax,t in zip(axs,np.linspace(0,len(times)-1,5).astype(int)):
        im=ax.imshow(sc['fields'][t]-datum,origin='lower',extent=[sc['coords'][:,0].min(),sc['coords'][:,0].max(),sc['coords'][:,1].min(),sc['coords'][:,1].max()],vmin=lo,vmax=hi,cmap=cmap)
        ax.set(title=sc['dates'][t][:16],xlabel='World x',ylabel='World y')
    fig.colorbar(im,ax=axs,label=label,extend=extension,shrink=.7);fig.suptitle(name.upper()+': shared input fields');save(fig,'input_fields')
    fig=plt.figure(figsize=(14,8));gs=fig.add_gridspec(2,3,left=.07,right=.98,bottom=.15,top=.87,wspace=.30,hspace=.35)
    for j,m in enumerate(['TMTM','ST-MTM']):
        ax=fig.add_subplot(gs[:,j]);r=runs[m]
        ax.imshow(r['maps']-datum,origin='lower',aspect='auto',extent=[-.5,len(times)-.5,0,1],vmin=lo,vmax=hi,cmap=cmap)
        ax.set(title=m+f" ({len(r['maps'])} samples)",xlabel='Time step',ylabel='Native map position / extent')
    for k,m in enumerate(['X-only RA-MTM','Dual-Y']):
        ax=fig.add_subplot(gs[k,2]);r=runs[m]
        im=ax.imshow(r['maps']-datum,origin='lower',aspect='auto',extent=[-.5,len(times)-.5,0,span],vmin=lo,vmax=hi,cmap=cmap)
        for t,(row,ids) in enumerate(zip(r['rows'],sc['tracks'])):
            for i,tid in enumerate(ids):ax.scatter(t,row['x'][i],s=3,color=plt.get_cmap('tab20')(tid%20))
        ax.set(title=('X-only RA = Dual-X' if k==0 else 'Dual-Y')+f" ({len(r['maps'])} samples)",xlabel='Time step',ylabel=('X' if k==0 else 'Y')+' reference coordinate')
    fig.suptitle(name.upper()+': unchanged baselines and dual centroid-reference maps\nFixed scalar color range; RA axes in world units; native raster sizes disclosed',fontsize=12)
    cax=fig.add_axes([.36,.045,.32,.017]);fig.colorbar(im,cax=cax,orientation='horizontal',label=label,extend=extension)
    save(fig,'comparison_maps')
    # Longest tracks selected by lifetime only, with identical identities in X/Y.
    ids=sorted(set(v for fr in sc['tracks'] for v in fr),key=lambda k:(-sum(k in fr for fr in sc['tracks']),k))[:3]
    fig,axs=plt.subplots(2,3,figsize=(12,6),layout='constrained')
    for col,tid in enumerate(ids):
        for axis in [0,1]:
            tt=[t for t,fr in enumerate(sc['tracks']) if tid in fr];ix=[sc['tracks'][t].index(tid) for t in tt]
            truth=[sc['centers'][t][i,axis] for t,i in zip(tt,ix)];rr=runs['X-only RA-MTM' if axis==0 else 'Dual-Y']['rows']
            axs[axis,col].plot(tt,truth,'k--',label='Extracted centroid')
            axs[axis,col].plot(tt,[rr[t]['x'][i] for t,i in zip(tt,ix)],color='#16846c',label='Dual anchor')
            axs[axis,col].set(title=f'Track {tid}',xlabel='Time step',ylabel='XY'[axis]+' reference coordinate',ylim=(0,span));axs[axis,col].grid(alpha=.15)
    axs[0,0].legend();fig.suptitle(name.upper()+': three longest tracks (selection by lifetime, not performance)');save(fig,'longest_tracks')


def main(name):
    folder=OUT/name;folder.mkdir(parents=True,exist_ok=True);ep.save(folder/'status.json',dict(status='running'))
    start=time.perf_counter()
    if name=='ring':
        fields,coords,provenance=generate();sc=ep.scene_from_fields(fields,coords,210**2/196,'split');persistence_audit(sc['trees'])
        sc.update(dates=[str(t) for t in range(40)],indices=np.arange(40));span=210.;nominal=196
        p=replace(ep.P,canvas=span,width_scale=1/(2*span),rho=.5,gap=.5*span/120,extra_budget=span/120)
        st=ep.b2.LayoutParameters.from_preset('ring')
    else:
        provenance=ep.audit_source();sc=ep.extract();span=120.;nominal=8192;p=replace(ep.P,rho=.5);st=None
    preprocess=time.perf_counter()-start
    ep.save(folder/'protocol.json',dict(dataset=name,source=provenance,extraction=sc.get('protocol'),parameters=asdict(p),
        reference='leaf-support centroid for X-only and Dual; not previous extremum-reference revision',
        baseline='existing run_method unchanged; Ring paper preset unchanged; ERA5 existing protocol',
        timing='median of three cyclic-order end-to-end layout/render/validation runs; shared extraction, metrics, plotting and IO excluded; Dual per-repeat time = X+Y',
        readout='single-view: native calibrated X plus true Y at track birth held fixed (oracle); Dual: native X/Y',
        minimum_motion=.001*span,normalization='fixed enclosing square diagonal',preprocessing_seconds=preprocess))
    ep.save(folder/'shared_features.json',dict(centers=sc['centers'],areas=sc['areas'],tracks=sc['tracks'],leaf_ids=sc['ids'],hierarchies=sc['hier'],dates=sc['dates'],tracking=sc['tracking']))
    runs={};timings=[];view_methods=['TMTM','ST-MTM','X-only RA-MTM','Dual-Y']
    for rep in range(3):
        for m in view_methods[rep:]+view_methods[:rep]:
            print(name,'repeat',rep+1,m,flush=True)
            if m in ['TMTM','ST-MTM']:
                r=ep.run_method(sc,m,p,canvas=span,length=nominal,stmtm_parameters=st,refine_raster=name!='ring',strict_checks=name!='ring')
            else:r=solve_view(sc,p,0 if m=='X-only RA-MTM' else 1,nominal)
            assert all(v['topology_equal'] for v in r['checks'])
            timings.append(dict(repetition=rep,method=m,layout_render_validation_seconds=r['seconds']))
            if m in runs:
                for old,new in zip(runs[m]['rows'],r['rows']):np.testing.assert_allclose(old['x'],new['x'],atol=1e-8,rtol=0)
                assert np.array_equal(runs[m]['maps'],r['maps'])
            else:runs[m]=r
    ep.table(folder/'runtime_repeats.csv',timings)
    table=[];rendered=[];affine_rows=[];robust=[]
    for m in ['TMTM','ST-MTM','X-only RA-MTM','Dual-Reference RA-MTM']:
        dual=m=='Dual-Reference RA-MTM';r=runs['X-only RA-MTM'] if dual else runs[m];y=runs['Dual-Y'] if dual else None
        qm=quality(sc,r['rows']);ym=quality(sc,y['rows']) if dual else None
        met=position_motion_metrics(sc['centers'],positions(sc,r['rows'],None if y is None else y['rows']),sc['tracks'],(span,span),.001*span)
        table.append(dict(dataset=name,method=m,**met,**{k+'_x':v for k,v in qm.items()},**{k+'_y':None if ym is None else ym[k] for k in qm},
            runtime_seconds=float(np.median([sum(v['layout_render_validation_seconds'] for v in timings if v['repetition']==rep and v['method'] in (['X-only RA-MTM','Dual-Y'] if dual else [m])) for rep in range(3)])),raster_x=len(r['maps']),raster_y=len(y['maps']) if dual else None,
            tau_x=max(v.get('tau',0) for v in r['rows']) if 'RA' in m else None,tau_y=max(v['tau'] for v in y['rows']) if dual else None))
        rendered.append(dict(dataset=name,method=m,**position_motion_metrics(sc['centers'],positions(sc,r['rows'],None if y is None else y['rows'],True),sc['tracks'],(span,span),.001*span)))
        if not dual:
            x0=r['rows'][0]['x'];centered=x0-x0.mean();den=float(centered@centered)
            slope=(centered[:,None]*(sc['centers'][0]-sc['centers'][0].mean(0))).sum(0)/den if den>1e-12 else np.zeros(2)
            offset=sc['centers'][0].mean(0)-x0.mean()*slope
            decoded=[row['x'][:,None]*slope+offset for row in r['rows']]
            affine_rows.append(dict(dataset=name,method=m,calibration='first_frame_2d_affine',first_frame_identifiable=den>1e-12,
                **position_motion_metrics(sc['centers'],decoded,sc['tracks'],(span,span),.001*span)))
        pos=positions(sc,r['rows'],None if y is None else y['rows'])
        for threshold,interior in [(0.,False),(.25,False),(.5,False),(0.,True)]:
            errors=[]
            for link in sc['tracking']:
                if link['iou']<threshold or (interior and link['boundary']):continue
                t=link['t'];i=sc['tracks'][t].index(link['track']);j=sc['tracks'][t-1].index(link['track'])
                errors.append(np.linalg.norm((pos[t][i]-pos[t-1][j])-(sc['centers'][t][i]-sc['centers'][t-1][j]))/(span*np.sqrt(2)))
            robust.append(dict(dataset=name,method=m,iou_min=threshold,interior_only=interior,matched_pairs=len(errors),motion_2d_nmae=float(np.mean(errors)) if errors else None))
    ep.table(folder/'metrics.csv',table);ep.table(folder/'rendered_metrics.csv',rendered)
    ep.table(folder/'affine_metrics.csv',affine_rows);ep.table(folder/'tracking_robustness.csv',robust)
    for m,r in runs.items():
        ep.save(folder/(m+'_records.json'),dict(rows=r['rows'],records=r['records'],checks=r['checks']))
        np.savez_compressed(folder/(m+'_map.npz'),values=r['maps'])
    plot(name,sc,runs,span,folder,table)
    ep.save(folder/'status.json',dict(status='complete',frames=len(sc['frames']),features=sum(map(len,sc['ids'])),matched_pairs=len(sc['tracking']),
        unique_scalar_map_checks=sum(len(r['checks']) for r in runs.values()),all_topology_pass=True,seconds=time.perf_counter()-start))
    print('COMPLETE',name,table,flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--dataset',choices=['ring','era5','both'],default='both');ap.add_argument('--plot-only',action='store_true');args=ap.parse_args()
    for name in (['ring','era5'] if args.dataset=='both' else [args.dataset]):
        if not args.plot_only:main(name);continue
        if name=='ring':
            fields,coords,_=generate();sc=ep.scene_from_fields(fields,coords,210**2/196,'split');sc['dates']=[str(t) for t in range(40)];span=210
        else:sc=ep.extract();span=120
        folder=OUT/name;saved=json.loads((folder/'shared_features.json').read_text())
        assert sc['tracks']==saved['tracks'] and all(np.array_equal(a,b) for a,b in zip(sc['centers'],saved['centers']))
        runs={}
        for m in ['TMTM','ST-MTM','X-only RA-MTM','Dual-Y']:
            r=json.loads((folder/(m+'_records.json')).read_text());r['maps']=np.load(folder/(m+'_map.npz'))['values']
            for row in r['rows']:
                for k in ['x','z','w']:row[k]=np.array(row[k])
            runs[m]=r
        plot(name,sc,runs,span,folder,None)
