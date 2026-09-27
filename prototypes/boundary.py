"""Are conflicts driven by boundary extrema? (figure work, 2026-09-27)

Cropping a field to a rectangle creates minima/maxima on the domain boundary that may be only the flank of a
feature outside. For every real dataset we (i) count leaves on the boundary (within one grid cell), (ii) count
conflict frames whose best witness triple uses a boundary leaf, and (iii) recompute the conflict share after
removing boundary leaves from the hierarchy (their subtrees collapse; widths/references of the rest unchanged).
Output: prototypes/output/boundary.json.  Run: .venv/bin/python -W ignore prototypes/boundary.py
"""
from pathlib import Path
import sys, json
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import general_method as gm, theory as th, replicate as rp, task_reference as tr, relax_hierarchy as rh, fig_witness as fw
from ramtm.reference_points import reference_points_from_frames

OUT = tr.OUT; NPIX = 1024


def prune(struct, keep):
    """Remove leaf ranks not in `keep`; collapse unary nodes. struct: rh.node_tree format."""
    if isinstance(struct, int): return struct if struct in keep else None
    kids = [c for c in (prune(c, keep) for c in struct[1]) if c is not None]
    if not kids: return None
    if len(kids) == 1: return kids[0]
    return [struct[0], kids]


def leaves(s): return [s] if isinstance(s, int) else [l for c in s[1] for l in leaves(c)]
def to_list(s, mp): return mp[s] if isinstance(s, int) else [to_list(c, mp) for c in s[1]]


def main():
    res = {}
    for name in ['era5', 'era5_2014', 'wildfire']:
        ds = rp.LOADERS[name](); sc = ds['sc']
        ext = reference_points_from_frames(sc['frames'], sc['ids'], kind='extremum')
        ref = gm.auto_reference(sc, ext, ds['lo'], ds['hi'])
        p = gm.universal_parameters(ref['origin'], ref['extent'], ds['domain_area']); theta = gm.THETA_FRACTION * p.canvas
        C = np.asarray(sc['coords']); cell = float(np.min(np.diff(np.unique(C[:, 0])))); lo, hi = C.min(0), C.max(0)
        nb = nl = conf = conf_bw = conf_int = 0; kept_leaves = 0
        for t, (fr, ids) in enumerate(zip(sc['frames'], sc['ids'])):
            P = np.array([fr.coordinates[i] for i in ids]); onb = np.any((P <= lo + cell * .51) | (P >= hi - cell * .51), axis=1)
            nb += int(onb.sum()); nl += len(ids)
            w = p.width_scale * np.asarray(sc['areas'][t]); q = np.asarray(ref['qs'][t]); s0 = rh.node_tree(fr, ids)
            ts = th.dp_tau(w, q, th.to_tree(s0), p, NPIX); tf = th.dp_tau(w, q, list(range(len(ids))), p, NPIX) if len(ids) > 1 else 0.
            if ts - tf > theta:
                conf += 1; b, trip = fw.witness(fr, ids, q)
                if trip is not None and any(onb[x] for x in trip): conf_bw += 1
            keep = {i for i in range(len(ids)) if not onb[i]}; kept_leaves += len(keep)
            s1 = prune(s0, keep)
            if s1 is None or isinstance(s1, int): continue
            L_ = leaves(s1); mp = {l: i for i, l in enumerate(L_)}
            ts1 = th.dp_tau(w[L_], q[L_], to_list(s1, mp), p, NPIX); tf1 = th.dp_tau(w[L_], q[L_], list(range(len(L_))), p, NPIX)
            conf_int += int(ts1 - tf1 > theta)
        T = len(sc['ids'])
        res[name] = dict(frames=T, leaves=nl, boundary_leaves=nb, boundary_share=nb / nl, conflict_frames=conf,
                         conflicts_with_boundary_witness=conf_bw, interior_only_conflict_frames=conf_int,
                         interior_only_conflict_share=conf_int / T, interior_leaves_per_frame=kept_leaves / T)
        print(name, res[name], flush=True)
    (OUT / 'boundary.json').write_text(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
