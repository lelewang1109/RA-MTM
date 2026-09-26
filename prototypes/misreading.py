"""Pilot: do merge tree maps make readers misjudge approach/separation, and does the certificate catch it?

Reader proxy. For every pair of tracks (i, j) present at frames t and t+k, a reader compares their
vertical distance on the map: D_map = |u_i - u_j| (displayed anchors). The reading is
  'approach' if D_map(t+k) - D_map(t) < -eps_map,  'separate' if > +eps_map,  else 'no change',
with eps_map = THETA_FRACTION * (axis extent of that map)   (2%, the single global constant).
Truth, two versions:
  T2D   : 2-D distance between leaf extrema (what readers naturally assume), eps = 2% of domain diagonal
  claim : the distance the map claims to encode: 2-D for TMTM / ST-MTM, |q_i - q_j| for reference maps
A REVERSAL is a clear truth change read as the clear opposite (false approach / false separation).
Flags:
  frame flag   : certificate conflict (H > theta) at t or t+k          -- method-agnostic
  feature flag : |u - q| > theta for i or j at t or t+k                -- reference maps only (disclosure)
We report reversal rates, flag recall, and LIFT = reversal rate among flagged / among unflagged
(ERA5 flags 58% of frames, so recall alone would be misleading).
Run: .venv/bin/python -W ignore prototypes/misreading.py
"""
from pathlib import Path
import sys, json, csv
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import general_method as gm, relax_hierarchy as rh, conflict_strategies as cs, task_reference as tr
from experiments import era5 as ep
from ramtm.error_budget import solve_sequence
from ramtm.reference_points import reference_points_from_frames

OUT = tr.OUT; THETA = gm.THETA_FRACTION
KS = [1, 2, 4, 8]


def method_positions(ds):
    """Displayed anchor positions per method, plus claimed coordinates and axis extents."""
    sc = ds['sc']; ext = reference_points_from_frames(sc['frames'], sc['ids'], kind='extremum')
    ref = gm.auto_reference(sc, ext, ds['lo'], ds['hi'])
    p = gm.universal_parameters(ref['origin'], ref['extent'], ds['domain_area']); theta = THETA * p.canvas
    span = ds['native_span']
    px = gm.Parameters(canvas=span, canvas_origin=float(min(ds['lo'][0], 0.)), width_scale=.5 * span / ds['domain_area'],
                       gap=span / 240, extra_budget=span / 120, rho=.5)
    M = {}
    for m in ['TMTM', 'ST-MTM']:
        kw = dict(canvas=span, length=ds['nominal'], refine_raster=False, strict_checks=False)
        if ds['name'] == 'ring': kw['stmtm_parameters'] = ep.b2.LayoutParameters.from_preset('ring')
        rows = ep.run_method(sc, m, px, **kw)['rows']
        U = [np.asarray(r['pixel_x'], float) for r in rows]
        lo = min(u.min() for u in U); hi = max(u.max() for u in U)
        M[m] = dict(u=U, claim=None, extent=max(hi - lo, 1e-9), dev=None)
    xr = solve_sequence(sc['centers'], sc['areas'], sc['hier'], px, reference_axis=0, feature_ids=sc['tracks'], reference_points=ext)
    M['fixed-X anchored'] = dict(u=[r['x'] for r in xr], claim=[e[:, 0] for e in ext], extent=px.canvas,
                                 dev=[abs(r['x'] - r['reference']) for r in xr], theta=THETA * px.canvas)
    rowsA = cs.solve_weighted_sequence(sc, ref['qs'], {}, p)
    M['ours: auto direction'] = dict(u=[r['x'] for r in rowsA], claim=ref['qs'], extent=p.canvas,
                                     dev=[abs(r['x'] - r['reference']) for r in rowsA], theta=theta)
    # certificate per frame (auto-direction reference) and relaxed layout
    structs, H = [], []
    for t, (fr, ids) in enumerate(zip(sc['frames'], sc['ids'])):
        w = p.width_scale * np.asarray(sc['areas'][t]); q = ref['qs'][t]
        tf, _ = gm.tau_free(w, q, p); s0 = rh.node_tree(fr, ids); th, _ = rh.best_tau(s0, w, q, p)
        H.append(th - tf)
        structs.append(rh.relax_frame(fr, ids, w, q, p, theta, tf)[0] if th - tf > theta else s0)
    rowsR = rh.solve_sequence_structs(sc, ref['qs'], structs, p)
    M['ours: relaxed'] = dict(u=[r['x'] for r in rowsR], claim=ref['qs'], extent=p.canvas,
                              dev=[abs(r['x'] - r['reference']) for r in rowsR], theta=theta)
    return M, ext, np.array(H) > theta, ref


def judge(delta, eps):
    return np.where(delta < -eps, -1, np.where(delta > eps, 1, 0))


def analyse(ds, eps_frac=THETA, cache=None):
    """eps_frac: reader threshold only (method constants stay at THETA)."""
    sc = ds['sc']; M, ext, conflict, ref = cache if cache is not None else method_positions(ds)
    diag = float(np.linalg.norm(ds['hi'] - ds['lo'])); eps2d = eps_frac * diag
    tracks = sc['tracks']; rows_out = []; events = []
    for m, D in M.items():
        eps_map = eps_frac * D['extent']
        for k in KS:
            rec = []
            for t in range(len(tracks) - k):
                common = [x for x in tracks[t] if x in tracks[t + k]]
                ia = {x: tracks[t].index(x) for x in common}; ib = {x: tracks[t + k].index(x) for x in common}
                for a_ in range(len(common)):
                    for b_ in range(a_ + 1, len(common)):
                        i, j = common[a_], common[b_]
                        dm = abs(D['u'][t + k][ib[i]] - D['u'][t + k][ib[j]]) - abs(D['u'][t][ia[i]] - D['u'][t][ia[j]])
                        d2 = np.linalg.norm(ext[t + k][ib[i]] - ext[t + k][ib[j]]) - np.linalg.norm(ext[t][ia[i]] - ext[t][ia[j]])
                        if D['claim'] is None: dc, epsc = d2, eps2d
                        else:
                            dc = abs(D['claim'][t + k][ib[i]] - D['claim'][t + k][ib[j]]) - abs(D['claim'][t][ia[i]] - D['claim'][t][ia[j]])
                            epsc = eps_map
                        fflag = bool(conflict[t] or conflict[t + k])
                        feat = None
                        if D['dev'] is not None:
                            th = D['theta']
                            feat = bool(max(D['dev'][t][ia[i]], D['dev'][t][ia[j]], D['dev'][t + k][ib[i]], D['dev'][t + k][ib[j]]) > th)
                        rec.append((judge(dm, eps_map), judge(d2, eps2d), judge(dc, epsc), fflag, feat, t, i, j, dm, d2))
            if not rec: continue
            rj, r2, rc, ff, fe = (np.array([r[x] for r in rec]) for x in range(5))
            tt = np.array([r[5] for r in rec]); rng = np.random.default_rng(0)
            def stats(truth):
                clear = truth != 0
                rev = clear & (rj == -truth)
                null = np.mean([np.sum(clear & (rng.permutation(rj) == -truth)) / max(1, clear.sum()) for _ in range(200)])
                frames_ = np.unique(tt[clear]); boots = []
                for _ in range(500):
                    pick = rng.choice(frames_, len(frames_)); m_ = np.concatenate([np.where(clear & (tt == f))[0] for f in pick]) if len(pick) else np.array([], int)
                    boots.append(rev[m_].mean() if len(m_) else np.nan)
                missed = clear & (rj == 0)
                out = dict(clear=int(clear.sum()), reversal_rate=float(rev.sum() / max(1, clear.sum())),
                           null_reversal_rate=float(null), ci95=[float(np.nanpercentile(boots, 2.5)), float(np.nanpercentile(boots, 97.5))] if boots else None,
                           missed_rate=float(missed.sum() / max(1, clear.sum())),
                           frame_flag_recall=float((rev & ff).sum() / max(1, rev.sum())),
                           frame_flag_share=float((clear & ff).sum() / max(1, clear.sum())),
                           rev_rate_flagged=float((rev & ff).sum() / max(1, (clear & ff).sum())),
                           rev_rate_unflagged=float((rev & ~ff).sum() / max(1, (clear & ~ff).sum())))
                out['frame_flag_lift'] = out['rev_rate_flagged'] / out['rev_rate_unflagged'] if out['rev_rate_unflagged'] > 0 else None
                if fe.dtype != object and fe[0] is not None:
                    fe_ = fe.astype(bool)
                    out.update(feature_flag_recall=float((rev & fe_).sum() / max(1, rev.sum())),
                               feature_flag_share=float((clear & fe_).sum() / max(1, clear.sum())),
                               unwarned_reversal_rate=float((rev & ~fe_).sum() / max(1, clear.sum())))
                return out, rev
            s2, rev2 = stats(r2); sc_, revc = stats(rc)
            rows_out.append(dict(dataset=ds['name'], method=m, k=k, eps_frac=eps_frac, pairs=len(rec), **{'T2D_' + a: b for a, b in s2.items()},
                                 **{'claim_' + a: b for a, b in sc_.items()}))
            if k == 2:
                for idx in np.where(rev2)[0]:
                    r = rec[idx]
                    events.append(dict(dataset=ds['name'], method=m, t=int(r[5]), track_i=int(r[6]), track_j=int(r[7]),
                                       map_change=float(r[8]) / D['extent'], true_change=float(r[9]) / diag, frame_flag=bool(r[3]),
                                       date=sc['dates'][int(r[5])] if 'dates' in sc else str(r[5])))
    return rows_out, events


def main():
    allrows, allev = [], []
    for make in (gm.era5, gm.ring, gm.gaussians):
        ds = make(); print('running', ds['name'], flush=True)
        r, e = analyse(ds); allrows += r; allev += e
    (OUT / 'misreading.json').write_text(json.dumps(allrows, indent=1, default=float))
    with open(OUT / 'misreading_events.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(allev[0].keys())); w.writeheader(); w.writerows(allev)
    for r in allrows:
        if r['k'] != 2: continue
        print(f"{r['dataset']:9s} {r['method']:22s} pairs {r['pairs']:5d} | T2D clear {r['T2D_clear']:5d} rev {r['T2D_reversal_rate']:.3f} "
              f"miss {r['T2D_missed_rate']:.3f} | flagshare {r['T2D_frame_flag_share']:.2f} recall {r['T2D_frame_flag_recall']:.2f} "
              f"lift {r['T2D_frame_flag_lift'] if r['T2D_frame_flag_lift'] is None else round(r['T2D_frame_flag_lift'],2)} "
              f"| claim rev {r['claim_reversal_rate']:.3f} miss {r['claim_missed_rate']:.3f}"
              + (f" featrecall {r.get('claim_feature_flag_recall', float('nan')):.2f} featshare {r.get('claim_feature_flag_share', float('nan')):.2f} unwarned {r.get('claim_unwarned_reversal_rate', float('nan')):.3f}"
                 if 'claim_feature_flag_recall' in r else ''), flush=True)


if __name__ == '__main__':
    main()
