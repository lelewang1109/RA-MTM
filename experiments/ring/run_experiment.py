"""Ring dataset adapter for the existing Storms/ERA5 three-method pipeline."""
from pathlib import Path
import sys
import argparse
import hashlib
import platform
import shutil
import time
from dataclasses import asdict, replace
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from experiments.real_era5 import run_experiment as pipeline
from experiments.ring.dataset import generate, persistence_audit

b2 = pipeline.b2
OUT = ROOT/'results/supplementary/ring'
DATA = ROOT/'data/generated/ring'
CANVAS = 210.
LENGTH = 196
METHODS = pipeline.METHODS
DISPLAY = {'TMTM': 'TMTM', 'ST-MTM': 'ST-MTM', 'RA-MTM': 'My Method'}


def quality(sc, result, method):
    """Same SNS/TW(k=3)/summed matched TD as archived Storms evaluation."""
    rows = []
    for t, (c, row) in enumerate(zip(sc['centers'], result['rows'])):
        d = np.linalg.norm(c[:, None]-c[None, :], axis=-1)
        n = len(c)
        td = 0.
        if t:
            old = dict(zip(sc['ids'][t-1], result['rows'][t-1]['x']))
            now = dict(zip(sc['ids'][t], row['x']))
            td = sum(abs(now[k]-old[v]) for k, v in sc['matches'][t].items())
        rows.append(dict(t=t, method=DISPLAY[method], features=n,
                         SNS=b2.scale_normalized_stress(d, row['x']),
                         TW=b2.trustworthiness(c, row['x'], 3) if n > 6 else None,
                         TW_k1=b2.trustworthiness(c, row['x'], 1) if n > 2 else None,
                         TD=float(td)))
    valid = [r['TW'] for r in rows if r['TW'] is not None]
    return dict(Dataset='Ring', Method=DISPLAY[method],
                SNS=float(np.mean([r['SNS'] for r in rows])),
                TW=float(np.mean(valid)) if valid else None,
                TD=float(sum(r['TD'] for r in rows)),
                Runtime_seconds=result['compute_seconds']), rows


def figures(sc, results, counts):
    plt = pipeline.plt
    figdir = OUT/'figures'
    figdir.mkdir(parents=True, exist_ok=True)
    lo, hi = float(sc['fields'].min()), float(sc['fields'].max())
    fig, axes = plt.subplots(1, 5, figsize=(15, 3.6), layout='constrained')
    for ax, t in zip(axes, [0, 10, 20, 30, 39]):
        im = ax.imshow(sc['fields'][t], origin='lower', extent=[0, 210, 0, 210],
                       cmap='magma', vmin=lo, vmax=hi, interpolation='nearest')
        ax.set(title=f't = {t}', xlabel='x'); ax.set_ylabel('y')
    fig.colorbar(im, ax=axes, label='Scalar value', shrink=.7)
    fig.suptitle('Ring: unchanged author-generated scalar fields (14 x 14, 40 frames)')
    fig.savefig(figdir/'raw_fields.png', dpi=180); plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(14, 6), layout='constrained')
    for ax, method in zip(axes, METHODS):
        data = results[method]['maps']
        im = ax.imshow(data, origin='lower', aspect='auto', extent=[-.5, 39.5, 0, 1],
                       cmap='magma', vmin=lo, vmax=hi, interpolation='nearest')
        ax.set(title=f'{DISPLAY[method]}\nNative raster: {len(data)} samples', xlabel='Time step', ylabel='Map position / native extent')
    fig.colorbar(im, ax=axes, label='Scalar value', shrink=.7)
    fig.suptitle('Ring: three methods, shared fields / trees / tracking / color scale')
    fig.savefig(figdir/'comparison.png', dpi=200)
    fig.savefig(figdir/'comparison.svg'); plt.close(fig)
    for method in METHODS:
        fig, ax = plt.subplots(figsize=(6, 6), layout='constrained')
        im = ax.imshow(results[method]['maps'], origin='lower', aspect='auto',
                       cmap='magma', vmin=lo, vmax=hi, interpolation='nearest')
        ax.set(title=DISPLAY[method]+' — Ring', xlabel='Time step', ylabel='Native map sample')
        fig.colorbar(im, ax=ax, label='Scalar value')
        fig.savefig(figdir/(method+'.png'), dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(10, 3.5), layout='constrained')
    ax.step(range(40), [r['features'] for r in counts], where='mid', label='Leaf features')
    ax.step(range(40), [r['supernodes'] for r in counts], where='mid', label='Merge-tree supernodes')
    ax.set(xlabel='Time step', ylabel='Count', title='Shared tree extraction; p=0.001 removes no features')
    ax.legend(); fig.savefig(figdir/'feature_counts.png', dpi=180); plt.close(fig)


def main(repeats=3):
    OUT.mkdir(parents=True, exist_ok=True); DATA.mkdir(parents=True, exist_ok=True)
    pipeline.save(OUT/'status.json', dict(status='running'))
    start = time.perf_counter()
    fields, coords, provenance = generate()
    # Same fixed-domain equal-area capacity rule as Storms: complete domain
    # receives half the canvas in RA-MTM. Units change, dimensionless weights do not.
    sc = pipeline.scene_from_fields(fields, coords, CANVAS**2/196, 'split')
    counts = persistence_audit(sc['trees'])
    preprocessing_seconds = time.perf_counter()-start
    sc.update(dates=[str(t) for t in range(40)], indices=np.arange(40))
    factor = CANVAS/pipeline.C
    ra = replace(pipeline.P, canvas=CANVAS, width_scale=1/(2*CANVAS),
                 gap=pipeline.P.gap*factor, extra_budget=pipeline.P.extra_budget*factor)
    st = b2.LayoutParameters.from_preset('ring')
    protocol = dict(dataset='Ring', shared_input_sha256=provenance['sha256_tyx'],
                    methods=DISPLAY, stmtm_parameters=asdict(st), ramtm_parameters=asdict(ra),
                    persistence_fraction=.001, persistence_interpretation='fraction of each frame scalar range; all finite pairs exceed threshold, so no-op',
                    input_modifications='none; source float32 fields, shared split trees',
                    tree_builder='existing deterministic Freudenthal grid builder, not TTK; shared by all methods',
                    feature_definition='extremum plus regular vertices of incident leaf arc; shared centroids and supports',
                    ramtm_reference='extremum world x, separate from shared leaf-support centroid geometry',
                    ramtm_anchor_rule='rho=1: extremum may lie anywhere inside its own leaf interval; absolute widths unchanged',
                    ramtm_temporal_rule='residual motion in extremum reference coordinates, weighted by shared support IoU; births have zero temporal weight',
                    evaluation_reference='legacy centroid task metrics retained; extremum reference errors reported separately for every method',
                    correspondence='existing maximum-overlap positive-intersection Hungarian leaf matching',
                    coordinates='source x,y in [0,210]; all metric positions in common source-coordinate units',
                    tmtm_unit=CANVAS/195, ramtm_unit_conversion=factor,
                    baseline_gauge='existing one-time first-frame reflection and translation; no per-frame fit',
                    sns='existing scale_normalized_stress, mean of 40 frames; single-feature frame contributes zero',
                    tw='existing trustworthiness k=3; only shared frames N>6; undefined frames blank, not zero',
                    tw_valid_frames=[r['t'] for r in counts if r['features'] > 6],
                    td='existing summed absolute displacement across shared matched feature pairs; common physical units',
                    runtime='median of cyclic-order repeated layout+render wall times, excludes extraction, validation, evaluation, plotting, I/O; includes actual raster fallback',
                    runtime_repeats=repeats, shared_preprocessing_seconds=preprocessing_seconds,
                    raster='TMTM 196; ST-MTM fixed paper L=196 with no refinement; RA attempts same 196 then existing fixed doubling only if unrepresentable; failures disclosed',
                    platform=platform.platform(), python=sys.version, numpy=np.__version__)
    pipeline.save(OUT/'provenance.json', provenance); pipeline.save(OUT/'protocol.json', protocol)
    np.savez_compressed(DATA/'ring.npz', fields=fields, coordinates=coords, times=np.arange(40))
    pipeline.table(OUT/'feature_counts.csv', counts); pipeline.table(OUT/'tracking.csv', sc['tracking'])
    tree_records = [dict(timestep=f.timestep, root=f.root, children=f.children,
                         arcs=[asdict(a) for a in f.arcs.values()], values=f.values,
                         coordinates=f.coordinates, domain_min=f.domain_min, domain_max=f.domain_max)
                    for f in sc['frames']]
    pipeline.save(DATA/'shared_trees.json', dict(frames=tree_records))
    pipeline.save(OUT/'shared_tree_digest.json', dict(sha256=hashlib.sha256((DATA/'shared_trees.json').read_bytes()).hexdigest()))
    results = {}; timings = []
    for rep in range(repeats):
        for method in METHODS[rep % 3:]+METHODS[:rep % 3]:
            print(f'Ring repetition {rep+1}/{repeats}: {method}', flush=True)
            r = pipeline.run_method(sc, method, ra, canvas=CANVAS, length=LENGTH,
                                    stmtm_parameters=st, refine_raster=False, strict_checks=False)
            if method in results:
                assert np.array_equal(r['maps'], results[method]['maps']), 'nondeterministic map'
                for a, b in zip(r['rows'], results[method]['rows']):
                    np.testing.assert_allclose(a['x'], b['x'], atol=1e-10, rtol=0)
            else:
                results[method] = r
            timings.append(dict(repetition=rep, method=DISPLAY[method],
                                layout_render_seconds=r['compute_seconds'],
                                including_validation_seconds=r['seconds']))
            pipeline.table(OUT/'runtime_repeats.csv', timings)
    summaries = []; metrics = []; quality_frames = []; checks = []
    for method in METHODS:
        r = results[method]
        r['compute_seconds'] = float(np.median([v['layout_render_seconds'] for v in timings if v['method']==DISPLAY[method]]))
        summary, perframe = quality(sc, r, method)
        summaries.append(summary); quality_frames.extend(perframe)
        m, pf, feats = pipeline.evaluate(sc, r, method, canvas=CANVAS)
        m['first_run_including_validation_seconds'] = m.pop('seconds')
        tw1 = [v['TW_k1'] for v in perframe if v['TW_k1'] is not None]
        extremum_error=[abs(row['x']-fr.coordinates[ids,0])/CANVAS
                        for row,fr,ids in zip(r['rows'],sc['frames'],sc['ids'])]
        metrics.append(dict(**summary, **{k:v for k,v in m.items() if k!='method'},
                            extremum_reference_nmae=float(np.mean(np.concatenate(extremum_error))),
                            TW_valid_frames=sum(v['TW'] is not None for v in perframe),
                            TW_k1_mean=float(np.mean(tw1)), TW_k1_valid_frames=len(tw1)))
        pipeline.table(OUT/(method+'_task_frames.csv'), pf)
        pipeline.table(OUT/(method+'_features.csv'), feats)
        pipeline.save(OUT/(method+'_records.json'), dict(records=r['records'], rows=r['rows'], gauge=r['gauge']))
        np.savez_compressed(OUT/(method+'_map.npz'), values=r['maps'])
        for check in r['checks']:
            check['root_level_error_scalar'] = check.pop('root_level_error_hPa')
            checks.append(check)
    pipeline.table(OUT/'comparison.csv', summaries)
    pipeline.table(ROOT/'results/main/ring_metrics.csv', summaries)
    pipeline.table(OUT/'all_metrics.csv', metrics)
    pipeline.table(OUT/'quality_per_frame.csv', quality_frames)
    pipeline.table(OUT/'validity.csv', checks)
    figures(sc, results, counts)
    for name in ['comparison.png', 'raw_fields.png', 'feature_counts.png']:
        destination = ROOT/'results/main/figures'/('ring_'+name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(OUT/'figures'/name, destination)
    lines = ['| Dataset | Method | SNS ↓ | TW ↑ | TD ↓ | Runtime (s) ↓ |',
             '|---|---|---:|---:|---:|---:|']
    for row in summaries:
        lines.append(f"| Ring | {row['Method']} | {row['SNS']:.6f} | {row['TW']:.6f} | {row['TD']:.6f} | {row['Runtime_seconds']:.6f} |")
    (OUT/'comparison.md').write_text('\n'.join(lines)+f'\n\nTW: k=3, t=23,34,39 only; TD: summed matched displacement in common source-coordinate units. Runtime: median of {repeats} layout/render runs; extraction and validation excluded.\n')
    pipeline.save(OUT/'status.json', dict(status='complete', methods=list(DISPLAY.values()),
        shape_tyx=list(fields.shape), nonfinite_values=int((~np.isfinite(fields)).sum()),
        features_range=[min(r['features'] for r in counts), max(r['features'] for r in counts)],
        supernodes_range=[min(r['supernodes'] for r in counts), max(r['supernodes'] for r in counts)],
        tw_valid_frames=protocol['tw_valid_frames'],
        raster_summary={m:dict(length=results[m]['maps'].shape[0],
            topology_failed_frames=[v['t'] for v in results[m]['checks'] if not v['topology_equal']],
            collapsed_frames=[v['t'] for v in results[m]['checks'] if v['nominal_width_collapsed']]) for m in METHODS}))
    print(summaries, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repeats', type=int, default=3)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats must be positive')
    try:
        main(args.repeats)
    except BaseException as error:
        pipeline.save(OUT/'status.json', dict(status='failed', error=str(error)))
        raise
