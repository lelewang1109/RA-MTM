"""ST-MTM best case (review v1, M7): parameter grid spanning the values of all four published presets
(weights uniform/inverse, reorder threshold r in {0.65, 0.85, 0.95}, temporal lambda in {0.05, 0.5, 1.5}).
For each dataset and configuration: reader-proxy reversal / miss / error (k = 2, eps = 2%) and NN preservation.
Output: prototypes/output/stmtm_grid.json.  Run: .venv/bin/python -W ignore prototypes/stmtm_grid.py [datasets]
"""
from pathlib import Path
import sys, json, itertools, time
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import replicate as rp, general_method as gm, task_reference as tr, eval_v2 as ev
from experiments import era5 as ep
from ramtm.reference_points import reference_points_from_frames

OUT = tr.OUT
GRID = list(itertools.product(['uniform', 'inverse'], [.65, .85, .95], [.05, .5, 1.5]))


def main():
    names = sys.argv[1:] or ['era5', 'era5_2014', 'wildfire', 'ring']
    path = OUT / 'stmtm_grid.json'; res = json.loads(path.read_text()) if path.exists() else {}
    for name in names:
        ds = rp.LOADERS[name](); sc = ds['sc']; t0 = time.perf_counter()
        ext = reference_points_from_frames(sc['frames'], sc['ids'], kind='extremum')
        ref = gm.auto_reference(sc, ext, ds['lo'], ds['hi'])
        p = gm.universal_parameters(ref['origin'], ref['extent'], ds['domain_area']); theta = gm.THETA_FRACTION * p.canvas
        span = ds['native_span']
        px = gm.Parameters(canvas=span, canvas_origin=float(min(ds['lo'][0], 0.)), width_scale=.5 * span / ds['domain_area'],
                           gap=span / 240, extra_budget=span / 120, rho=.5)
        diag = float(np.linalg.norm(ds['hi'] - ds['lo'])); qs = [np.asarray(q, float) for q in ref['qs']]
        L = 196 if name == 'ring' else ds['nominal']
        K = 1. if name == 'ring' else float(px.width_scale * sc['areas'][0].sum())
        rows = []
        for w, r, lam in GRID:
            prm = ep.b2.LayoutParameters(w, K, r, lam, L, 0, min_spacing_delta=.01, optimizer_tolerance=1e-11)
            try:
                out = ep.run_method(sc, 'ST-MTM', px, canvas=span, length=L, stmtm_parameters=prm, refine_raster=False, strict_checks=False)
            except Exception as e:
                rows.append(dict(weights=w, r=r, lam=lam, error=str(e)[:120])); continue
            U = [np.asarray(x['pixel_x'], float) for x in out['rows']]
            extent = max(max(u.max() for u in U) - min(u.min() for u in U), 1e-9)
            W = ev.windows(sc, ext, U, extent, 2, .02, diag, qs, theta)
            s = ev.summary(W, np.random.default_rng(0)); h = ev.hidden_costs(sc, ext, U, extent)
            rows.append(dict(weights=w, r=r, lam=lam, reversal=s['reversal'], miss=s['miss'], error=s['error'],
                             nn=h['nn_preservation'], flips=h['order_flip_rate']))
            print(f"{name:10s} {w:8s} r={r:.2f} lambda={lam:<4} rev {s['reversal']:.3f} err {s['error']:.3f} NN {h['nn_preservation']:.3f}", flush=True)
        ok = [x for x in rows if 'reversal' in x]
        res[name] = dict(grid=rows, best_reversal=min(ok, key=lambda x: x['reversal']), best_error=min(ok, key=lambda x: x['error']),
                         seconds=time.perf_counter() - t0)
        path.write_text(json.dumps(res, indent=1))
        b = res[name]['best_reversal']; e = res[name]['best_error']
        print(f"== {name}: best reversal {b['reversal']:.3f} ({b['weights']}, r={b['r']}, lambda={b['lam']}), best error {e['error']:.3f}", flush=True)


if __name__ == '__main__':
    main()
