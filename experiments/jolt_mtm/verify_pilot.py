"""Independent metric checks, convex-solver cross-check and DP brute force."""
from pathlib import Path
import sys
import json
import csv
from itertools import product, combinations
from dataclasses import replace
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from experiments.jolt_mtm.run_pilot import OUT,p,generate,CANVAS,fit_gaps,shortest_path


def read_csv(name):
    with (OUT/name).open() as stream:return list(csv.DictReader(stream))


def main():
    checks=[]
    def check(name,condition):
        assert condition,name
        checks.append(name)
    fields,coords,_=generate()
    sc=p.scene_from_fields(fields,coords,CANVAS**2/196,'split')
    paths=json.loads((OUT/'selected_paths.json').read_text())
    metrics={v['method']:v for v in read_csv('continuous_metrics.csv')}
    for name,path in paths.items():
        sns=[];sse=den=td=dynamic=0.;count=0;tw={1:[],3:[]}
        for t,row in enumerate(path):
            x=np.array(row['x']);c=sc['centers'][t];n=len(x)
            check(f'{name}/{t}: legal leaf order',tuple(row['order']) in p.leaf_orders(sc['hier'][t]))
            if n>1:check(f'{name}/{t}: strict anchor order',np.all(np.diff(x[row['order']])>0))
            d=np.array([[np.linalg.norm(a-b) for b in c] for a in c])
            dx=np.abs(x[:,None]-x[None,:]);pair=np.triu_indices(n,1)
            dd=d[pair];xx=dx[pair]
            alpha=float(np.dot(dd,xx)/np.dot(xx,xx)) if np.dot(xx,xx)>0 else 0.
            sns.append(float(np.sum((dd-alpha*xx)**2)/np.sum(dd**2)) if np.sum(dd**2)>0 else 0.)
            sse+=np.sum((dd-xx)**2);den+=np.sum(dd**2)
            for k in tw:
                if n<=2*k:continue
                penalty=0
                for i in range(n):
                    source=sorted((j for j in range(n) if j!=i),key=lambda j:(d[i,j],j))
                    target=sorted((j for j in range(n) if j!=i),key=lambda j:(dx[i,j],j))
                    penalty+=sum(source.index(j)+1-k for j in set(target[:k])-set(source[:k]))
                tw[k].append(1-2*penalty/(n*k*(2*n-3*k-1)))
            if t:
                previous=paths[name][t-1]['x']
                pairs=[(sc['ids'][t-1].index(v),sc['ids'][t].index(k)) for k,v in sc['matches'][t].items()]
                td+=sum(abs(x[j]-previous[i]) for i,j in pairs)
                for (a,b),(i,j) in combinations(pairs,2):
                    predicted=abs(x[b]-x[j])-abs(previous[a]-previous[i])
                    truth=np.linalg.norm(c[b]-c[j])-np.linalg.norm(sc['centers'][t-1][a]-sc['centers'][t-1][i])
                    dynamic+=(predicted-truth)**2;count+=1
        computed=dict(SNS=np.mean(sns),TW1=np.mean(tw[1]),TW3=np.mean(tw[3]),
            distance_NRMSE=np.sqrt(sse/den),pair_change_NRMSE=np.sqrt(dynamic/count)/CANVAS,TD=td)
        for key,value in computed.items():
            check(name+': independent '+key,np.isclose(value,float(metrics[name][key]),atol=1e-10,rtol=1e-10))
    # Compare two mathematically different implementations of the convex fit.
    params=replace(p.b2.LayoutParameters.from_preset('ring'),mode='base',optimizer_tolerance=1e-11)
    solver_errors=[]
    for t in [8,13,23,34,39]:
        orders=p.leaf_orders(sc['hier'][t])
        for order in [orders[0],orders[len(orders)//2],orders[-1]]:
            _,value,kkt=fit_gaps(sc['centers'][t],order,params.min_spacing_delta)
            leaves=tuple(sc['ids'][t][i] for i in order)
            x=p.b2.project_leaf_anchors(sc['frames'][t],leaves,params)
            d=np.array([np.linalg.norm(sc['centers'][t][order[i]]-sc['centers'][t][order[j]]) for i,j in combinations(range(len(order)),2)])
            projected=np.array([x[j]-x[i] for i,j in combinations(range(len(order)),2)])
            error=abs(np.sum((projected-d)**2)-value)/max(1.,value)
            solver_errors.append(float(error))
            check(f'frame {t} {order}: NNLS vs SLSQP',error<1e-7)
    # Arbitrary asymmetric graphs, including unary costs and forbidden edges.
    rng=np.random.default_rng(703)
    for run in range(12):
        sizes=[2,3,2,3];nodes=[list(range(n)) for n in sizes]
        edges=[rng.random((a,b)) for a,b in zip(sizes[:-1],sizes[1:])]
        if run%2:edges[0][1,2]=np.inf
        unary=[rng.random(n) for n in sizes]
        _,path,value=shortest_path(nodes,edges,unary)
        brute=min(sum(unary[t][z[t]] for t in range(4))+sum(edges[t][z[t],z[t+1]] for t in range(3)) for z in product(*nodes))
        check(f'DP brute force {run}',abs(value-brute)<1e-12)
    frame=read_csv('frame_oracles.csv')
    check('all 746 legal orders enumerated',sum(int(v['orders']) for v in frame)==746)
    for v in read_csv('candidates.csv'):
        bound=float(frame[int(v['t'])]['relaxed_SNS_infimum'])
        check('relaxed bound <= candidate SNS',bound<=float(v['SNS'])+1e-9)
    for row in frame:
        check('relaxed bound <= ST baseline SNS',float(row['relaxed_SNS_infimum'])<=float(row['ST_SNS'])+1e-9)
    summary=json.loads((OUT/'summary.json').read_text())
    check('baseline overlap independently reconstructed',summary['baseline_overlap']==summary['baseline_reported_overlap'])
    check('original geometry stop condition retained',summary['geometry_gate_passed_by']==[])
    # Verify finite stored rasters and every extracted leaf/branch signature.
    for name in paths:
        image=np.load(OUT/(name+'_map.npz'))['values']
        check(name+': common raster budget',image.shape==(196,40) and np.isfinite(image).all())
        for t,tr in enumerate(sc['trees']):
            check(name+f': raster topology frame {t}',p.signature(image[:,t],tr.kind)==p.signature(tr))
    p.save(OUT/'verification.json',dict(status='pass',checks=len(checks),
        max_NNLS_SLSQP_relative_objective_difference=max(solver_errors),
        coverage=['independent SNS TW distance temporal formulas for all paths',
                  'NNLS compared with existing SLSQP on 15 fits','DP compared with brute force on 12 graphs',
                  'all enumerated candidates above relaxed SNS bound','all output raster topology signatures'],
        note='Numerical verification, not statistical significance or a general topology theorem.'))
    print(f'PASS: {len(checks)} checks; solver relative difference {max(solver_errors):.3g}')


if __name__=='__main__':main()
