"""Optimal barrier filling rendered into real maps (verifies attainable.delta* on the rendered columns).

Given a rendered column (LCA-path filling) and its anchors, replace every inter-anchor segment's peak
(join convention; split trees are negated) by the optimal barrier b_k = C_k + delta*, clipping the segment
to <= b_k and raising its existing peak to b_k if needed. Anchors, widths and order are unchanged; hierarchy-consistent
frames have delta* = 0 and b_k = f(lca(k, k+1)), i.e. the merge tree is still exact.
Run: .venv/bin/python -W ignore prototypes/filling.py   (checks measured d_top == delta* on all datasets)
"""
from pathlib import Path
import sys, json
from itertools import combinations
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import relax_hierarchy as rh, replicate as rp, task_reference as tr
from experiments import era5 as ep

OUT = tr.OUT
CAPS = [0., .02, .2, np.inf]


CLEARANCE = 1e-6          # barrier clearance above adjacent leaf values (fraction of |value|+1): keeps extrema strict


def barriers(order_ids, fr, s):
    n = len(order_ids)
    P = np.full((n, n), np.nan)
    for i, j in combinations(range(n), 2): P[i, j] = s * float(fr.values[fr.lca(order_ids[i], order_ids[j])])
    C = np.array([min(P[i, j] for i in range(k + 1) for j in range(k + 1, n)) for k in range(n - 1)])
    f = np.array([s * float(fr.values[x]) for x in order_ids]); ell = np.maximum(f[:-1], f[1:])
    d = max([0.] + [(P[i, j] - C[i:j].max()) / 2 for i, j in combinations(range(n), 2)] + list(ell - C))
    b = C + d
    if d > 0: b = np.maximum(b, ell + CLEARANCE * (1 + np.abs(ell)))   # relaxed columns only: keep extrema strict
    return b, d


def optimal_fill(col, order_ids, anchors, fr, kind):
    s = -1. if kind == 'split' else 1.; g = s * np.asarray(col, float).copy()
    if len(order_ids) < 2: return col.copy(), 0.
    b, d = barriers(order_ids, fr, s)
    for k in range(len(order_ids) - 1):
        lo, hi = sorted((int(anchors[k]), int(anchors[k + 1])))
        assert hi - lo >= 2, 'anchors must be separated by at least one pixel'
        seg = g[lo + 1:hi]; np.minimum(seg, b[k], out=seg)
        if seg.max() < b[k]: seg[np.argmax(seg)] = b[k]          # raise the existing peak: no new extrema
    return s * g, d


def main():
    res = {}
    for name in rp.LOADERS:
        ds = rp.LOADERS[name](); sc = ds['sc']; kind = sc['trees'][0].kind; rng = float(np.ptp(sc['fields']))
        res[name] = []
        for cap in CAPS:
            o = rh.run(ds, cap, make_figure=False, return_internal=True)['_internal']
            rows = o['results']['R_relaxed']['_rows']
            maps, dsk, _ = rh.render(sc, rows, o['p'], ds['nominal'])
            me_lca = rh.merge_errors(sc, maps, dsk, kind)
            opt = maps.astype(float).copy(); ds_ = []
            for t, (fr, sk) in enumerate(zip(sc['frames'], dsk)):
                opt[:, t], d = optimal_fill(maps[:, t], list(sk.ordering), sk.anchors, fr, kind); ds_.append(d)
            me_opt = rh.merge_errors(sc, opt, dsk, kind)
            Dl = np.array([m.max() if len(m) else 0. for m in me_lca]); Do = np.array([m.max() if len(m) else 0. for m in me_opt])
            sig = 0
            for t, tree in enumerate(sc['trees']):
                try: sig += ep.signature(opt[:, t], tree.kind) == ep.signature(tree)
                except ValueError: pass
            sig_lca = 0
            for t, tree in enumerate(sc['trees']):
                try: sig_lca += ep.signature(maps[:, t], tree.kind) == ep.signature(tree)
                except ValueError: pass
            changed = np.abs(opt - maps) > 1e-9
            r = dict(cap=cap, pixels_changed_share=float(changed.mean()), columns_changed=int(changed.any(0).sum()),
                     D_lca_share=float(Dl.max() / rng), D_opt_share=float(Do.max() / rng),
                     mean_lca_share=float(Dl.mean() / rng), mean_opt_share=float(Do.mean() / rng),
                     measured_vs_closed_form_max=float(np.max(np.abs(Do - np.array(ds_))) / rng),
                     topology_exact_frames=int(sig), topology_exact_frames_lca=int(sig_lca), frames=len(Do))
            res[name].append(r)
            print(f"{name:10s} cap {cap}: max d_top LCA {r['D_lca_share']:.3f} -> optimal {r['D_opt_share']:.3f} (mean {r['mean_lca_share']:.3f} -> {r['mean_opt_share']:.3f}); "
                  f"|measured - delta*| {r['measured_vs_closed_form_max']:.1e}; exact-topology frames opt {sig} / LCA {sig_lca} of {len(Do)}", flush=True)
    (OUT / 'filling.json').write_text(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
