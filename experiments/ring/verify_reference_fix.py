"""Causal regressions and an unretouched before/after reference comparison."""
from pathlib import Path
import sys
import json
import csv
from dataclasses import replace
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from experiments.ring.run_experiment import pipeline, OUT, CANVAS, LENGTH
from experiments.ring.dataset import generate
import ramtm.error_budget as eb


def main():
    tests=[]
    def check(name,ok):
        assert ok,name
        tests.append(dict(check=name,status='pass'))
    fields,coords,meta=generate()
    sc=pipeline.scene_from_fields(fields,coords,CANVAS**2/196,'split')
    factor=CANVAS/pipeline.C
    p=replace(pipeline.P,canvas=CANVAS,width_scale=1/(2*CANVAS),
              gap=pipeline.P.gap*factor,extra_budget=pipeline.P.extra_budget*factor)
    new=json.loads((OUT/'RA-MTM_records.json').read_text())
    legacy=pipeline.run_method(sc,'RA-MTM',replace(p,rho=.5),canvas=CANVAS,length=LENGTH,
                              refine_raster=False,strict_checks=False,ramtm_reference='centroid')
    before=OUT/'reference_fix_before'
    if before.exists():
        old=json.loads((before/'RA-MTM_records.json').read_text())
        check('legacy path reproduces archived original layouts',all(np.allclose(a['x'],b['x'],atol=1e-9,rtol=0) for a,b in zip(old['rows'],legacy['rows'])))
        for method in ['TMTM','ST-MTM']:
            a=np.load(before/(method+'_map.npz'))['values']
            b=np.load(OUT/(method+'_map.npz'))['values']
            check(method+' raster byte-identical to before fix',np.array_equal(a,b))
            a=json.loads((before/(method+'_records.json')).read_text())
            b=json.loads((OUT/(method+'_records.json')).read_text())
            check(method+' continuous anchors unchanged',all(np.array_equal(x['x'],y['x']) for x,y in zip(a['rows'],b['rows'])))
        check('raw input unchanged',json.loads((before/'provenance.json').read_text())['sha256_tyx']==meta['sha256_tyx'])
        check('shared tree digest unchanged',(before/'shared_tree_digest.json').read_bytes()==(OUT/'shared_tree_digest.json').read_bytes())
        check('evaluation tracking unchanged',(before/'tracking.csv').read_bytes()==(OUT/'tracking.csv').read_bytes())
    for t,(r,a,fr,ids) in enumerate(zip(new['rows'],sc['areas'],sc['frames'],sc['ids'])):
        q=fr.coordinates[ids,0]
        check(f'frame {t}: absolute width and extremum reference',np.array_equal(r['reference'],q) and np.allclose(r['w'],p.width_scale*a,rtol=0,atol=1e-12))
        check(f'frame {t}: hierarchy and budget certificate',tuple(r['order']) in eb.leaf_orders(sc['hier'][t]) and max(abs(np.array(r['x'])-q))<=r['budget']+1e-6 and r['global_gap_bound']<.01)
    events=[]
    for info in sc['tracking']:
        t=info['t'];i=sc['ids'][t].index(info['current']);j=sc['ids'][t-1].index(info['previous'])
        old_step=legacy['rows'][t]['x'][i]-legacy['rows'][t-1]['x'][j]
        new_step=new['rows'][t]['x'][i]-new['rows'][t-1]['x'][j]
        qstep=new['rows'][t]['reference'][i]-new['rows'][t-1]['reference'][j]
        events.append(dict(t=t,leaf=info['current'],previous_leaf=info['previous'],iou=info['iou'],
            centroid_step=sc['centers'][t][i,0]-sc['centers'][t-1][j,0],extremum_step=qstep,
            old_layout_step=float(old_step),new_layout_step=float(new_step),
            budget_sum=new['rows'][t]['budget']+new['rows'][t-1]['budget']))
    event=next(r for r in events if r['t']==8 and r['leaf']==43)
    check('stationary extremum at the reported split',event['extremum_step']==0.)
    check('split no longer inherits leaf-support centroid displacement',abs(event['new_layout_step'])<=event['budget_sum']+1e-6 and abs(event['old_layout_step'])>event['budget_sum'])
    pipeline.table(OUT/'reference_transition_diagnostics.csv',events)

    # A support changes even though its point reference stays fixed. Check both
    # join/split use cases through explicit point references; no smoothing rule.
    tiny=replace(eb.Parameters(),rho=1.,extra_budget=0.)
    a=eb.solve_frame([[60.,40.]],[1000.],0,p=tiny,reference=[10.])
    b=eb.solve_frame([[100.,40.]],[1.],0,previous=a['x'],previous_q=[10.],p=tiny,reference=[10.],temporal_confidence=[.001])
    check('stationary reference survives support/area replacement',abs(a['x'][0]-10)<1e-8 and abs(b['x'][0]-10)<1e-8)
    c=np.array([[30.,20.],[70.,30.]])
    fixed=replace(tiny,extra_budget=1.)
    one=eb.solve_frame(c,[100,100],(0,1),p=fixed,reference=[25.,65.])
    two=eb.solve_frame(c+np.array([5.,0.]),[100,100],(0,1),p=fixed,reference=[30.,70.])
    check('true reference translation is preserved',np.allclose(two['x']-one['x'],5.,atol=1e-5))
    # Backwards-compatible API and analytical gradients under confidence weights.
    old=eb.solve_frame(c,[100,100],(0,1))
    explicit=eb.solve_frame(c,[100,100],(0,1),reference=c[:,0],temporal_confidence=[1,1])
    check('centroid API compatibility',np.allclose(old['x'],explicit['x'],atol=1e-10))
    real_minimize=eb.minimize;errors=[]
    def inspect(fun,x,jac,**kwargs):
        eps=1e-4;eye=np.eye(len(x))
        fd=np.array([(fun(x+eps*d)-fun(x-eps*d))/(2*eps) for d in eye])
        errors.append(float(max(abs(fd-jac(x)))))
        return real_minimize(fun,x,jac=jac,**kwargs)
    try:
        eb.minimize=inspect
        eb.solve_frame(c,[100,100],(0,1),previous=[26.,np.nan],previous_q=[25.,np.nan],p=fixed,
            matched=[True,False],reference=[25.,65.],temporal_confidence=[.01,0.])
    finally:
        eb.minimize=real_minimize
    check('confidence-weighted masked gradient',max(errors)<1e-6)
    zero=eb.solve_frame(c,[100,100],(0,1),previous=[100.,0.],previous_q=[25.,65.],p=fixed,
                       reference=[25.,65.],temporal_confidence=[0.,0.])
    check('zero-confidence matches exert no temporal force',np.allclose(zero['x'],one['x'],atol=1e-8))
    for kw in [dict(reference=[np.nan,1.]),dict(reference=[1.]),dict(temporal_confidence=[-1.,1.]),dict(temporal_confidence=[np.inf,1.])]:
        try:
            eb.solve_frame(c,[100,100],(0,1),**kw)
        except ValueError:
            ok=True
        else:
            ok=False
        check('invalid reference/confidence rejected '+str(kw),ok)
    newmap=np.load(OUT/'RA-MTM_map.npz')['values']
    plt=pipeline.plt
    fig,axes=plt.subplots(1,2,figsize=(12,5.5),layout='constrained')
    for ax,data,title in zip(axes,[legacy['maps'],newmap],['Before: support-centroid reference','After: extremum reference']):
        im=ax.imshow(data,origin='lower',aspect='auto',extent=[-.5,39.5,0,CANVAS],cmap='magma',
                     vmin=float(fields.min()),vmax=float(fields.max()),interpolation='nearest')
        ax.axvline(7.5,color='cyan',lw=.8,ls='--')
        ax.set(title=title,xlabel='Time step',ylabel='Fixed world x coordinate')
    fig.colorbar(im,ax=axes,label='Scalar value',shrink=.8)
    fig.suptitle(f"Same raw fields, trees, widths and metrics | t=7 to 8 displacement: {abs(event['old_layout_step']):.2f} → {abs(event['new_layout_step']):.2f}")
    fig.savefig(ROOT/'results/main/figures/ring_reference_fix.png',dpi=180);plt.close(fig)
    def table(path):
        with path.open() as f:return list(csv.DictReader(f))
    current=next(r for r in table(OUT/'comparison.csv') if r['Method']=='My Method')
    summary=dict(checks=tests,count=len(tests),split_event=event,max_gradient_error=max(errors),
        algorithm_changes=['explicit extremum references distinct from centroid geometry','rho=1 admits off-center extrema without changing widths','IoU-weighted residual temporal term'],
        unchanged=['input field','tree extraction','supports and absolute areas','shared tracking','baseline methods and parameters','SNS/TW/TD definitions'],
        new_metrics=current,
        limitation='Coarse-grid extremum switches and hierarchy conflicts can still create jumps. This fixes support-induced false motion, not all temporal discontinuities; full-sequence TD can increase.')
    pipeline.save(OUT/'reference_fix_verification.json',summary)
    print(f'PASS {len(tests)} reference-fix checks; split displacement {abs(event["old_layout_step"]):.6f} -> {abs(event["new_layout_step"]):.6f}')


if __name__=='__main__':main()
