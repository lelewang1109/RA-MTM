"""Full-period ERA5 encoding-fidelity study. No meteorological tracking truth is assumed.
Run with --suite main (118 frames), sensitivity, or all. All methods see identical fields.
"""
from pathlib import Path
import sys, json, csv, hashlib, time, argparse, shutil, platform
from datetime import datetime, timezone
from dataclasses import asdict, replace
import numpy as np
from netCDF4 import Dataset, num2date
import netCDF4, scipy
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import gaussian_filter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from ramtm.baselines import tmtm as b1, stmtm as b2
from ramtm.error_budget import Parameters, solve_frame, leaf_orders
from ramtm.reference_anchored import render_sequence
SOURCE=ROOT/'data/real/ERA5_MSLP/ERA5_MSLP_19991117_20000114.nc'
OUT=ROOT/'results/supplementary/era5'
C=120.; L=8192; R=6371.; PHI=52.5
# c times the complete equal-area domain is 60, so absolute widths can never
# consume more than half the canvas. c does not depend on frame or outcome.
P=Parameters(width_scale=60/(C*C),extra_budget=1.,motion_weight=.5,rho=1.)
METHODS=['TMTM','ST-MTM','RA-MTM']
plt.rcParams.update({'font.size':10,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})

def encode(v):
    if isinstance(v,np.ndarray):return v.tolist()
    if isinstance(v,np.generic):return v.item()
    raise TypeError(type(v).__name__)
def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,default=encode,indent=2,allow_nan=False))
def table(path,rows):
    if not rows:return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def mean(v):return float(np.mean(v)) if len(v) else None

def audit_source():
    h=hashlib.sha256()
    with SOURCE.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    with Dataset(SOURCE) as ds:
        tm=np.asarray(ds['valid_time'][:]);lat=np.asarray(ds['latitude'][:]);lon=np.asarray(ds['longitude'][:])
        if not np.all(np.diff(tm)==3600):raise ValueError('expected uninterrupted hourly input')
        v=ds['msl'];bad=0;lo=np.inf;hi=-np.inf
        for start in range(0,len(tm),48):
            a=np.asarray(v[start:start+48].filled(np.nan),float)
            bad+=int((~np.isfinite(a) | (abs(a)>1e10)).sum());lo=min(lo,float(np.nanmin(a)));hi=max(hi,float(np.nanmax(a)))
        if bad:raise ValueError(f'{bad} missing/invalid values; protocol does not impute')
        if v.units!='Pa':raise ValueError('source pressure must be Pa')
        times=[str(t) for t in num2date(tm,ds['valid_time'].units)]
        return dict(path=str(SOURCE.relative_to(ROOT)),sha256=h.hexdigest(),shape=list(v.shape),units='Pa',
            first=times[0],last=times[-1],hourly_step_seconds=3600,missing_values=bad,minimum_Pa=lo,maximum_Pa=hi,
            latitude=[float(lat.min()),float(lat.max())],longitude=[float(lon.min()),float(lon.max())],
            global_attributes={k:ds.getncattr(k) for k in ds.ncattrs()},
            runtime=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,netCDF4=netCDF4.__version__,platform=platform.platform()),
            code_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in [
                'experiments/real_era5/run_experiment.py','src/ramtm/error_budget.py','src/ramtm/reference_anchored.py',
                'src/ramtm/baselines/tmtm.py','src/ramtm/baselines/stmtm.py']},
            source_type='ERA5 reanalysis, not independent observed cyclone tracks',
            documentation='https://www.ecmwf.int/en/forecasts/dataset/ecmwf-reanalysis-v5')

def scene_from_fields(fields,coords,area,kind='join'):
    """Shared Storms/Ring tree extraction, leaf support, and overlap matching."""
    fields=np.asarray(fields)
    if fields.ndim!=3 or not np.isfinite(fields).all():
        raise ValueError('expected finite time-by-y-by-x fields')
    ny,nx=fields.shape[1:]
    frames=[];trees=[];ids=[];centers=[];areas=[];hier=[];boundary=[];matches=[];tracks=[];tracking=[];counter=0
    for t,field in enumerate(fields):
        tr=b1.build_augmented_merge_tree(field,kind)
        children={k:tuple(tr.arcs[a].child for a in n.child_arcs) for k,n in tr.nodes.items()}
        arcs={a:b2.TreeArc(a,e.child,e.parent,np.asarray(e.regular_vertices[::-1],int)) for a,e in tr.arcs.items()}
        fr=b2.AugmentedMergeTreeFrame(t,tr.root,children,arcs,tr.values,coords,coords.min(0),coords.max(0))
        leaves=list(fr.leaves);rank={k:i for i,k in enumerate(leaves)}
        def visit(k):
            ch=children[k]
            if not ch:return rank[k]
            return visit(ch[0]) if len(ch)==1 else tuple(visit(c) for c in ch)
        h=visit(tr.root)
        if len(leaves)>12:raise ValueError(f'{t}: {len(leaves)} leaves; exhaustive-order protocol limit exceeded; do not silently prune')
        m={} if not t else b2.match_leaves_by_overlap(frames[-1],fr)
        ii={k:i for i,k in enumerate(ids[-1])} if t else {}
        tids=[];bm=[]
        for k in leaves:
            sv=fr.leaf_feature_vertices(k);edge=bool(np.any((sv//nx==0)|(sv//nx==ny-1)|(sv%nx==0)|(sv%nx==nx-1)));bm.append(edge)
            if k in m:
                j=ii[m[k]];tid=tracks[-1][j]
                prev=set(frames[-1].leaf_feature_vertices(m[k]));now=set(sv)
                inter=len(prev&now);iou=inter/len(prev|now)
                tracking.append(dict(t=t,current=k,previous=m[k],track=tid,iou=iou,boundary=edge or boundary[-1][j]))
            else:tid=counter;counter+=1
            tids.append(tid)
        frames.append(fr);trees.append(tr);ids.append(leaves);hier.append(h);matches.append(m);tracks.append(tids);boundary.append(bm)
        centers.append(np.array([fr.leaf_centroid(k) for k in leaves]));areas.append(np.array([fr.leaf_size(k)*area for k in leaves]))
    return dict(fields=fields,frames=frames,trees=trees,ids=ids,centers=centers,areas=areas,hier=hier,
        boundary=boundary,matches=matches,tracks=tracks,tracking=tracking,coords=coords)

def extract(step=12,grid=49,sigma=250.,angle=0.):
    co=np.cos(np.deg2rad(PHI))
    with Dataset(SOURCE) as ds:
        lat=np.asarray(ds['latitude'][:]);lon=np.asarray(ds['longitude'][:])
        boundsx=R*co*np.deg2rad([lon.min(),lon.max()]);boundsy=R*np.sin(np.deg2rad([lat.min(),lat.max()]))/co
        dx=np.diff(boundsx)[0]/grid;dy=np.diff(boundsy)[0]/grid
        X,Y=np.meshgrid(boundsx[0]+(np.arange(grid)+.5)*dx,boundsy[0]+(np.arange(grid)+.5)*dy)
        pts=np.c_[np.rad2deg(np.arcsin(Y.ravel()*co/R)),np.rad2deg(X.ravel()/R/co)]
        # Isotropic normalization preserves projected Euclidean geometry.
        # The enclosing-circle diameter is invariant to reference direction.
        # Rotating the reference therefore cannot change lengths or area units.
        span=float(np.hypot(np.diff(boundsx)[0],np.diff(boundsy)[0]));factor=C/span
        xy=np.c_[(X.ravel()-boundsx[0])*factor,(Y.ravel()-boundsy[0])*factor]
        corners=np.array([[0,0],[np.diff(boundsx)[0]*factor,0],[0,np.diff(boundsy)[0]*factor],[np.diff(boundsx)[0]*factor,np.diff(boundsy)[0]*factor]])
        th=np.deg2rad(angle);rot=np.array([[np.cos(th),np.sin(th)],[-np.sin(th),np.cos(th)]])
        scale=1.
        centered=xy-corners.mean(0)
        coords=np.c_[centered[:,0]*np.cos(th)+centered[:,1]*np.sin(th),-centered[:,0]*np.sin(th)+centered[:,1]*np.cos(th)]+C/2
        area=dx*dy*(factor*scale)**2
        fields=[];frames=[];trees=[];ids=[];centers=[];areas=[];hier=[];boundary=[];matches=[];tracks=[];tracking=[];counter=0;preprocessing=[]
        inds=np.arange(0,len(ds['valid_time']),step);dates=[str(v) for v in num2date(ds['valid_time'][inds],ds['valid_time'].units)]
        for t,idx in enumerate(inds):
            f=np.asarray(ds['msl'][int(idx)].filled(np.nan),float)/100
            interpolated=RegularGridInterpolator((lat,lon),f)(pts).reshape(grid,grid)
            field=gaussian_filter(interpolated,(sigma/dy,sigma/dx),mode='reflect')
            preprocessing.append(dict(t=t,rmse_hPa=float(np.sqrt(np.mean((field-interpolated)**2))),max_change_hPa=float(np.max(abs(field-interpolated))),input_min_hPa=float(interpolated.min()),smoothed_min_hPa=float(field.min())))
            fields.append(field)
        shared=scene_from_fields(fields,coords,area,'join')
        frames=shared['frames'];trees=shared['trees'];ids=shared['ids'];centers=shared['centers'];areas=shared['areas']
        hier=shared['hier'];boundary=shared['boundary'];matches=shared['matches'];tracks=shared['tracks'];tracking=shared['tracking']
        counter=len(set(v for row in tracks for v in row))
    return dict(fields=np.array(fields),frames=frames,trees=trees,ids=ids,hier=hier,centers=centers,areas=areas,boundary=boundary,
        matches=matches,tracks=tracks,tracking=tracking,dates=dates,indices=inds,coords=coords,preprocessing=preprocessing,
        protocol=dict(step_hours=step,grid=grid,smoothing_sigma_km=sigma,angle_degrees=angle,projection='spherical Lambert cylindrical equal-area',standard_parallel=PHI,
        earth_radius_km=R,cell_area_km2=dx*dy,cell_area_layout=area,layout_unit_km=1/(factor*scale),coordinate_normalization='fixed enclosing-circle diameter, invariant under reference rotation',
        smoothing_boundary='reflect',spatial_domain='entire supplied rectangle; cell centers; bilinear interpolation',
        feature_definition='join-tree leaf plus regular vertices on its incident arc, not a cyclone basin',
        topology_signature='leaf extrema and branching merge levels; unary root extension contracted; scalar levels rounded to 1e-7 hPa',
        correspondence='maximum intersection-count Hungarian assignment, positive overlap only; shared by ST-MTM, RA-MTM and metrics',
        no_persistence_cancellation=True,frames=len(inds),leaves_min=min(map(len,ids)),leaves_max=max(map(len,ids)),
        total_features=sum(map(len,ids)),matched_pairs=len(tracking),tracks=counter,boundary_features=sum(map(sum,boundary))))

def signature(tree, kind='join'):
    if not isinstance(tree,b1.AugmentedMergeTree):
        v=np.asarray(tree);v=v[np.r_[True,np.abs(np.diff(v))>1e-10]]
        # Contract only degree-two strictly monotone chain vertices. This
        # preserves the 1-D merge tree, its extrema and all saddle levels.
        # It makes checks independent of the raster's oversampling density.
        if len(v)>2:
            direction=np.sign(np.diff(v))
            v=v[np.r_[True,direction[:-1]!=direction[1:],True]]
        tree=b1.build_augmented_merge_tree(v,kind)
    branches=[]
    def walk(k):
        arcs=tree.nodes[k].child_arcs
        if not arcs:return (round(float(tree.values[k]),7),)
        leaves=tuple(sorted(a for arc in arcs for a in walk(tree.arcs[arc].child)))
        if len(arcs)>1:branches.append((round(float(tree.values[k]),7),leaves))
        return leaves
    leaves=walk(tree.root)
    if len(set(leaves))!=len(leaves):raise ValueError('ambiguous equal leaf values in topology signature')
    return sorted(branches),sorted(leaves)

def run_method(sc,method,p=P,relative=False,*,canvas=C,length=L,
               stmtm_parameters=None,refine_raster=True,strict_checks=True,
               ramtm_reference='extremum'):
    # Dataset adapters reuse this runner; ERA5 defaults remain unchanged.
    C=canvas;L=length
    rows=[];cert=[];start=time.perf_counter();frames=sc['frames'];ids=sc['ids']
    if method=='TMTM':
        decisions,layouts,energy=b1.optimize_temporal_order(sc['trees'])
        unit=C/(sc['trees'][0].sample_count-1)
        for tr,lin,leaves in zip(sc['trees'],layouts,ids):
            bychild={a.child:a.id for a in tr.arcs.values()};iv=[lin.subtree_intervals[bychild[k]] for k in leaves]
            x=np.array([lin.position_of_vertex[k] for k in leaves])*unit
            rows.append(dict(x=x,z=np.array([(s+e)/2 for s,e in iv])*unit,w=np.array([e-s+1 for s,e in iv])*unit,order=tuple(np.argsort(x)),pixel_x=x.copy(),pixel_w=np.array([e-s+1 for s,e in iv])*unit))
        maps=np.column_stack([tr.values[lin.vertex_at_position] for tr,lin in zip(sc['trees'],layouts)])
        cert=dict(decisions=decisions,energy=energy)
    elif method=='ST-MTM':
        params=stmtm_parameters or b2.LayoutParameters('uniform',float(P.width_scale*sc['areas'][0].sum()),.95,.5,L,0,min_spacing_delta=.01,optimizer_tolerance=1e-11)
        params.validate(len(frames))
        if params.layout_length!=L or params.start_timestep!=0 or params.mode!='temporal':
            raise ValueError('shared forward runner requires matching L, Start=0, temporal mode')
        skeletons=[]
        for t,(fr,leaves,m) in enumerate(zip(frames,ids,sc['matches'])):
            if not t:order=b2.optimal_hierarchical_leaf_order(fr);temporal=None
            else:
                order=b2.choose_temporal_order(fr,skeletons[-1].ordering,m,params.reorder_threshold_r)
                temporal=b2._temporal_positions(order,m,skeletons[-1])
            x=b2.project_leaf_anchors(fr,order,params,temporal)
            if not t:x+=sc['centers'][0][:,0].mean()-x.mean()
            s,e=b2.allocate_leaf_intervals(fr,order,x,params)
            skeletons.append(b2.ContinuousSkeleton(order,x,s,e));ix=[order.index(k) for k in leaves];rank={k:i for i,k in enumerate(leaves)}
            rows.append(dict(x=x[ix],z=((s+e)/2)[ix],w=(e-s)[ix],order=tuple(rank[k] for k in order)))
        ds,padding=b2.discretize_skeletons(frames,skeletons,L)
        maps=np.column_stack([b2.fill_frame(f,s,L) for f,s in zip(frames,ds)])
        lo=min(s.starts.min() for s in skeletons);hi=max(s.ends.max() for s in skeletons);unit=(hi-lo)/(L-padding-1);offset=int(np.ceil(padding/2))
        for row,d,leaves in zip(rows,ds,ids):
            ix=[d.ordering.index(k) for k in leaves];row.update(pixel_x=(d.anchors[ix]-offset)*unit+lo,pixel_w=(d.ends[ix]-d.starts[ix])*unit)
        cert=dict(parameters=asdict(params),continuous=[asdict(s) for s in skeletons],discrete=[asdict(s) for s in ds],padding=padding)
    else:
        if ramtm_reference not in ('extremum','centroid'):
            raise ValueError('unknown RA-MTM reference mode')
        references=[fr.coordinates[leaves,0] if ramtm_reference=='extremum' else c[:,0]
                    for fr,leaves,c in zip(frames,ids,sc['centers'])]
        overlap={(v['t'],v['current']):v['iou'] for v in sc['tracking']}
        for t,(c,a,h) in enumerate(zip(sc['centers'],sc['areas'],sc['hier'])):
            prev=pq=None;mask=None;confidence=np.zeros(len(c))
            if t:
                prev=np.zeros(len(c));pq=np.zeros(len(c));mask=np.zeros(len(c),bool);old={k:i for i,k in enumerate(ids[t-1])}
                for i,k in enumerate(ids[t]):
                    if k in sc['matches'][t]:
                        j=old[sc['matches'][t][k]];prev[i]=rows[-1]['x'][j];pq[i]=references[t-1][j];mask[i]=True
                        confidence[i]=overlap[t,k] if ramtm_reference=='extremum' else 1.
            aa=a*sc['areas'][0].sum()/a.sum() if relative else a
            r=solve_frame(c,aa,h,prev,pq,p,matched=mask,reference=references[t],temporal_confidence=confidence);rows.append(r)
        render_length=L;render_failures=[]
        while True:
            try:
                maps,ds,er=render_sequence(frames,ids,rows,C,render_length)
                break
            except ValueError as error:
                if str(error)!='fixed-reference raster cannot represent these intervals; increase resolution' or render_length>=131072:
                    raise
                render_failures.append(dict(length=render_length,error=str(error)))
                render_length*=2
        for row,d,leaves in zip(rows,ds,ids):
            ix=[d.ordering.index(k) for k in leaves];row.update(pixel_x=d.anchors[ix]*C/(render_length-1),pixel_w=(d.ends[ix]-d.starts[ix])*C/(render_length-1))
            cert.append({k:v for k,v in row.items() if k not in ('pixel_x','pixel_w')})
        cert=dict(parameters=asdict(p),reference_mode=ramtm_reference,temporal_confidence='shared support IoU' if ramtm_reference=='extremum' else 'unit',relative_width=relative,frames=cert,raster_errors=er,discrete=[asdict(s) for s in ds],render_failures=render_failures)
    compute_seconds=time.perf_counter()-start
    # Exclude validation for every method from the layout/render timer.
    if method=='TMTM':
        for tr,lin in zip(sc['trees'],layouts):
            assert np.array_equal(np.sort(lin.vertex_at_position),np.arange(tr.sample_count))
            for a in tr.arcs:
                v=lin.position_of_vertex[list(tr.subtree_vertices(a))];assert v.max()-v.min()+1==len(v)
    elif method!='ST-MTM':
        for row,q in zip(rows,references):
            assert row['global_gap_bound']<.01
            assert np.max(abs(row['x']-q))<=row['budget']+1e-6
    # Gauge correction for both baselines uses the first frame only, never later data.
    scale=1.;shift=0.
    if method in METHODS[:2]:
        q=sc['centers'][0][:,0];x=rows[0]['x'];scale=1. if np.dot(x-x.mean(),q-q.mean())>=0 else -1.;shift=float(q.mean()-scale*x.mean())
        for r in rows:
            for k in ('x','z','pixel_x'):r[k]=scale*r[k]+shift
            if scale<0:r['order']=tuple(reversed(r['order']))
        if scale<0:maps=maps[::-1]
    # Refinement changes only raster sampling, never an optimizer or coordinates.
    # Keep every failed nominal-resolution check as a disclosed capacity result.
    raster_attempts=[]
    resolution=maps.shape[0]
    while True:
        bad=[t for t,tr in enumerate(sc['trees']) if signature(maps[:,t],tr.kind)!=signature(tr)]
        collapsed=[t for t,r in enumerate(rows) if np.any(r['pixel_w']<=0)]
        raster_attempts.append(dict(length=maps.shape[0],failed_frames=bad,collapsed_width_frames=collapsed))
        if (not bad and not collapsed) or not refine_raster:break
        if method=='TMTM' or resolution>=131072:
            raise AssertionError(f'{method}: scalar topology failure at {resolution}: {bad}')
        resolution*=2
        if method=='ST-MTM':
            ds,padding=b2.discretize_skeletons(frames,skeletons,resolution)
            maps=np.column_stack([b2.fill_frame(f,s,resolution) for f,s in zip(frames,ds)])
            unit=(hi-lo)/(resolution-padding-1);offset=int(np.ceil(padding/2))
            for row,d,leaves in zip(rows,ds,ids):
                ix=[d.ordering.index(k) for k in leaves]
                row.update(pixel_x=scale*((d.anchors[ix]-offset)*unit+lo)+shift,pixel_w=(d.ends[ix]-d.starts[ix])*unit)
            if scale<0:maps=maps[::-1]
            cert.update(discrete=[asdict(s) for s in ds],padding=padding)
        else:
            maps,ds,er=render_sequence(frames,ids,rows,C,resolution)
            for row,d,leaves in zip(rows,ds,ids):
                ix=[d.ordering.index(k) for k in leaves]
                row.update(pixel_x=d.anchors[ix]*C/(resolution-1),pixel_w=(d.ends[ix]-d.starts[ix])*C/(resolution-1))
            cert.update(discrete=[asdict(s) for s in ds],raster_errors=er)
    cert['raster_attempts']=raster_attempts
    checks=[]
    for t,(tr,r) in enumerate(zip(sc['trees'],rows)):
        top=signature(maps[:,t],tr.kind)==signature(tr);legal=tuple(r['order']) in leaf_orders(sc['hier'][t]);o=list(r['order'])
        overlap=max(0.,float(np.max((r['w'][o][:-1]+r['w'][o][1:])/2-np.diff(r['z'][o])))) if len(o)>1 else 0.
        # TMTM widths count inclusive samples; neighboring sample bins can touch.
        if method=='TMTM':overlap=max(0.,overlap-C/(sc['trees'][0].sample_count-1))
        checks.append(dict(t=t,method=method,raster_length=maps.shape[0],nominal_topology_failed=t in raster_attempts[0]['failed_frames'],nominal_width_collapsed=t in raster_attempts[0]['collapsed_width_frames'],topology_equal=top,hierarchy_legal=legal,max_overlap=overlap,
            root_level_error_hPa=abs(float(maps[:,t].max() if tr.kind=='join' else maps[:,t].min())-float(tr.values[tr.root])),
            anchor_raster_error=float(np.max(abs(r['pixel_x']-r['x']))),width_raster_error=float(np.max(abs(r['pixel_w']-r['w'])))))
        if (strict_checks and not top) or not legal or overlap>1e-5:raise AssertionError(checks[-1])
        if not all(np.isfinite(r[k]).all() for k in ['x','z','w','pixel_x','pixel_w']) or np.min(r['w'])<=0 or (strict_checks and np.min(r['pixel_w'])<=0):
            raise AssertionError('nonfinite or collapsed layout')
    return dict(rows=rows,maps=maps,records=cert,checks=checks,seconds=time.perf_counter()-start,compute_seconds=compute_seconds,gauge=dict(scale=scale,shift=shift))

def evaluate(sc,result,method,calibration='native',rendered=False,iou_min=0.,interior=False,*,canvas=C):
    C=canvas
    rows=result['rows'];q0=sc['centers'][0][:,0];xx=rows[0]['x'];s=1.;b=0.
    if calibration=='first_frame_affine' and method in METHODS[:2]:
        denom=float(np.sum((xx-xx.mean())**2));s=float(np.dot(xx-xx.mean(),q0-q0.mean())/denom) if denom>1e-12 else 1.
        if abs(s)<1e-8:raise ValueError('degenerate first-frame affine calibration')
        b=float(q0.mean()-s*xx.mean())
    births={};feature=[];perframe=[];link={(v['t'],v['current']):v for v in sc['tracking']}
    for t,(r,c,a,tids) in enumerate(zip(rows,sc['centers'],sc['areas'],sc['tracks'])):
        x=s*r['pixel_x' if rendered else 'x']+b;w=abs(s)*r['pixel_w' if rendered else 'w'];q=c[:,0]
        geom=np.linalg.norm(c[:,None,:]-c[None,:,:],axis=-1);dh=abs(x[:,None]-x[None,:]);pair=np.triu_indices(len(x),1)
        if interior:
            boundary=np.asarray(sc['boundary'][t],bool)
            keep=~boundary[pair[0]] & ~boundary[pair[1]]
            pair=(pair[0][keep],pair[1][keep])
        ref=[];motion=[];growth=[];traj=[]
        for i,tid in enumerate(tids):
            matched=(t,sc['ids'][t][i]) in link;info=link.get((t,sc['ids'][t][i]));eligible=matched and info['iou']>=iou_min and (not interior or not info['boundary'])
            if tid not in births:births[tid]=(x[i]-q[i],w[i],a[i])
            if not interior or not sc['boundary'][t][i]:ref.append(abs(x[i]-q[i])/C)
            mm=gg=tt=None
            if matched:
                j=sc['tracks'][t-1].index(tid);old=rows[t-1];px=s*old['pixel_x' if rendered else 'x'][j]+b;pw=abs(s)*old['pixel_w' if rendered else 'w'][j]
                mm=abs((x[i]-px)-(q[i]-sc['centers'][t-1][j,0]))/C
                gg=abs(np.log(w[i]/pw)-np.log(a[i]/sc['areas'][t-1][j])) if w[i]>0 and pw>0 else None
                tt=abs((x[i]-q[i])-births[tid][0])/C
                if eligible:
                    motion.append(mm);traj.append(tt)
                    if gg is not None:growth.append(gg)
            feature.append(dict(t=t,track=tid,reference=abs(x[i]-q[i])/C,motion=mm,growth=gg,trajectory=tt,eligible=eligible,
                boundary=sc['boundary'][t][i],iou=None if info is None else info['iou'],q=q[i],x=x[i],width=w[i],area=a[i]))
        total=abs(np.log(w.sum()/sum(abs(s)*rows[0]['pixel_w' if rendered else 'w']))-np.log(a.sum()/sc['areas'][0].sum()))
        perframe.append(dict(t=t,date=sc['dates'][t],block=int(sc['indices'][t]//168),reference_nmae=mean(ref),motion_step_nmae=mean(motion),growth_step_log_mae=mean(growth),trajectory_nmae=mean(traj),total_growth_log_error=float(total),
            geometry_sse=float(np.sum((geom[pair]-dh[pair])**2)),geometry_den=float(np.sum(geom[pair]**2)),tau=float(r.get('tau',0.)),n=len(x),matched=len(motion)))
    metric=dict(method=method,calibration=calibration,rendered=rendered,iou_min=iou_min,interior_only=interior,
        reference_nmae=mean([v['reference'] for v in feature if not interior or not v['boundary']]),
        motion_step_nmae=mean([v['motion'] for v in feature if v['eligible']]),
        trajectory_nmae=mean([v['trajectory'] for v in feature if v['eligible']]),
        growth_step_log_mae=mean([v['growth'] for v in feature if v['eligible'] and v['growth'] is not None]),
        total_growth_log_mae=mean([v['total_growth_log_error'] for v in perframe[1:]]),
        distance_nrmse=float(np.sqrt(sum(v['geometry_sse'] for v in perframe)/sum(v['geometry_den'] for v in perframe))) if sum(v['geometry_den'] for v in perframe)>0 else None,
        matched_pairs=sum(v['eligible'] for v in feature),growth_pairs=sum(v['eligible'] and v['growth'] is not None for v in feature),collapsed_intervals=sum(v['width']<=0 for v in feature),features=sum(map(len,sc['ids'])),reference_features=sum(not interior or not v['boundary'] for v in feature),frames=len(rows),seconds=result['seconds'],affine_scale=s,affine_shift=b)
    return metric,perframe,feature

def figures(sc,results,stats):
    path=ROOT/'results/main/figures';path.mkdir(parents=True,exist_ok=True)
    fig,axes=plt.subplots(3,3,figsize=(15,11),layout='constrained')
    # Fixed quantile dates, independent of method performance.
    for ax,t in zip(axes[0],np.linspace(0,len(sc['frames'])-1,3,dtype=int)):
        im=ax.imshow(sc['fields'][t],origin='lower',cmap='RdBu_r',vmin=960,vmax=1040,extent=[-30,40,30,75],aspect='auto')
        ax.set(title=sc['dates'][t][:16],xlabel='Longitude (degrees)',ylabel='Equal-area latitude coordinate')
        # imshow y is equal-area, label actual latitude at known projected rows.
        ticks=np.array([30,45,60,75]);positions=30+45*(np.sin(np.deg2rad(ticks))-.5)/(np.sin(np.deg2rad(75))-.5)
        ax.set_yticks(positions,labels=ticks)
    fig.colorbar(im,ax=axes[0],label='Smoothed MSLP (hPa)',shrink=.7)
    days=sc['indices']/24
    for ax,m in zip(axes[1],METHODS):
        ax.imshow(results[m]['maps'],aspect='auto',origin='lower',cmap='RdBu_r',vmin=960,vmax=1040,extent=[0,days[-1],0,1])
        ax.set(title=m,xlabel='Days since 1999-11-17',ylabel='Map pixel fraction')
    for m in METHODS:
        pf=stats[m];axes[2,0].plot(days,[v['reference_nmae'] for v in pf],label=m)
        axes[2,1].plot(days,[v['motion_step_nmae'] for v in pf],label=m)
    axes[2,0].set(ylabel='Reference NMAE',xlabel='Days');axes[2,0].legend()
    axes[2,1].set(ylabel='Matched step-motion NMAE',xlabel='Days')
    axes[2,2].plot(days,[v['tau'] for v in stats['RA-MTM']],color='#29957d',label=r'$\tau^*$')
    ax2=axes[2,2].twinx();ax2.step(days,list(map(len,sc['ids'])),color='#888888',alpha=.5);ax2.set_ylabel('Leaf count',color='#777777')
    axes[2,2].set(xlabel='Days',ylabel='Minimum reference conflict');axes[2,2].legend()
    fig.suptitle('ERA5 full supplied region and period — derived-feature encoding fidelity\nScalar maps use each method’s native raster; quantitative positions are decoded to fixed coordinates')
    fig.savefig(path/'era5_evidence.png',dpi=180);fig.savefig(path/'era5_evidence.svg');plt.close(fig)

def execute(label,sc,methods=METHODS,p=P,relative=False,keep_maps=False):
    print('RUN',label,sc['protocol'],flush=True);base=OUT/label;base.mkdir(parents=True,exist_ok=True)
    save(base/'protocol.json',sc['protocol']);table(base/'tracking.csv',sc['tracking']);table(base/'preprocessing.csv',sc['preprocessing'])
    results={};metrics=[];stats={};checks=[];features=[]
    for m in methods:
        print('METHOD',label,m,flush=True);r=run_method(sc,m,p,relative);results[m]=r
        for cal in ['native','first_frame_affine']:
            met,pf,feat=evaluate(sc,r,m,cal);metrics.append(dict(run=label,**met))
            table(base/(m+'_'+cal+'_frames.csv'),pf)
            if cal=='native':stats[m]=pf;features.extend(dict(method=m,**v) for v in feat)
        pix,_,_=evaluate(sc,r,m,rendered=True);metrics.append(dict(run=label,**pix))
        checks.extend(dict(run=label,**v) for v in r['checks'])
        save(base/(m+'_records.json'),dict(gauge=r['gauge'],details=r['records']))
        if keep_maps:np.savez_compressed(base/(m+'_arrays.npz'),scalar_map=r['maps'])
        print('RESULT',label,m,metrics[-3],flush=True)
    table(base/'metrics.csv',metrics);table(base/'validity.csv',checks);table(base/'features.csv',features)
    if keep_maps:
        np.savez_compressed(base/'input.npz',fields=sc['fields'],coordinates=sc['coords'],source_indices=sc['indices'])
        save(base/'features.json',dict(ids=sc['ids'],centers=sc['centers'],areas=sc['areas'],hierarchies=sc['hier'],tracks=sc['tracks'],boundary=sc['boundary'],dates=sc['dates']))
    return results,metrics,stats,checks

def stability(sc,res,stats):
    rows=[];rng=np.random.default_rng(20260921)
    for cal in ['native','first_frame_affine']:
        pf={m:evaluate(sc,r,m,cal)[1] for m,r in res.items()}
        blocks=sorted(set(v['block'] for v in pf['RA-MTM']))
        for m in METHODS[:2]:
            for key in ['reference_nmae','motion_step_nmae','growth_step_log_mae','trajectory_nmae']:
                diffs=[]
                for block in blocks:
                    pairs=[(a[key],b[key]) for a,b in zip(pf[m],pf['RA-MTM']) if a['block']==block and a[key] is not None and b[key] is not None]
                    diffs.append(float(np.mean([a-b for a,b in pairs])))
                boot=np.mean(rng.choice(diffs,size=(5000,len(diffs)),replace=True),axis=1)
                rows.append(dict(calibration=cal,baseline=m,metric=key,blocks=len(diffs),ra_better_blocks=sum(d>1e-9 for d in diffs),ties=sum(abs(d)<=1e-9 for d in diffs),baseline_minus_ra_mean=float(np.mean(diffs)),block_bootstrap_low=float(np.quantile(boot,.025)),block_bootstrap_high=float(np.quantile(boot,.975))))
    table(ROOT/'results/auxiliary/era5_stability.csv',rows)
    strata=[]
    for threshold in [0.,.1,.25,.5]:
        for interior in [False,True]:
            for m,r in res.items():
                metric,_,_=evaluate(sc,r,m,iou_min=threshold,interior=interior);strata.append(metric)
    table(ROOT/'results/auxiliary/era5_tracking_robustness.csv',strata)
    # Conflict strata are defined by RA's feasibility certificate, not by wins.
    strata=[]
    for conflict in [False,True]:
        selected=[i for i,v in enumerate(stats['RA-MTM']) if (v['tau']>1e-6)==conflict]
        for m in METHODS:
            pf=[stats[m][i] for i in selected]
            strata.append(dict(conflict=conflict,method=m,frames=len(pf),reference_nmae=mean([v['reference_nmae'] for v in pf]),motion_step_nmae=mean([v['motion_step_nmae'] for v in pf if v['motion_step_nmae'] is not None]),distance_nrmse=float(np.sqrt(sum(v['geometry_sse'] for v in pf)/sum(v['geometry_den'] for v in pf))) if pf else None))
    table(ROOT/'results/auxiliary/era5_conflict_strata.csv',strata)
    diagnostics=[]
    def induced_clusters(h,tids,common):
        clusters=set()
        def visit(node):
            if isinstance(node,(int,np.integer)):
                return {tids[node]} & common
            members=set().union(*(visit(child) for child in node))
            if 1<len(members)<len(common):clusters.add(tuple(sorted(members)))
            return members
        visit(h);return clusters
    for t,(c,a,h,tids) in enumerate(zip(sc['centers'],sc['areas'],sc['hier'],sc['tracks'])):
        current=set(tids);previous=set(sc['tracks'][t-1]) if t else set();common=current & previous
        changed=None if len(common)<3 else induced_clusters(h,tids,common)!=induced_clusters(sc['hier'][t-1],sc['tracks'][t-1],common)
        r=res['RA-MTM']['rows'][t]
        q=np.asarray(r.get('reference',c[:,0]));width=P.width_scale*a;pair=np.triu_indices(len(q),1)
        direct_conflicts=int(np.sum(abs(q[pair[0]]-q[pair[1]])<(width[pair[0]]+width[pair[1]])/2+P.gap))
        diagnostics.append(dict(t=t,date=sc['dates'][t],leaves=len(tids),births=len(current-previous),deaths=len(previous-current),common_leaves=len(common),induced_hierarchy_changed=changed,
            reference_order_legal=tuple(np.argsort(q)) in leaf_orders(h),projected_interval_conflict_pairs=direct_conflicts,tau=r['tau'],budget=r['budget'],global_qp_gap=r['global_gap_bound'],boundary_features=sum(sc['boundary'][t])))
    table(ROOT/'results/auxiliary/era5_scene_diagnostics.csv',diagnostics)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--suite',choices=['main','sensitivity','all'],default='all');args=ap.parse_args()
    if args.suite=='all' and OUT.exists():
        backup=ROOT/'archive'/('era5_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        owned=[OUT]+[p for p in (ROOT/'results').rglob('era5_*') if OUT not in p.parents and p.is_file() and p.name!='era5_regression.json']
        for source in owned:
            target=backup/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(source),str(target))
    OUT.mkdir(parents=True,exist_ok=True);status=OUT/('status_'+args.suite+'.json')
    save(status,dict(status='running',suite=args.suite,started=datetime.now(timezone.utc).isoformat()))
    try:
        save(OUT/'source.json',audit_source())
        if args.suite in ('main','all'):
            save(OUT/'status_main.json',dict(status='running'))
            sc=extract();res,met,stats,checks=execute('main',sc,keep_maps=True)
            table(ROOT/'results/main/era5_metrics.csv',met);table(ROOT/'results/validity/era5_main.csv',checks)
            stability(sc,res,stats);figures(sc,res,stats)
            abl=[];ac=[]
            for label,pars,relative in [('NoTime',replace(P,motion_weight=0.),False),('ReferenceOnly',replace(P,geometry_weight=0.),False),('RelativeWidth',P,True)]:
                _,mm,_,cc=execute(label,sc,['RA-MTM'],pars,relative);abl.extend(mm);ac.extend(cc)
            table(ROOT/'results/ablation/era5_core.csv',[m for m in met if m['method']=='RA-MTM']+abl)
            table(ROOT/'results/validity/era5_ablation.csv',ac)
            save(OUT/'status_main.json',dict(status='complete'))
        if args.suite in ('sensitivity','all'):
            save(OUT/'status_sensitivity.json',dict(status='running'))
            mets=[];checks=[]
            # Independent fixed protocol variations; no outcome-based tuning.
            cases=[('daily',dict(step=24),P,METHODS),('six_hour',dict(step=6),P,METHODS),
                ('sigma200',dict(step=24,sigma=200),P,METHODS),('sigma300',dict(step=24,sigma=300),P,METHODS),
                ('grid41',dict(step=24,grid=41),P,METHODS),('grid61',dict(step=24,grid=61),P,METHODS),
                ('direction45',dict(step=24,angle=45),P,METHODS),('direction90',dict(step=24,angle=90),P,METHODS),
                ('beta1',dict(step=24),replace(P,reference_weight=1),['RA-MTM']),('beta8',dict(step=24),replace(P,reference_weight=8),['RA-MTM']),
                ('budget0',dict(step=24),replace(P,extra_budget=0),['RA-MTM']),('budget4',dict(step=24),replace(P,extra_budget=4),['RA-MTM'])]
            for label,kw,p,methods in cases:
                sc=extract(**kw);_,mm,_,cc=execute(label,sc,methods,p);mets.extend(mm);checks.extend(cc)
            table(ROOT/'results/sensitivity/era5_protocol.csv',mets);table(ROOT/'results/validity/era5_sensitivity.csv',checks)
            save(OUT/'status_sensitivity.json',dict(status='complete'))
        save(status,dict(status='complete',suite=args.suite,finished=datetime.now(timezone.utc).isoformat()))
    except BaseException as e:
        save(status,dict(status='failed',suite=args.suite,error=str(e)));raise
if __name__=='__main__':main()
