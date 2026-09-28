"""Alternative to relaxation: persistence simplification (review v1, R2 W2).

Prune every branch whose persistence (elder rule: merge value minus extremum value) is below eps, keep the
remaining leaves with their widths and references, and recompute the certificate. Simplification removes
conflicts by deleting features; relaxation keeps every feature and pays in merge levels.
Reports per eps (fraction of the value range): conflict share (H > theta), mean leaves per frame,
share of leaf instances removed, and the median persistence of the removed leaves.
Output: prototypes/output/persistence.json.  Run: .venv/bin/python -W ignore prototypes/persistence.py
"""
from pathlib import Path
import sys, json
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import general_method as gm, theory as th, replicate as rp, task_reference as tr
from ramtm.reference_points import reference_points_from_frames

OUT = tr.OUT
EPS = [0., .01, .02, .05]; NPIX = 1024


def pruned(fr, ids, eps, s):
    """Nested-list hierarchy on leaf ranks after pruning branches of persistence < eps (elder rule)."""
    rank = {k: i for i, k in enumerate(ids)}; removed = []
    def visit(k):
        ch = fr.children[k]
        if not ch: return rank[k], s * float(fr.values[k])
        res = [visit(c) for c in ch]; fv = s * float(fr.values[k])
        e = int(np.argmin([m for _, m in res])); keep = []
        for i, r in enumerate(res):
            if i == e or fv - r[1] >= eps: keep.append(r)
            else: removed.append(fv - r[1])
        if len(keep) == 1: return keep[0]
        return [x for x, _ in keep], min(m for _, m in res)
    return visit(fr.root)[0], removed


def leaves(t): return [t] if isinstance(t, int) else [l for c in t for l in leaves(c)]
def relabel(t, mp): return mp[t] if isinstance(t, int) else [relabel(c, mp) for c in t]


def main():
    res = {}
    for name in ['era5', 'era5_2014', 'wildfire']:
        ds = rp.LOADERS[name](); sc = ds['sc']; s = -1. if sc['trees'][0].kind == 'split' else 1.
        ext = reference_points_from_frames(sc['frames'], sc['ids'], kind='extremum')
        ref = gm.auto_reference(sc, ext, ds['lo'], ds['hi'])
        p = gm.universal_parameters(ref['origin'], ref['extent'], ds['domain_area']); theta = gm.THETA_FRACTION * p.canvas
        rng = float(np.ptp(sc['fields'])); res[name] = []
        for eps in EPS:
            conf = 0; nl = []; total = 0; rem = []
            for t, (fr, ids) in enumerate(zip(sc['frames'], sc['ids'])):
                w = p.width_scale * np.asarray(sc['areas'][t]); q = np.asarray(ref['qs'][t])
                tree, r_ = pruned(fr, ids, eps * rng, s); rem += r_
                L = leaves(tree); total += len(ids); nl.append(len(L))
                if isinstance(tree, int): continue
                tree = relabel(tree, {l: i for i, l in enumerate(L)}); ww, qq = w[L], q[L]
                ts = th.dp_tau(ww, qq, tree, p, NPIX)
                if ts <= theta: continue
                tf = th.dp_tau(ww, qq, list(range(len(L))), p, NPIX)
                conf += int(ts - tf > theta)
            r = dict(eps=eps, conflict_share=conf / len(sc['ids']), mean_leaves=float(np.mean(nl)),
                     removed_share=1 - sum(nl) / total, removed_median_persistence_share=float(np.median(rem)) / rng if rem else 0.)
            res[name].append(r)
            print(f"{name:10s} eps {eps:.0%}: conflicts {r['conflict_share']:.0%}, leaves/frame {r['mean_leaves']:.1f}, "
                  f"features removed {r['removed_share']:.0%}", flush=True)
    (OUT / 'persistence.json').write_text(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
