"""Preprocessing sensitivity (review v1, W8): do conflict prevalence and the RQ2 ranking depend on feature extraction?

ERA5 1999/2000 and 2013/14: smoothing sigma in {150, 250, 350} km (250 = main protocol).
Wildfire: leaf cap in {8, 10, 12} (12 = main protocol; the smallest smoothing meeting the cap is chosen).
Per variant: leaves per frame, conflict share (H > theta), and reader-proxy reversal / error (k = 2, eps = 2%)
for ST-MTM, A, R (kappa = 20%), and oracle q.
Output: prototypes/output/sensitivity.json.  Run: .venv/bin/python -W ignore prototypes/sensitivity.py [variants]
"""
from pathlib import Path
import sys, json
import numpy as np
from scipy.ndimage import gaussian_filter
sys.path.insert(0, str(Path(__file__).resolve().parent))
import datasets_extra as dx, general_method as gm, relax_hierarchy as rh, task_reference as tr, eval_v2 as ev
from experiments import era5 as ep

OUT = tr.OUT; ROOT = Path(__file__).resolve().parents[1]
ERA = dict(era5=ROOT / 'data/real/ERA5_MSLP/ERA5_MSLP_19991117_20000114_12h_arco.nc', era5_2014=dx.ERA5_2014)


def era5_variant(name, sigma):
    ep.SOURCE = ERA[name].resolve(); sc = ep.extract(step=1, sigma=sigma)
    cell = sc['protocol']['cell_area_layout']; grid = sc['protocol']['grid']
    return dict(name=name, sc=sc, lo=sc['coords'].min(0), hi=sc['coords'].max(0), domain_area=grid * grid * cell,
                nominal=4096, cmap='RdBu_r', vrange=None, native_span=120.)


def wildfire_variant(cap):
    L, dates, meta = dx._wildfire_fields()
    g = np.linspace(dx.SPAN / dx.GRID / 2, dx.SPAN - dx.SPAN / dx.GRID / 2, dx.GRID); X, Y = np.meshgrid(g, g)
    coords = np.c_[X.ravel(), Y.ravel()]
    for s in dx.SIGMAS:
        F = np.array([gaussian_filter(f, s) for f in L])
        bg = np.array([gaussian_filter(f, 16., truncate=50.) for f in L])
        F = F + 1e-3 * np.ptp(F) * bg / max(bg.max(), 1e-12)
        if dx._count_leaves(F) <= cap: break
    sc = ep.scene_from_fields(F, coords, (dx.SPAN / dx.GRID) ** 2, 'split'); sc['dates'] = dates
    return dict(name='wildfire', sc=sc, lo=coords.min(0), hi=coords.max(0), domain_area=dx.SPAN ** 2,
                nominal=2048, cmap='inferno', vrange=None, native_span=dx.SPAN, sigma_cells=s)


VARIANTS = {'era5_s150': lambda: era5_variant('era5', 150.), 'era5_s350': lambda: era5_variant('era5', 350.),
            'era5_2014_s200': lambda: era5_variant('era5_2014', 200.), 'era5_2014_s350': lambda: era5_variant('era5_2014', 350.),
            'wildfire_cap8': lambda: wildfire_variant(8), 'wildfire_cap10': lambda: wildfire_variant(10)}


def analyse(key):
    ds = VARIANTS[key](); sc = ds['sc']
    base = rh.run(ds, 0., make_figure=False)
    H = np.array([d['tau_hier'] - d['tau_free'] for d in base['frame_log']])
    M, ext, ref, p, theta, dstar = ev.methods(ds)
    diag = float(np.linalg.norm(ds['hi'] - ds['lo'])); qs = [np.asarray(q, float) for q in ref['qs']]
    rng = np.random.default_rng(0); proxy = {}
    for m in ['TMTM', 'ST-MTM', 'A', 'R 20%', 'oracle q']:
        W = ev.windows(sc, ext, M[m]['u'], M[m]['extent'], 2, .02, diag, qs, theta)
        proxy[m] = ev.summary(W, rng)
    n = [len(i) for i in sc['ids']]
    return dict(variant=key, frames=len(n), leaves_mean=float(np.mean(n)), leaves_max=int(max(n)),
                conflict_share=float(np.mean(H > base['theta'])), dstar_R20=dstar['R 20%'], proxy=proxy,
                sigma_cells=ds.get('sigma_cells'))


def main():
    keys = sys.argv[1:] or list(VARIANTS)
    path = OUT / 'sensitivity.json'; res = json.loads(path.read_text()) if path.exists() else {}
    for k in keys:
        r = analyse(k); res[k] = r; path.write_text(json.dumps(res, indent=1, default=float))
        pr = r['proxy']
        print(f"{k:16s} leaves {r['leaves_mean']:.1f} (max {r['leaves_max']}), conflicts {r['conflict_share']:.0%} | rev/err "
              + '  '.join(f"{m} {pr[m]['reversal']:.3f}/{pr[m]['error']:.3f}" for m in pr), flush=True)


if __name__ == '__main__':
    main()
