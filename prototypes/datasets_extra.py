"""Additional real datasets for the replication study (loaders return the same dict as general_method).

wildfire : Franke et al. hierarchically aggregated FRP (Zenodo 11234747, CC-BY 4.0), 10 km level,
           Australia, 2019-11-01 .. 2019-12-30 in 2-day sums (30 frames). Preprocessing rules, fixed a priori:
             - equirectangular km coordinates, square bounding box of cells active in the window, 64x64 grid
             - value = log(1 + binned FRP [MW])
             - background = 1e-3 * broad Gaussian (sigma 16 cells, no truncation): removes the zero plateau
               (a flat plateau yields a spurious tie-broken maximum)
             - smoothing sigma = SMALLEST value in SIGMAS such that every frame has <= 12 split-tree leaves
               (tractability rule for exact certificates; ST-MTM used 15% persistence simplification instead)
era5_2014: ERA5 MSLP, same region/protocol as the main ERA5 study, winter 2013-12-01 .. 2014-01-31, 12-hourly.
"""
from pathlib import Path
import json
import numpy as np
from scipy.ndimage import gaussian_filter
import general_method as gm
from experiments import era5 as ep

ROOT = Path(__file__).resolve().parents[1]
WILDFIRE = ROOT / 'data/real/wildfire/wildfire.json'
ERA5_2014 = ROOT / 'data/real/ERA5_MSLP/ERA5_MSLP_20131201_20140131_12h_arco.nc'
SIGMAS = [1., 1.5, 2., 2.5, 3., 4., 5., 6., 8.]
GRID, SPAN = 64, 120.


def _wildfire_fields():
    d = json.loads(WILDFIRE.read_text())
    series = d['timeseries']['series']; i0 = series.index('2019-11-01'); n_days = 60
    cells = [c for top in d['data'] for c in (top.get('children') or [])]          # 10 km level
    lat = np.array([c['lat'] for c in cells]); lng = np.array([c['lng'] for c in cells])
    V = np.array([c['data'][i0:i0 + n_days] for c in cells], float)                   # cells x days
    V = V.reshape(len(cells), n_days // 2, 2).sum(-1)                                   # 2-day sums
    active = V.sum(1) > 0
    phi0 = np.deg2rad(np.mean(lat[active]))
    x = lng * np.cos(phi0) * 111.32; y = lat * 110.57
    x0, x1, y0, y1 = x[active].min(), x[active].max(), y[active].min(), y[active].max()
    side = max(x1 - x0, y1 - y0) * 1.02; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    ix = np.clip(((x - (cx - side / 2)) / side * GRID).astype(int), 0, GRID - 1)
    iy = np.clip(((y - (cy - side / 2)) / side * GRID).astype(int), 0, GRID - 1)
    raw = np.zeros((V.shape[1], GRID, GRID))
    for c in np.where(active)[0]: raw[:, iy[c], ix[c]] += V[c]
    dates = [series[i0 + 2 * t] for t in range(V.shape[1])]
    return np.log1p(raw), dates, dict(cells_10km=int(active.sum()), side_km=float(side), cell_km=float(side / GRID))


def _count_leaves(fields):
    from ramtm.baselines import tmtm as b1
    return max(sum(1 for n in b1.build_augmented_merge_tree(f, 'split').nodes.values() if not n.child_arcs) for f in fields)


def wildfire():
    L, dates, meta = _wildfire_fields()
    g = np.linspace(SPAN / GRID / 2, SPAN - SPAN / GRID / 2, GRID); X, Y = np.meshgrid(g, g)
    coords = np.c_[X.ravel(), Y.ravel()]
    for s in SIGMAS:
        F = np.array([gaussian_filter(f, s) for f in L])
        bg = np.array([gaussian_filter(f, 16., truncate=50.) for f in L])
        F = F + 1e-3 * np.ptp(F) * bg / max(bg.max(), 1e-12)
        if _count_leaves(F) <= 12: break
    meta.update(sigma_cells=s, sigma_km=s * meta['cell_km'], leaves_max=_count_leaves(F))
    sc = ep.scene_from_fields(F, coords, (SPAN / GRID) ** 2, 'split'); sc['dates'] = dates
    return dict(name='wildfire', sc=sc, lo=coords.min(0), hi=coords.max(0), domain_area=SPAN ** 2,
                nominal=2048, cmap='inferno', vrange=None, native_span=SPAN, meta=meta)


def era5_2014():
    ep.SOURCE = ERA5_2014.resolve()
    sc = ep.extract(step=1)
    cell = sc['protocol']['cell_area_layout']; grid = sc['protocol']['grid']
    return dict(name='era5_2014', sc=sc, lo=sc['coords'].min(0), hi=sc['coords'].max(0), domain_area=grid * grid * cell,
                nominal=4096, cmap='RdBu_r', vrange=(1013.25 - 35, 1013.25 + 35), native_span=120.)
