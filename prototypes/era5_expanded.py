"""ERA5 extraction on an expanded domain without boundary-induced minima (2026-09-27).

The protocol window (30-75N, 30W-40E; 49x49 equal-area cells, 250 km Gaussian smoothing) is unchanged: every cell
centre, coordinate, area unit and parameter is identical to experiments/era5.py::extract. What changes:
1. The same equal-area grid is extended by BUF cells west/east/south and as far north as the pole allows, on the
   expanded download (prototypes/era5_arco_expanded.py). Interpolation and smoothing run on the extended grid, so
   smoothing near the window edge uses real data instead of reflection.
2. A leaf is admissible iff it is a strict local minimum of the extended smoothed field (Freudenthal 6-neighbourhood,
   the adjacency of the merge-tree sweep) located inside the window.
3. After cropping, every basin without an admissible minimum is filled to its spill level (priority flood with an
   increment EPS far below the 1e-7-hPa-rounded topology signature and every reported number), i.e. minima imposition.
   The merge tree of the filled field has exactly the admissible minima as leaves; cut flanks of lows whose centre lies
   outside the window no longer appear as features.
The filled fields go to experiments/era5.py::scene_from_fields unchanged. Unfilled smoothed fields: sc['fields_smooth'].
Run (self-check): .venv/bin/python -W ignore prototypes/era5_expanded.py
"""
from pathlib import Path
import sys, heapq
import numpy as np
from netCDF4 import Dataset, num2date
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'src'))
from experiments import era5 as ep

R, PHI, C = ep.R, ep.PHI, ep.C
WINDOW = dict(lat=(30., 75.), lon=(-30., 40.))            # protocol window (bounds of the CDS / 12h_arco files)
BUF = 10                                                   # cells; 10 x ~97 km >= 4 sigma of the 250 km smoothing
# Main setting (decided 2026-09-27): the largest window inside the expanded download that keeps a smoothing buffer
# of >= 5 cells (~620 km, 2.5 sigma) on the south/west/east sides; north side limited by the pole (>= 3 cells).
MAIN_WINDOW = dict(lat=(25., 80.), lon=(-40., 50.))
MAIN_BUF = 5
EPS = 1e-5                                                 # hPa
NB = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)]  # Freudenthal (TTK) 2-D adjacency used by the sweep
FILES = {'1999': ROOT / 'data/real/ERA5_MSLP/ERA5_MSLP_19991117_20000114_12h_arco_expanded.nc',
         '2014': ROOT / 'data/real/ERA5_MSLP/ERA5_MSLP_20131201_20140131_12h_arco_expanded.nc'}


def strict_minima(f):
    """Strict local minima (all 6 Freudenthal neighbours higher), excluding the grid border."""
    c = f[1:-1, 1:-1]; m = np.ones_like(c, bool)
    for dy, dx in NB: m &= f[1 + dy:f.shape[0] - 1 + dy, 1 + dx:f.shape[1] - 1 + dx] > c
    out = np.zeros_like(f, bool); out[1:-1, 1:-1] = m
    return out


def impose_minima(f, markers):
    """Priority flood from the markers: result >= f, equals f at markers, and every other cell has a strictly lower
    Freudenthal neighbour, so the markers are the only minima of the result."""
    ny, nx = f.shape; g = np.full_like(f, np.nan); h = []
    for i, j in zip(*np.nonzero(markers)): g[i, j] = f[i, j]; heapq.heappush(h, (f[i, j], i, j))
    while h:
        v, i, j = heapq.heappop(h)
        for dy, dx in NB:
            a, b = i + dy, j + dx
            if 0 <= a < ny and 0 <= b < nx and np.isnan(g[a, b]):
                g[a, b] = max(f[a, b], v + EPS); heapq.heappush(h, (g[a, b], a, b))
    return g


def extract(path, grid=49, sigma=250., buf=BUF, window=WINDOW):
    co = np.cos(np.deg2rad(PHI))
    bx = R * co * np.deg2rad(window['lon']); by = R * np.sin(np.deg2rad(window['lat'])) / co
    dx = np.diff(bx)[0] / grid; dy = np.diff(by)[0] / grid
    north = int(np.floor((R / co * np.sin(np.deg2rad(89.9)) - by[1]) / dy)); bn = min(buf, north)
    ix = np.arange(-buf, grid + buf); iy = np.arange(-buf, grid + bn)
    X, Y = np.meshgrid(bx[0] + (ix + .5) * dx, by[0] + (iy + .5) * dy)
    pts = np.c_[np.rad2deg(np.arcsin(Y.ravel() * co / R)), np.rad2deg(X.ravel() / R / co)]
    span = float(np.hypot(np.diff(bx)[0], np.diff(by)[0])); factor = C / span
    Xw, Yw = X[buf:buf + grid, buf:buf + grid], Y[buf:buf + grid, buf:buf + grid]
    xy = np.c_[(Xw.ravel() - bx[0]) * factor, (Yw.ravel() - by[0]) * factor]
    corners = np.array([[0, 0], [np.diff(bx)[0] * factor, np.diff(by)[0] * factor]])
    coords = xy - corners.mean(0) + C / 2                  # angle = 0 of the protocol
    area = dx * dy * factor ** 2
    smooth, filled, stats = [], [], []
    with Dataset(path) as d:
        lat = np.asarray(d['latitude'][:]); lon = np.asarray(d['longitude'][:])
        assert pts[:, 0].min() >= lat.min() and pts[:, 0].max() <= lat.max() and pts[:, 1].min() >= lon.min() and pts[:, 1].max() <= lon.max()
        tm = d['valid_time']; dates = [str(v) for v in num2date(tm[:], tm.units)]
        for t in range(len(dates)):
            f = np.asarray(d['msl'][t], float) / 100
            big = RegularGridInterpolator((lat, lon), f)(pts).reshape(len(iy), len(ix))
            big = gaussian_filter(big, (sigma / dy, sigma / dx), mode='reflect')
            w = big[buf:buf + grid, buf:buf + grid]
            mk = strict_minima(big)[buf:buf + grid, buf:buf + grid]
            if not mk.any(): mk = np.zeros_like(w, bool); mk[np.unravel_index(np.argmin(w), w.shape)] = True
            g = impose_minima(w, mk)
            cropmin = strict_minima(np.pad(w, 1, constant_values=np.inf))[1:-1, 1:-1]
            stats.append(dict(t=t, true_minima=int(mk.sum()), crop_minima=int(cropmin.sum()),
                              max_fill_hPa=float((g - w).max()), filled_cells=int((g - w > 1e-3).sum())))
            smooth.append(w); filled.append(g)
    sc = ep.scene_from_fields(filled, coords, area, 'join')
    for t, s in enumerate(stats): assert len(sc['ids'][t]) == s['true_minima'], (t, len(sc['ids'][t]), s)
    sc.update(fields_smooth=np.array(smooth), dates=dates, fill_stats=stats,
              protocol=dict(grid=grid, smoothing_sigma_km=sigma, buffer_cells=buf, buffer_north_cells=bn, cell_area_km2=dx * dy,
                            cell_area_layout=area, layout_unit_km=1 / factor, minima='strict minima of the extended field inside the window; other basins filled (priority flood, eps=1e-5 hPa)'))
    return sc


def loader(season, name, sigma=250., window=MAIN_WINDOW, buf=MAIN_BUF):
    sc = extract(FILES[season], sigma=sigma, buf=buf, window=window); sc['window'] = window
    cell = sc['protocol']['cell_area_layout']; grid = sc['protocol']['grid']
    return dict(name=name, sc=sc, lo=sc['coords'].min(0), hi=sc['coords'].max(0), domain_area=grid * grid * cell,
                nominal=4096, cmap='RdBu_r', vrange=(1013.25 - 35, 1013.25 + 35), native_span=120.)


if __name__ == '__main__':
    import json
    ep.SOURCE = (ROOT / 'data/real/ERA5_MSLP/ERA5_MSLP_19991117_20000114_12h_arco.nc').resolve()
    old = ep.extract(step=1)
    for season in ['1999', '2014']:
        if not FILES[season].exists(): print('missing', FILES[season]); continue
        sc = extract(FILES[season]) if season == '1999' else extract(FILES[season], buf=MAIN_BUF, window=MAIN_WINDOW)
        if season == '1999':
            assert np.allclose(sc['coords'], old['coords']), 'coords differ from protocol'  # protocol window, BUF=10
            print('coords identical to protocol; max |smooth - protocol field| (hPa) =', float(np.abs(sc['fields_smooth'] - old['fields']).max()))
        n = np.array([len(i) for i in sc['ids']]); st = sc['fill_stats']
        print(season, 'frames', len(n), 'leaves/frame mean %.2f min %d max %d' % (n.mean(), n.min(), n.max()),
              'crop minima/frame %.2f' % np.mean([s['crop_minima'] for s in st]),
              'max fill %.1f hPa' % max(s['max_fill_hPa'] for s in st), 'boundary features', int(sum(map(sum, sc['boundary']))))
