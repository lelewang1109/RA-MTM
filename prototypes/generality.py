"""Generality and scalability of the certificate beyond merge trees.

(a) Dendrogram-ordered dense pixel displays (Franke et al. 2021 style): 1024 active 10-km wildfire cells,
    one pixel row each (unit widths, no gap, canvas exactly n rows). Hierarchy = agglomerative clustering of
    the cells' FRP time series (data similarity, as in Franke et al.'s hierarchical orderings) or of their
    locations (control). Reference = position along the principal geographic axis, scaled to rows.
    tau_free (any order) = sorted assignment (equal widths); tau*(dendrogram) exact by DP.
(b) Scalability: exact DP time on random binary hierarchies with n up to 4096 leaves.
Run: .venv/bin/python -W ignore prototypes/generality.py
"""
from pathlib import Path
import sys, json, time
import numpy as np
from scipy.cluster.hierarchy import linkage, to_tree
sys.setrecursionlimit(100000)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import theory as th, datasets_extra as dx, task_reference as tr
from ramtm.error_budget import Parameters

OUT = tr.OUT


def dendro(Z):
    def rec(node): return int(node.id) if node.is_leaf() else [rec(node.left), rec(node.right)]
    return rec(to_tree(Z))


def cells():
    d = json.loads(dx.WILDFIRE.read_text()); series = d['timeseries']['series']; i0 = series.index('2019-11-01')
    cs = [c for top in d['data'] for c in (top.get('children') or [])]
    V = np.array([c['data'][i0:i0 + 60] for c in cs], float).reshape(len(cs), 30, 2).sum(-1)
    lat = np.array([c['lat'] for c in cs]); lng = np.array([c['lng'] for c in cs]); a = V.sum(1) > 0
    phi0 = np.deg2rad(lat[a].mean())
    xy = np.c_[lng[a] * np.cos(phi0) * 111.32, lat[a] * 110.57]
    return np.log1p(V[a]), xy


def main():
    X, xy = cells(); n = len(X)
    c = xy - xy.mean(0); a = np.linalg.eigh(c.T @ c)[1][:, -1]; proj = c @ a
    q = (proj - proj.min()) / np.ptp(proj) * (n - 1) + .5                # reference in row units
    p = Parameters(canvas=float(n), canvas_origin=0., width_scale=1., gap=0., rho=0., extra_budget=0.)
    w = np.ones(n)
    tau_free = float(np.max(abs(np.arange(n) + .5 - np.sort(q))))       # sorted assignment is optimal for equal widths
    res = dict(n=n, tau_free_rows=tau_free, hierarchies=[])
    Xc = X - X.mean(1, keepdims=True); Xc /= np.maximum(np.linalg.norm(Xc, axis=1, keepdims=True), 1e-12)
    q_rank = np.empty(n); q_rank[np.argsort(proj)] = np.arange(n) + .5   # rank reference: tau_free = 0 exactly
    res['rank_reference'] = []
    for label, Z in [('time-series, average linkage (correlation)', linkage(Xc, 'average', metric='euclidean')),
                     ('time-series, complete linkage', linkage(Xc, 'complete')),
                     ('time-series, Ward', linkage(Xc, 'ward')),
                     ('location, Ward (control)', linkage(xy, 'ward')),
                     ('location, single (control)', linkage(xy, 'single'))]:
        t0 = time.perf_counter(); tau = th.dp_tau(w, q, dendro(Z), p, n, tol=.25); dt = time.perf_counter() - t0
        res['hierarchies'].append(dict(hierarchy=label, tau_star_rows=tau, tau_star_share=tau / n,
                                       H_share=(tau - tau_free) / n, seconds=dt))
        tr_ = th.dp_tau(w, q_rank, dendro(Z), p, n, tol=.25)
        res['rank_reference'].append(dict(hierarchy=label, tau_star_rows=tr_, tau_star_share=tr_ / n))
        print(f"{label:45s} tau* = {tau:7.1f} rows ({tau / n:.1%} of n)   H = {(tau - tau_free) / n:.1%}   [{dt:.2f} s]   | rank reference: tau* = H = {tr_ / n:.1%}", flush=True)
    print(f"free (any order): tau_free = {tau_free:.1f} rows ({tau_free / n:.1%})")
    rng = np.random.default_rng(0); scal = []
    for m in [64, 256, 1024, 4096]:
        pts = rng.random((m, 2)); Z = linkage(pts, 'average'); N = 4 * m
        pp = Parameters(canvas=float(N), canvas_origin=0., width_scale=1., gap=1., rho=.5, extra_budget=0.)
        ww = rng.integers(1, 3, m).astype(float); qq = pts[:, 0] * N
        t0 = time.perf_counter(); th.dp_tau(ww, qq, dendro(Z), pp, N, tol=.5); dt = time.perf_counter() - t0
        scal.append(dict(leaves=m, pixels=N, seconds=dt)); print(f"scalability: n={m:5d} N={N:6d}  exact tau* in {dt:.2f} s", flush=True)
    res['scalability'] = scal
    (OUT / 'generality.json').write_text(json.dumps(res, indent=1, default=float))


if __name__ == '__main__':
    main()
