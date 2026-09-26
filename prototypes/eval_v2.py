"""Evaluation v2 (answers the v1 panel review): RQ2 as a budget trade-off, projection floor, per-feature flags,
and method-agnostic hidden costs.

Methods per dataset
  TMTM, ST-MTM                  existing merge tree maps (their own width models)
  fixed-X anchored              reference-anchored layout along a fixed longitude (hierarchy kept)
  A                             reference-anchored layout along the automatic direction (hierarchy kept)
  R kappa=2% / 20% / inf        certificate-driven relaxation at three budgets (+ its topological cost delta*)
  oracle q / oracle x           anchors placed exactly at the reference (auto direction / x); no hierarchy -> the
                                floor that any 1-D map along that direction reaches in the reader proxy
Reader proxy (unchanged from misreading.py): pair of tracks over k steps; map reading by |u_i-u_j| change with
eps = 2% of the method's occupied anchor range; truth = change of 2-D extremum distance beyond 2% of the diagonal.
  reversal, miss, error = reversal + miss, committed reversal = rev / (rev + correct)
  paired differences R - ST-MTM, R - A: circular moving-block bootstrap over time (block = k + 2 steps)
Flags (disclosure): per-feature flag = |c(u) - q| > theta for i or j at t or t+k, where c is the best monotone
  calibration of the map's axis (width-free certificate); recall of reversals and lift.
Hidden costs (q-independent): raw order-flip rate of tracked pairs between consecutive steps, anchor jitter
  mean |du| / occupied range, per-frame Kruskal stress-1, Spearman, and nearest-neighbour preservation vs 2-D.
Output: prototypes/output/eval_v2.json.  Run: .venv/bin/python -W ignore prototypes/eval_v2.py [datasets]
"""
from pathlib import Path
import sys, json
from itertools import combinations
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import replicate as rp, misreading as mr, relax_hierarchy as rh, general_method as gm, task_reference as tr, attainable as at

OUT = tr.OUT
KS = [1, 2, 4, 8]; EPS = [.01, .02, .05]; CAPS = [.02, .2, np.inf]; THETA = gm.THETA_FRACTION


def calibrated(u, q):
    """Best monotone calibration of anchors u onto references q (attains tau_pt of the order)."""
    o = np.argsort(u, kind='stable'); Q = q[o]
    pm = np.maximum.accumulate(Q); sm = np.minimum.accumulate(Q[::-1])[::-1]
    c = np.empty_like(Q); c[o] = (pm + sm) / 2
    return c


def methods(ds):
    sc = ds['sc']; kind = sc['trees'][0].kind
    M, ext, conflict, ref = mr.method_positions(ds)
    p = gm.universal_parameters(ref['origin'], ref['extent'], ds['domain_area']); theta = THETA * p.canvas
    occ = lambda U: max(max(u.max() for u in U) - min(u.min() for u in U), 1e-9)
    out = {k: dict(u=[np.asarray(x, float) for x in M[k]['u']], extent=M[k]['extent']) for k in ['TMTM', 'ST-MTM', 'fixed-X anchored']}
    out['A'] = dict(u=[np.asarray(x, float) for x in M['ours: auto direction']['u']], extent=M['ours: auto direction']['extent'])
    rng = float(np.ptp(sc['fields'])); dstar = {}
    for cap in CAPS:
        structs = []
        for t, (fr, ids) in enumerate(zip(sc['frames'], sc['ids'])):
            w = p.width_scale * np.asarray(sc['areas'][t]); q = ref['qs'][t]
            tf, _ = gm.tau_free(w, q, p); s0 = rh.node_tree(fr, ids); th_, _ = rh.best_tau(s0, w, q, p)
            structs.append(rh.relax_frame_threshold(fr, ids, w, q, p, theta, tf, cap * rng)[0] if th_ - tf > theta else s0)
        rows = rh.solve_sequence_structs(sc, ref['qs'], structs, p)
        U = [np.asarray(r['x'], float) for r in rows]; name = f'R {"inf" if cap == np.inf else f"{int(cap*100)}%"}'
        out[name] = dict(u=U, extent=occ(U))
        d = []
        for t, (fr, ids) in enumerate(zip(sc['frames'], sc['ids'])):
            V = at.lca_matrix(fr, ids, kind); n = len(ids)
            d.append(float(at.Filling(n).delta(np.array([rows[t]['order']], int), V)[0]) if n > 1 else 0.)
        dstar[name] = dict(max=max(d), mean=float(np.mean(d)), max_share=max(d) / rng, mean_share=float(np.mean(d)) / rng,
                           relaxed_frames=int(sum(x > 1e-12 for x in d)), unit_range=rng)
    Uq = [np.asarray(q, float) for q in ref['qs']]; out['oracle q'] = dict(u=Uq, extent=occ(Uq))
    Ux = [np.asarray(e, float)[:, 0] for e in ext]; out['oracle x'] = dict(u=Ux, extent=occ(Ux))
    return out, ext, ref, p, theta, dstar


def windows(sc, ext, U, extent, k, eps_frac, diag, qs, theta):
    tracks = sc['tracks']; eps_map = eps_frac * extent; eps2d = eps_frac * diag; rec = []
    C = [calibrated(u, np.asarray(q, float)) for u, q in zip(U, qs)]
    for t in range(len(tracks) - k):
        ia = {x: i for i, x in enumerate(tracks[t])}; ib = {x: i for i, x in enumerate(tracks[t + k])}
        common = [x for x in tracks[t] if x in ib]
        for a_, b_ in combinations(common, 2):
            i0, j0, i1, j1 = ia[a_], ia[b_], ib[a_], ib[b_]
            dm = abs(U[t + k][i1] - U[t + k][j1]) - abs(U[t][i0] - U[t][j0])
            d2 = np.linalg.norm(ext[t + k][i1] - ext[t + k][j1]) - np.linalg.norm(ext[t][i0] - ext[t][j0])
            dev = max(abs(C[t][i0] - qs[t][i0]), abs(C[t][j0] - qs[t][j0]), abs(C[t + k][i1] - qs[t + k][i1]), abs(C[t + k][j1] - qs[t + k][j1]))
            rec.append((int(mr.judge(dm, eps_map)), int(mr.judge(d2, eps2d)), t, dev > theta))
    if not rec: return None
    R = np.array(rec, dtype=object)
    rj = R[:, 0].astype(int); truth = R[:, 1].astype(int); tt = R[:, 2].astype(int); flag = R[:, 3].astype(bool)
    clear = truth != 0
    return dict(rj=rj, truth=truth, t=tt, flag=flag, clear=clear, rev=clear & (rj == -truth), miss=clear & (rj == 0),
                correct=clear & (rj == truth))


def summary(W, rng):
    c = W['clear']; n = int(c.sum())
    if n == 0: return dict(clear=0)
    rev, miss, cor = W['rev'], W['miss'], W['correct']
    null = np.mean([np.sum(c & (rng.permutation(W['rj']) == -W['truth'])) / n for _ in range(200)])
    fl = W['flag']
    out = dict(clear=n, reversal=float(rev.sum() / n), miss=float(miss.sum() / n), error=float((rev | miss).sum() / n),
               committed_reversal=float(rev.sum() / max(1, (rev | cor).sum())), null_reversal=float(null),
               feature_flag_share=float((c & fl).sum() / n), feature_flag_recall=float((rev & fl).sum() / max(1, rev.sum())))
    rf = (rev & fl).sum() / max(1, (c & fl).sum()); ru = (rev & ~fl).sum() / max(1, (c & ~fl).sum())
    out['feature_flag_lift'] = float(rf / ru) if ru > 0 else None
    return out


def paired(Wa, Wb, T, k, rng, B=2000):
    """Circular moving-block bootstrap over time steps (block = k+2) of a - b on the same clear cases."""
    c = Wa['clear']; t = Wa['t']; L = k + 2; nb = int(np.ceil(T / L)); res = {}
    for key in ['rev', 'miss']:
        a = Wa[key].astype(float); b = Wb[key].astype(float); diffs = []
        by_t = {s: np.where(c & (t == s))[0] for s in range(T)}
        for _ in range(B):
            starts = rng.integers(0, T, nb)
            idx = np.concatenate([by_t[(s + j) % T] for s in starts for j in range(L)])
            if len(idx): diffs.append(a[idx].mean() - b[idx].mean())
        d = float(a[c].mean() - b[c].mean()); lo, hi = np.percentile(diffs, [2.5, 97.5])
        res[key] = dict(diff=d, ci95=[float(lo), float(hi)], significant=bool(lo > 0 or hi < 0))
    res['blocks'] = nb; res['block_steps'] = L
    return res


def hidden_costs(sc, ext, U, extent):
    tracks = sc['tracks']; flips = tot = 0; jit = []
    for t in range(1, len(U)):
        prev = {k: i for i, k in enumerate(tracks[t - 1])}
        common = [(prev[k], i) for i, k in enumerate(tracks[t]) if k in prev]
        for (p1, c1), (p2, c2) in combinations(common, 2):
            tot += 1; flips += int(np.sign(U[t - 1][p1] - U[t - 1][p2]) != np.sign(U[t][c1] - U[t][c2]))
        jit += [abs(U[t][c] - U[t - 1][p]) / extent for p, c in common]
    st, sp, nn = [], [], []
    for t, u in enumerate(U):
        P = np.asarray(ext[t], float); n = len(u)
        if n < 3: continue
        pr = list(combinations(range(n), 2))
        d1 = np.array([abs(u[i] - u[j]) for i, j in pr]); d2 = np.array([np.linalg.norm(P[i] - P[j]) for i, j in pr])
        s = (d1 @ d2) / max(d1 @ d1, 1e-12); st.append(float(np.sqrt(np.sum((s * d1 - d2) ** 2) / np.sum(d2 ** 2))))
        if n >= 4:
            v = at_spearman(d1, d2)
            if not np.isnan(v): sp.append(v)
        D1 = np.abs(u[:, None] - u[None]); D2 = np.linalg.norm(P[:, None] - P[None], axis=2)
        np.fill_diagonal(D1, np.inf); np.fill_diagonal(D2, np.inf); nn.append(float(np.mean(D1.argmin(1) == D2.argmin(1))))
    return dict(order_flip_rate=flips / max(1, tot), jitter=float(np.mean(jit)), stress=float(np.mean(st)),
                spearman=float(np.mean(sp)), nn_preservation=float(np.mean(nn)))


def at_spearman(a, b):
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1]) if np.std(ra) > 0 and np.std(rb) > 0 else np.nan


def analyse(name):
    ds = rp.LOADERS[name](); sc = ds['sc']; T = len(sc['tracks'])
    M, ext, ref, p, theta, dstar = methods(ds)
    diag = float(np.linalg.norm(ds['hi'] - ds['lo'])); qs = [np.asarray(q, float) for q in ref['qs']]
    rng = np.random.default_rng(0); out = dict(dataset=name, dstar=dstar, proxy=[], paired=[], hidden={})
    for m, D in M.items():
        out['hidden'][m] = hidden_costs(sc, ext, D['u'], D['extent'])
        for k in KS:
            for e in EPS:
                if k != 2 and e != .02: continue
                W = windows(sc, ext, D['u'], D['extent'], k, e, diag, qs, theta)
                if W is None: continue
                out['proxy'].append(dict(method=m, k=k, eps=e, **summary(W, rng)))
                if m.startswith('R ') and W['clear'].sum():
                    for other in ['ST-MTM', 'A']:
                        Wo = windows(sc, ext, M[other]['u'], M[other]['extent'], k, e, diag, qs, theta)
                        out['paired'].append(dict(method=m, other=other, k=k, eps=e, **paired(W, Wo, T, k, rng)))
    return out


def main():
    names = sys.argv[1:] or ['era5', 'era5_2014', 'wildfire', 'ring']
    res = {}
    path = OUT / 'eval_v2.json'
    if path.exists(): res = json.loads(path.read_text())
    for n in names:
        print('running', n, flush=True); r = analyse(n); res[n] = r
        for m, d in r['dstar'].items():
            print(f"  {m}: relaxed frames {d['relaxed_frames']}, delta* max {d['max']:.2f} ({d['max_share']:.1%}), mean {d['mean']:.2f}")
        for x in r['proxy']:
            if x['k'] == 2 and x['eps'] == .02 and x.get('clear'):
                print(f"  {x['method']:16s} n {x['clear']:4d} rev {x['reversal']:.3f} miss {x['miss']:.3f} err {x['error']:.3f} "
                      f"commit-rev {x['committed_reversal']:.3f} null {x['null_reversal']:.3f} | flag share {x['feature_flag_share']:.2f} "
                      f"recall {x['feature_flag_recall']:.2f} lift {x['feature_flag_lift']}")
        for x in r['paired']:
            if x['k'] == 2 and x['eps'] == .02:
                print(f"  {x['method']:9s} - {x['other']:6s}: rev {x['rev']['diff']:+.3f} {x['rev']['ci95']} sig {x['rev']['significant']} | "
                      f"miss {x['miss']['diff']:+.3f} {x['miss']['ci95']} ({x['blocks']} blocks)")
        for m, h in r['hidden'].items():
            print(f"  hidden {m:16s} flips {h['order_flip_rate']:.3f} jitter {h['jitter']:.3f} stress {h['stress']:.3f} spearman {h['spearman']:.3f} NN {h['nn_preservation']:.3f}", flush=True)
        path.write_text(json.dumps(res, indent=1, default=float))


if __name__ == '__main__':
    main()
