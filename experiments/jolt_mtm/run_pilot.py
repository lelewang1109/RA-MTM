"""Exhaustive Ring pilot; isolated from formal evidence and production methods."""
from pathlib import Path
import sys
import json
import time
import hashlib
from itertools import product, combinations
from dataclasses import replace

import numpy as np
from scipy.optimize import nnls

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from experiments.ring.run_experiment import pipeline as p, CANVAS, LENGTH
from experiments.ring.dataset import generate

OUT = ROOT / 'results/exploratory/jolt_mtm'
TOL = 1e-8


def geometry(c, x):
    d = np.linalg.norm(c[:, None] - c[None, :], axis=-1)
    ij = np.triu_indices(len(x), 1)
    residual = np.abs(x[:, None] - x[None, :]) - d
    return dict(SNS=p.b2.scale_normalized_stress(d, x),
                TW1=p.b2.trustworthiness(c, x, 1) if len(x) > 2 else None,
                TW3=p.b2.trustworthiness(c, x, 3) if len(x) > 6 else None,
                sse=float(np.sum(residual[ij] ** 2)), den=float(np.sum(d[ij] ** 2)))


def candidate(c, x, kind, order, **extra):
    return dict(x=np.asarray(x), kind=kind, order=tuple(order), **geometry(c, x), **extra)


def fit_gaps(c, order, delta):
    """Convex uniform stress: ||A*g-d||², g>=delta; certify NNLS KKT."""
    n = len(order)
    if n == 1:
        return np.zeros(1), 0., 0.
    pairs = list(combinations(range(n), 2))
    a = np.zeros((len(pairs), n-1))
    d = np.array([np.linalg.norm(c[order[i]]-c[order[j]]) for i, j in pairs])
    for k, (i, j) in enumerate(pairs):
        a[k, i:j] = 1.
    target = d - np.sum(a, axis=1)*delta
    h, _ = nnls(a, target, maxiter=10000)
    # einsum avoids the platform's previously observed small-matrix BLAS warnings.
    residual = np.einsum('ij,j->i', a, h)-target
    gradient = np.einsum('ij,i->j', a, residual)
    scale = max(1., float(np.max(d)))
    kkt = max(float(max(0., -gradient.min())/scale),
              float(np.max(np.abs(h*gradient))/scale**2))
    assert kkt < 1e-8, kkt
    ordered = np.r_[0., np.cumsum(h+delta)]
    ordered -= ordered.mean()
    x = np.empty(n); x[list(order)] = ordered
    return x, float(np.sum(residual**2)), kkt


def transition(sc, t, left, right):
    """Matrices of matched-pair distance-change SSE and matched-point TD."""
    old = {k:i for i,k in enumerate(sc['ids'][t-1])}
    new = {k:i for i,k in enumerate(sc['ids'][t])}
    matches = [(old[v], new[k]) for k,v in sc['matches'][t].items()]
    xx = np.array([v['x'] for v in left]); yy = np.array([v['x'] for v in right])
    sse = np.zeros((len(left), len(right))); td = sse.copy()
    for i,j in matches:
        td += np.abs(xx[:,i,None]-yy[None,:,j])
    for (i,j),(k,l) in combinations(matches, 2):
        truth = np.linalg.norm(sc['centers'][t][j]-sc['centers'][t][l])-np.linalg.norm(sc['centers'][t-1][i]-sc['centers'][t-1][k])
        err = np.abs(yy[:,j]-yy[:,l])[None,:]-np.abs(xx[:,i]-xx[:,k])[:,None]-truth
        sse += err**2
    return sse, td, len(matches)*(len(matches)-1)//2


def shortest_path(nodes, edges, unary=None):
    costs = np.zeros(len(nodes[0])) if unary is None else np.asarray(unary[0]).copy()
    backs = []
    for t, e in enumerate(edges, 1):
        values = costs[:,None]+e
        parent = np.argmin(values, axis=0)
        costs = values[parent,np.arange(len(parent))]
        if unary is not None: costs += unary[t]
        backs.append(parent)
    path = [int(np.argmin(costs))]
    for back in reversed(backs): path.append(int(back[path[-1]]))
    path.reverse()
    return [row[k] for row,k in zip(nodes,path)], path, float(costs.min())


def guarded(v, base):
    return (v['SNS'] <= base['SNS']+TOL and v['sse'] <= base['sse']+TOL
            and all(base[k] is None or v[k] >= base[k]-TOL for k in ['TW1','TW3']))


def summarize(sc, name, seq):
    dyn = td = 0.; count = 0
    for t in range(1,len(seq)):
        e, displacement, n = transition(sc,t,[seq[t-1]],[seq[t]])
        dyn += e[0,0]; td += displacement[0,0]; count += n
    return dict(method=name, SNS=float(np.mean([v['SNS'] for v in seq])),
        SNS_nontrivial=float(np.mean([v['SNS'] for v in seq if len(v['x'])>1])),
        TW1=p.mean([v['TW1'] for v in seq if v['TW1'] is not None]),
        TW3=p.mean([v['TW3'] for v in seq if v['TW3'] is not None]),
        distance_NRMSE=float(np.sqrt(sum(v['sse'] for v in seq)/sum(v['den'] for v in seq))),
        pair_change_NRMSE=float(np.sqrt(dyn/count)/CANVAS), pair_change_SSE=float(dyn),
        pair_change_count=count, TD=float(td),
        TW1_frames=sum(v['TW1'] is not None for v in seq), TW3_frames=sum(v['TW3'] is not None for v in seq))


def render(sc, name, seq, params, native=None):
    if native is not None:
        maps = native['maps']
        xs = [row['pixel_x'] for row in native['rows']]
        collapsed = sum(np.any(row['pixel_w']<=0) for row in native['rows'])
    elif all(v['kind']=='tmtm' for v in seq):
        maps = np.column_stack([tr.values[v['lin'].vertex_at_position] for tr,v in zip(sc['trees'],seq)])
        xs = [v['x'] for v in seq]; collapsed = 0
    else:
        skeletons = []
        for fr,ids,v in zip(sc['frames'],sc['ids'],seq):
            order = v['order']; leaves = tuple(ids[i] for i in order)
            x = v['x'][list(order)]
            s,e = p.b2.allocate_leaf_intervals(fr,leaves,x,params)
            skeletons.append(p.b2.ContinuousSkeleton(leaves,x,s,e))
        ds,padding = p.b2.discretize_skeletons(sc['frames'],skeletons,LENGTH)
        maps = np.column_stack([p.b2.fill_frame(fr,d,LENGTH) for fr,d in zip(sc['frames'],ds)])
        lo = min(s.starts.min() for s in skeletons); hi = max(s.ends.max() for s in skeletons)
        unit = (hi-lo)/(LENGTH-padding-1); offset = int(np.ceil(padding/2))
        xs = [np.array([(d.anchors[d.ordering.index(k)]-offset)*unit+lo for k in ids]) for d,ids in zip(ds,sc['ids'])]
        collapsed = sum(np.any(d.ends-d.starts<=0) for d in ds)
    failures = [t for t,tr in enumerate(sc['trees']) if p.signature(maps[:,t],tr.kind)!=p.signature(tr)]
    pixels = [candidate(c,x,'pixel',np.argsort(x)) for c,x in zip(sc['centers'],xs)]
    metrics = summarize(sc,name,pixels)
    metrics.update(resolution=int(len(maps)), topology_failed_frames=json.dumps(failures), collapsed_width_frames=int(collapsed))
    np.savez_compressed(OUT/(name+'_map.npz'),values=maps)
    return metrics, maps


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    started = time.perf_counter()
    p.save(OUT/'status.json',dict(status='running'))
    fields,coords,provenance = generate()
    sc = p.scene_from_fields(fields,coords,CANVAS**2/196,'split')
    sc.update(dates=list(map(str,range(40))),indices=np.arange(40))
    params = p.b2.LayoutParameters.from_preset('ring')
    protocol = dict(name='JOLT-MTM',input=provenance,frames=40,canvas=CANVAS,resolution=LENGTH,
        gap=params.min_spacing_delta,guard_tolerance=TOL,
        criteria='README.md fixed before first run; 5% geometry / 10% temporal exploratory gates',
        hashes={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in [
            'experiments/jolt_mtm/README.md','experiments/jolt_mtm/run_pilot.py',
            'src/ramtm/baselines/tmtm.py','src/ramtm/baselines/stmtm.py','experiments/real_era5/run_experiment.py']})
    p.save(OUT/'protocol.json',protocol)
    base = {}; native = {}
    for method in ['TMTM','ST-MTM']:
        r = p.run_method(sc,method,canvas=CANVAS,length=LENGTH,stmtm_parameters=params,refine_raster=False,strict_checks=False)
        native[method] = r
        base[method] = [candidate(c,row['x'],'baseline',row['order']) for c,row in zip(sc['centers'],r['rows'])]
    banks_a=[]; banks_b=[]; banks_c=[]; guard=[]; diagnostics=[]; candidates=[]; certificates=[]
    anchor_mean=float(base['ST-MTM'][0]['x'].mean())
    for t,(c,h,tr,fr,ids) in enumerate(zip(sc['centers'],sc['hier'],sc['trees'],sc['frames'],sc['ids'])):
        legal=p.leaf_orders(h); aa=[]; bb=[]; cc=[]; relaxed=[]
        nodes=[k for k,v in tr.nodes.items() if len(v.child_arcs)==2]
        for flags in product([False,True],repeat=len(nodes)):
            lin=p.b1.linearize_tree(tr,dict(zip(nodes,flags)))
            assert np.array_equal(np.sort(lin.vertex_at_position),np.arange(tr.sample_count))
            for arc in tr.arcs:
                vv=lin.position_of_vertex[list(tr.subtree_vertices(arc))]
                assert vv.max()-vv.min()+1==len(vv)
            x=lin.position_of_vertex[ids]*CANVAS/(tr.sample_count-1)
            g=native['TMTM']['gauge']; x=g['scale']*x+g['shift']
            aa.append(candidate(c,x,'tmtm',np.argsort(x),lin=lin))
        assert len(aa)==len(legal)==2**(len(ids)-1)
        assert set(v['order'] for v in aa)==set(legal)
        for order in legal:
            x,sse,kkt=fit_gaps(c,order,params.min_spacing_delta)
            v=candidate(c,x+anchor_mean,'free',order); bb.append(v)
            _,lower,kkt0=fit_gaps(c,order,0.)
            relaxed.append(lower/v['den'] if v['den'] else 0.)
            certificates.append(dict(t=t,order=str(order),kkt=kkt,relaxed_kkt=kkt0,raw_sse=sse,relaxed_sns_bound=relaxed[-1]))
            leaves=tuple(ids[i] for i in order)
            previous=None
            if t:
                old=dict(zip(sc['ids'][t-1],base['ST-MTM'][t-1]['x']))
                previous={k:old[sc['matches'][t][k]] for k in leaves if k in sc['matches'][t]}
            fitted=p.b2.project_leaf_anchors(fr,leaves,params,previous)
            if not t: fitted+=anchor_mean-fitted.mean()
            z=np.empty(len(ids)); z[list(order)]=fitted
            cc.append(candidate(c,z,'same_history',order))
        # Baseline first makes exact objective ties reproducible without an extra metric.
        allnodes=[base['ST-MTM'][t]]+bb+cc
        gg=[v for v in allnodes if guarded(v,base['ST-MTM'][t])]
        guard.append(gg); banks_a.append(aa); banks_b.append(bb); banks_c.append(cc)
        for v in aa+bb+cc:
            candidates.append(dict(t=t,kind=v['kind'],order=str(v['order']),SNS=v['SNS'],TW1=v['TW1'],TW3=v['TW3'],sse=v['sse'],passes_guard=guarded(v,base['ST-MTM'][t])))
        ref=base['ST-MTM'][t]
        diagnostics.append(dict(t=t,leaves=len(ids),orders=len(legal),ST_SNS=ref['SNS'],
            tmtm_best_SNS=min(v['SNS'] for v in aa),free_best_SNS=min(v['SNS'] for v in bb),
            same_history_best_SNS=min(v['SNS'] for v in cc),relaxed_SNS_infimum=min(relaxed),
            tmtm_guard_count=sum(guarded(v,ref) for v in aa),guard_count=len(gg),
            unique_guard_orders=len(set(v['order'] for v in gg))))
        print(f'frame {t:02d}: {len(ids)} leaves, {len(legal)} orders, {len(gg)} guarded candidates',flush=True)
    p.table(OUT/'frame_oracles.csv',diagnostics); p.table(OUT/'candidates.csv',candidates)
    p.table(OUT/'solver_certificates.csv',certificates)
    seqs=dict(base)
    seqs['TMTM-SNS-oracle']=[min(v,key=lambda a:a['SNS']) for v in banks_a]
    seqs['Free-SNS-oracle']=[min(v,key=lambda a:a['SNS']) for v in banks_b]
    seqs['Same-history-SNS-oracle']=[min(v,key=lambda a:a['SNS']) for v in banks_c]
    edges=[transition(sc,t,guard[t-1],guard[t])[0] for t in range(1,40)]
    seqs['JOLT-Guarded'],path,dpvalue=shortest_path(guard,edges)
    # Secondary diagnostic added after the first pilot: rule out paths that buy
    # relation fidelity with more raw motion. Keep the original result intact.
    td_edges=[]
    for t,e in enumerate(edges,1):
        _,td,_=transition(sc,t,guard[t-1],guard[t])
        _,limit,_=transition(sc,t,[base['ST-MTM'][t-1]],[base['ST-MTM'][t]])
        td_edges.append(np.where(td<=limit[0,0]+TOL,e,np.inf))
    seqs['JOLT-TD-Guarded'],_,_=shortest_path(guard,td_edges)
    # Greedy spatial comparator uses exactly the same guarded candidate banks.
    seqs['Guarded-framewise']=[min(v,key=lambda a:a['SNS']) for v in guard]
    overlaps=[]
    for t in range(1,40):
        mat=p.b1.spatial_overlap_matrix(sc['trees'][t-1],sc['trees'][t])
        overlaps.append(np.array([[p.b1.objective_between(sc['trees'][t-1],a['lin'],sc['trees'][t],b['lin'],mat)
            for b in banks_a[t]] for a in banks_a[t-1]]))
    seqs['TMTM-Overlap-DP'],_,overlap_value=shortest_path(banks_a,overlaps)
    metrics=[summarize(sc,name,seq) for name,seq in seqs.items()]
    p.table(OUT/'continuous_metrics.csv',metrics)
    assert abs(next(v for v in metrics if v['method']=='JOLT-Guarded')['pair_change_SSE']-dpvalue)<1e-6
    assert all(guarded(v,b) for v,b in zip(seqs['JOLT-Guarded'],base['ST-MTM']))
    ref_sse=next(v for v in metrics if v['method']=='ST-MTM')['pair_change_SSE']
    assert dpvalue<=ref_sse+1e-6
    original_overlap=float(np.sum(native['TMTM']['records']['energy']))
    # Independently recover the paper-1 baseline path in the enumerated bank.
    baseline_a=[]
    for row,bank in zip(base['TMTM'],banks_a):
        choices=[i for i,v in enumerate(bank) if np.allclose(row['x'],v['x'],atol=1e-9,rtol=0)]
        assert len(choices)==1; baseline_a.append(choices[0])
    baseline_overlap=sum(e[baseline_a[t],baseline_a[t+1]] for t,e in enumerate(overlaps))
    assert abs(baseline_overlap-original_overlap)<1e-9
    assert overlap_value<=baseline_overlap+1e-6
    raster=[]; images={}; rendering_failures=[]
    for name,seq in seqs.items():
        try:
            mm,img=render(sc,name,seq,params,native.get(name)); raster.append(mm); images[name]=img
        except (RuntimeError,ValueError) as exc:
            rendering_failures.append(dict(method=name,error=str(exc)))
    p.table(OUT/'raster_metrics.csv',raster); p.save(OUT/'rendering_failures.json',rendering_failures)
    serial={name:[dict(t=t,kind=v['kind'],order=v['order'],x=v['x']) for t,v in enumerate(seq)] for name,seq in seqs.items()}
    p.save(OUT/'selected_paths.json',serial)
    st=next(v for v in metrics if v['method']=='ST-MTM')
    jolt=next(v for v in metrics if v['method']=='JOLT-Guarded')
    jm=next((v for v in raster if v['method']=='JOLT-Guarded'),None)
    eligible=[]
    for v in metrics:
        rr=next((a for a in raster if a['method']==v['method']),None)
        if v['method'] in base or v['method']=='JOLT-TD-Guarded': continue
        if (v['SNS']<=.95*st['SNS'] and v['TW1']>=st['TW1']-TOL and v['TW3']>=st['TW3']-TOL
            and v['pair_change_NRMSE']<=st['pair_change_NRMSE']+TOL and rr is not None and rr['topology_failed_frames']=='[]'):
            eligible.append(v['method'])
    summary=dict(total_legal_orders=sum(v['orders'] for v in diagnostics),
        maximum_orders=max(v['orders'] for v in diagnostics),
        relaxed_mean_SNS_infimum=float(np.mean([v['relaxed_SNS_infimum'] for v in diagnostics])),
        baseline_mean_SNS=st['SNS'],baseline_overlap=baseline_overlap,optimal_overlap=overlap_value,
        baseline_reported_overlap=original_overlap,
        jolt_SNS_improvement=1-jolt['SNS']/st['SNS'],
        jolt_dynamic_RMSE_improvement=1-jolt['pair_change_NRMSE']/st['pair_change_NRMSE'],
        jolt_changed_frames=[t for t,(a,b) in enumerate(zip(seqs['JOLT-Guarded'],base['ST-MTM'])) if not np.allclose(a['x'],b['x'],atol=1e-8,rtol=0)],
        geometry_gate_passed_by=eligible,
        temporal_only_gate=bool(jolt['pair_change_NRMSE']<=.9*st['pair_change_NRMSE'] and jm is not None and jm['topology_failed_frames']=='[]'),
        rendering_failures=rendering_failures,elapsed_seconds=time.perf_counter()-started,
        limitations=['one exploratory Ring sequence, no independent test set',
            'SNS relaxation is a bound; other oracle paths optimize only their named metric',
            'DP optimality is restricted to fixed candidate banks, no joint continuous optimum',
            'guards are continuous; raster quality and ties may change rankings',
            'Branch B borrows ST intervals and filling; it does not guarantee absolute measures',
            'estimated matching and centroid changes are not independent physical motion truth'])
    p.save(OUT/'summary.json',summary)
    plot_names=['TMTM','ST-MTM','JOLT-Guarded','TMTM-Overlap-DP']
    fig,axes=p.plt.subplots(1,4,figsize=(14,5),layout='constrained')
    for ax,name in zip(axes,plot_names):
        if name in images:
            ax.imshow(images[name],origin='lower',aspect='auto',cmap='magma',vmin=fields.min(),vmax=fields.max())
        ax.set(title=name,xlabel='Frame',ylabel='196-sample map position')
    fig.savefig(OUT/'comparison.png',dpi=170); p.plt.close(fig)
    p.save(OUT/'status.json',dict(status='complete',elapsed_seconds=summary['elapsed_seconds']))
    print(json.dumps(summary,indent=2,default=p.encode))


if __name__=='__main__':
    main()
