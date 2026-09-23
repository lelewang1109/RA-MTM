"""Independent checks of Ring input, persisted layouts, metrics and provenance."""
from pathlib import Path
import sys
import ast
import json
import csv
import hashlib
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from experiments.ring.run_experiment import OUT, DATA, CANVAS, METHODS, DISPLAY, pipeline
from experiments.ring.dataset import SOURCE, generate, persistence_audit


def read_csv(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def main():
    from experiments.ring.verify_reference_fix import main as verify_reference_fix
    verify_reference_fix()
    checks = []
    def check(name, ok):
        if not ok:
            raise AssertionError(name)
        checks.append(dict(check=name, status='pass'))
    fields, coords, provenance = generate()
    saved = np.load(DATA/'ring.npz')
    check('exact source shape and finite values', fields.shape==(40,14,14) and np.isfinite(fields).all())
    check('saved field byte identity', np.array_equal(saved['fields'], fields))
    check('input SHA256', json.loads((OUT/'provenance.json').read_text())['sha256_tyx']==hashlib.sha256(fields.tobytes()).hexdigest())
    # Execute just the inspected, archived original mathematical class; no
    # Inviwo processor or any upstream method is loaded.
    tree = ast.parse((SOURCE/'SpreadingRingGeneration.py').read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name=='spreading_ring')
    namespace = {'np': np}
    exec(compile(ast.Module(body=[cls], type_ignores=[]), '<original-ring-class>', 'exec'), namespace)
    cfg = provenance['actual_float32_property_values']
    ring = namespace['spreading_ring'](np.array(cfg['center']), cfg['peak0'], cfg['peakChange'],
        cfg['mu0'], cfg['muChange'], cfg['omega0'], cfg['omegaChange'])
    x,y = np.mgrid[0:210:14j,0:210:14j]
    original = np.array([ring.evaluate(np.dstack((x,y)),t).T.astype(np.float32) for t in range(40)])
    check('bitwise equality with archived original formula', np.array_equal(original,fields))
    check('radius expands over all frames', np.all(np.diff([cfg['mu0']+t*cfg['muChange'] for t in range(40)])>0))
    sc = pipeline.scene_from_fields(fields, coords, CANVAS**2/196, 'split')
    counts = persistence_audit(sc['trees'])
    check('shared feature range 1-7', (min(len(v) for v in sc['ids']),max(len(v) for v in sc['ids']))==(1,7))
    check('shared supernode range 2-14', (min(len(v.nodes) for v in sc['trees']),max(len(v.nodes) for v in sc['trees']))==(2,14))
    check('p=.001 cancellation is a no-op', all(r['canceled_features']==0 for r in counts))
    recorded = json.loads((OUT/'shared_tree_digest.json').read_text())
    check('shared tree file SHA256', recorded['sha256']==hashlib.sha256((DATA/'shared_trees.json').read_bytes()).hexdigest())
    loaded = pipeline.b2.load_frames_json(DATA/'shared_trees.json')
    check('shared neutral tree reload', all(np.array_equal(f.values,g.values) and f.children==g.children for f,g in zip(loaded,sc['frames'])))
    summaries = {r['Method']:r for r in read_csv(OUT/'comparison.csv')}
    timing = read_csv(OUT/'runtime_repeats.csv')
    for method in METHODS:
        output = json.loads((OUT/(method+'_records.json')).read_text())
        rows = output['rows']
        values = np.load(OUT/(method+'_map.npz'))['values']
        check(method+' finite complete raster', values.shape[1]==40 and np.isfinite(values).all())
        check(method+' 40 topology checks', all(pipeline.signature(values[:,t],'split')==pipeline.signature(tr) for t,tr in enumerate(sc['trees'])))
        sns=[];tw=[];td=0.
        for t,(c,row) in enumerate(zip(sc['centers'],rows)):
            x = np.asarray(row['x']); n=len(x)
            check(f'{method} frame {t} feature alignment', len(x)==len(sc['ids'][t]) and np.isfinite(x).all())
            d=np.sqrt(np.sum((c[:,None,:]-c[None,:,:])**2,axis=-1))
            e=abs(x[:,None]-x[None,:])
            alpha=np.sum(d*e)/np.sum(e*e) if np.sum(e*e)>0 else 0.
            sns.append(float(np.sum((d-alpha*e)**2)/np.sum(d*d)) if np.sum(d*d)>0 else 0.)
            if n>6:
                penalty=0
                for i in range(n):
                    before=sorted((j for j in range(n) if j!=i),key=lambda j:(d[i,j],j))
                    after=sorted((j for j in range(n) if j!=i),key=lambda j:(e[i,j],j))
                    penalty+=sum(before.index(j)+1-3 for j in set(after[:3])-set(before[:3]))
                tw.append(1-2*penalty/(n*3*(2*n-10)))
            if t:
                old=dict(zip(sc['ids'][t-1], rows[t-1]['x']))
                now=dict(zip(sc['ids'][t], x))
                td+=sum(abs(now[k]-old[v]) for k,v in sc['matches'][t].items())
        summary=summaries[DISPLAY[method]]
        check(method+' independent SNS/TW/TD formulas', np.allclose([np.mean(sns),np.mean(tw),td], [float(summary[k]) for k in ('SNS','TW','TD')],atol=1e-10,rtol=0))
        median=np.median([float(r['layout_render_seconds']) for r in timing if r['method']==DISPLAY[method]])
        check(method+' repeated runtime median', abs(median-float(summary['Runtime_seconds']))<1e-12)
    protocol=json.loads((OUT/'protocol.json').read_text())
    st=protocol['stmtm_parameters']
    check('unaltered ST-MTM paper preset', all(st[k]==v for k,v in dict(weights='uniform',total_leaf_extent_k=1.,reorder_threshold_r=.95,temporal_lambda=1.5,layout_length=196,start_timestep=0).items()))
    check('shared TW coverage', protocol['tw_valid_frames']==[23,34,39])
    check('all methods completed', json.loads((OUT/'status.json').read_text())['status']=='complete')
    pipeline.save(OUT/'verification.json',dict(checks=checks,count=len(checks)))
    # Ring-only evidence closure; do not relabel old Storms outputs as rerun.
    manifest=OUT/'manifest.json'
    paths=list(OUT.rglob('*'))+list(DATA.rglob('*'))+list((ROOT/'experiments/ring').rglob('*'))
    paths+=list((ROOT/'src/ramtm').rglob('*.py'))
    paths += [ROOT/'experiments/real_era5/run_experiment.py',ROOT/'scripts/run_all.py',ROOT/'pyproject.toml',ROOT/'results/main/ring_metrics.csv']
    paths+=list((ROOT/'results/main/figures').glob('ring_*.png'))
    paths=sorted(set(p for p in paths if p.is_file() and p!=manifest and '__pycache__' not in p.parts))
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    pipeline.save(manifest,dict(scope='Ring run only; existing other-dataset evidence is not re-certified',sha256=hashes))
    check('Ring manifest round trip', all(hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==v for k,v in hashes.items()))
    print(f'PASS {len(checks)} Ring checks; {len(hashes)} files hashed')


if __name__=='__main__':
    main()
