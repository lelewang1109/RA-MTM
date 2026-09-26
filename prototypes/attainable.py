"""Exact attainable position-topology frontier, optimal filling, and exact space cost.

Three results that close gaps left by frontier.py:

(a) Optimal filling for a fixed leaf order (closed form).  For a join tree on a line, any filling g reduces
    to its barrier heights b_k = max g on [a_k, a_{k+1}], and the 1-D merge level of leaves i<j (in map
    order) is max(b_i..b_{j-1}).  Minimising d_top = max_{i<j} |max(b_i..b_{j-1}) - f(lca(i,j))| over b:
    raising a barrier only helps the lower constraints, so take b_k = C_k + delta with
    C_k = min_{i<=k<j} f(lca(i,j)); feasible iff max_{i<=k<j} C_k >= f(lca(i,j)) - 2 delta. Hence
        delta*(pi) = max(0, max_{i<j} (f(lca(i,j)) - max_{i<=k<j} C_k) / 2).
    Barriers must also lie above the adjacent leaf values, b_k >= l_k = max(f(k), f(k+1)), which adds the
    term max_k (l_k - C_k):
        delta*(pi) = max(0, max_k (l_k - C_k), max_{i<j} (f(lca(i,j)) - max_{i<=k<j} C_k) / 2).
    Split trees: negate values. delta*(pi) = 0 iff pi is hierarchy-consistent; delta* >= gamma_v/2 (Thm 2).
(b) Because positions depend only on the order (tau(pi), closed form) and merge levels only on the order
    and the filling (delta*(pi)), the EXACT attainable frontier over all 1-D maps is
        F(delta) = min { tau(pi) : delta*(pi) <= delta }        over all n! orders.
    We enumerate all orders for every frame (n <= 11) and compare with the certified bound Phi (Corollary 1).
(c) tau_free exactly = min over all n! orders (general_method.tau_free hill-climbs for n > 6).

Run: .venv/bin/python -W ignore prototypes/attainable.py [dataset ...]
"""
from pathlib import Path
import sys, json, time
from itertools import permutations, islice, combinations
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import theory as th, relax_hierarchy as rh, replicate as rp, task_reference as tr, general_method as gm

OUT = tr.OUT
CHUNK = 20000
CAPS = [0., .02, .2, np.inf]
DELTAS = [0., .005, .01, .02, .05, .1, .15, .2, .3, .5, .75, 1.]
NPIX = 1024


def lca_matrix(fr, ids, kind):
    """V[a, b] = f(lca) of leaves with ranks a, b; V[a, a] = f(leaf a) (join convention: split trees negated)."""
    s = -1. if kind == 'split' else 1.
    n = len(ids); V = np.diag([s * float(fr.values[i]) for i in ids])
    for a, b in combinations(range(n), 2):
        V[a, b] = V[b, a] = s * float(fr.values[fr.lca(ids[a], ids[b])])
    return V


class Filling:
    def __init__(self, n):
        self.n = n; self.iu = np.triu_indices(n, 1)
        k = np.arange(n - 1)
        self.M = (self.iu[0][:, None] <= k[None]) & (k[None] < self.iu[1][:, None])      # pair (i,j) straddles gap k

    def delta(self, O, V):
        """delta*(pi) for each row of O (orders as rank arrays)."""
        O = np.asarray(O)
        if self.n < 2: return np.zeros(len(O))
        P = V[O[:, self.iu[0]], O[:, self.iu[1]]]                                          # (m, pairs)
        C = np.where(self.M[None], P[:, :, None], np.inf).min(1)                            # (m, gaps)
        mx = np.where(self.M[None], C[:, None, :], -np.inf).max(2)                          # (m, pairs)
        leaf = np.diag(V)[O]; ell = np.maximum(leaf[:, :-1], leaf[:, 1:])                   # (m, gaps)
        return np.maximum.reduce([np.zeros(len(O)), ((P - mx) / 2).max(1), (ell - C).max(1)])


def pareto(delta, tau):
    """Non-dominated (delta, tau) points: F(d) = min tau over delta <= d."""
    o = np.lexsort((tau, delta)); pts, best = [], np.inf
    for d, t in zip(delta[o], tau[o]):
        if t < best - 1e-12: pts.append((float(d), float(t))); best = t
    return pts


def f_at(pts, d):
    v = np.inf
    for dd, t in pts:
        if dd <= d + 1e-12: v = t
    return v


def frame_exact(w, q, p, V):
    n = len(w); fl = Filling(n)
    if n == 1: return dict(pts=[(0., float(rh.tau_orders([[0]], w, q, p)[0]))], tau_free=None)
    pts, tf = [], np.inf
    it = permutations(range(n))
    while True:
        O = np.array(list(islice(it, CHUNK)))
        if not len(O): break
        t = rh.tau_orders(O, w, q, p); d = fl.delta(O, V)
        tf = min(tf, float(t.min()))
        pts = pareto(np.r_[[a for a, _ in pts], d], np.r_[[b for _, b in pts], t])
    return dict(pts=pts, tau_free=tf)


def analyse(name):
    t0 = time.perf_counter(); ds = rp.LOADERS[name](); sc = ds['sc']; kind = sc['trees'][0].kind
    rng = float(np.ptp(sc['fields']))
    runs = {cap: rh.run(ds, cap, make_figure=False, return_internal=True) for cap in CAPS}
    base = runs[0.]; ref, p = base['_internal']['ref'], base['_internal']['p']; L = p.canvas; theta = base['theta']
    frames, steps = [], []
    import pickle
    cpath = OUT / f'attainable_{name}_cache.pkl'
    cache = pickle.loads(cpath.read_bytes()) if cpath.exists() else None; new_cache = []
    for t, (fr, ids) in enumerate(zip(sc['frames'], sc['ids'])):
        w = p.width_scale * np.asarray(sc['areas'][t]); q = ref['qs'][t]
        V = lca_matrix(fr, ids, kind); s0 = rh.node_tree(fr, ids)
        ex = cache[t] if cache is not None else frame_exact(w, q, p, V); new_cache.append(ex)
        tau_h, _ = rh.best_tau(s0, w, q, p)
        tf = ex['tau_free'] if ex['tau_free'] is not None else tau_h
        steps.append(th.frontier_steps(fr, s0, w, q, p, NPIX))
        lg = base['frame_log'][t]
        # sanity: attainable frontier at delta=0 equals tau* of the full hierarchy
        frames.append(dict(t=t, n=len(ids), V=V, pts=ex['pts'], tau_hier=tau_h, tau_free_exact=tf,
                           tau_free_old=lg['tau_free'], F0_minus_tauhier=f_at(ex['pts'], 0.) - tau_h))
    if cache is None:
        cpath.write_bytes(pickle.dumps(new_cache))
        if '--cache-only' in sys.argv: return None
    H = np.array([f['tau_hier'] - f['tau_free_exact'] for f in frames])
    Hold = np.array([f['tau_hier'] - f['tau_free_old'] for f in frames])
    cert = dict(conflict_frames_exact=int(np.sum(H > theta)), conflict_share_exact=float(np.mean(H > theta)),
                conflict_frames_old=int(np.sum(Hold > theta)),
                tau_free_old_minus_exact_max_share=float(max(f['tau_free_old'] - f['tau_free_exact'] for f in frames) / L),
                space_cost_max_share=float(max(f['tau_free_exact'] for f in frames) / L),
                H_max_share=float(H.max() / L), check_F0_eq_tauhier_max=float(max(abs(f['F0_minus_tauhier']) for f in frames) / L))
    # frontiers on a common grid (fraction of value range)
    grid = sorted(set([d * rng for d in DELTAS] + [b for st in steps for b, _ in st] + [pt[0] for f in frames for pt in f['pts']]))
    fr_rows = [dict(delta=g / rng, Phi=float(np.mean([th.phi_at(st, g) for st in steps]) / L),
                    F=float(np.mean([f_at(f['pts'], g) for f in frames]) / L)) for g in grid]
    # per-frame tightness of the certified bound: gap F_t - Phi_t at the breakpoints of Phi_t
    gaps_, tight = [], 0; total = 0
    for f, st in zip(frames, steps):
        for b, phi in st:
            Ft = f_at(f['pts'], b); total += 1; gaps_.append((Ft - phi) / L)
            if Ft - phi <= .5 * L / NPIX + 1e-9: tight += 1
    tightness = dict(breakpoints=total, tight_within_half_pixel=tight, gap_mean=float(np.mean(gaps_)),
                     gap_p90=float(np.percentile(gaps_, 90)), gap_max=float(np.max(gaps_)), min_gap=float(np.min(gaps_)))
    # our relaxation: same orders, LCA filling (measured) vs optimal filling (delta*), and optimality over orders
    ours = []
    for cap, r in runs.items():
        R = r['_internal']['results']['R_relaxed']; rows = R['_rows']; me = R['_me']
        rec = dict(cap=cap, tau=[], d_lca=[], d_opt=[], F_at_dopt=[], thm2=[])
        for f, row, m in zip(frames, rows, me):
            o = np.array([row['order']], int); n = f['n']
            t_ = float(rh.tau_orders(o, *(lambda t: (p.width_scale * np.asarray(sc['areas'][t]), ref['qs'][t]))(f['t']), p)[0])
            d_ = float(Filling(n).delta(o, f['V'])[0]) if n > 1 else 0.
            bad = th.violated_nodes(rh.node_tree(sc['frames'][f['t']], sc['ids'][f['t']]), tuple(int(i) for i in row['order']))
            g2 = max([abs(float(sc['frames'][f['t']].values[par] - sc['frames'][f['t']].values[v])) / 2 for v, par in bad] + [0.])
            rec['tau'].append(t_); rec['d_lca'].append(float(m.max()) if len(m) else 0.); rec['d_opt'].append(d_)
            rec['F_at_dopt'].append(f_at(f['pts'], d_)); rec['thm2'].append(d_ - g2)
        T = np.array(rec['tau']); Dl = np.array(rec['d_lca']); Do = np.array(rec['d_opt']); Fa = np.array(rec['F_at_dopt'])
        ours.append(dict(cap=cap, E_share=float(T.mean() / L), D_lca_share=float(Dl.max() / rng), D_opt_share=float(Do.max() / rng),
                         mean_d_lca_share=float(Dl.mean() / rng), mean_d_opt_share=float(Do.mean() / rng),
                         opt_filling_saving_max_share=float((Dl - Do).max() / rng),
                         frames_pareto_optimal=int(np.sum(T <= Fa + .5 * L / NPIX)), frames=len(T),
                         excess_over_attainable_mean_share=float(np.mean(T - Fa) / L),
                         excess_over_attainable_max_share=float(np.max(T - Fa) / L),
                         F_at_Dopt=float(np.mean([f_at(f['pts'], Do.max()) for f in frames]) / L),
                         Phi_at_Dopt=float(np.mean([th.phi_at(st, Do.max()) for st in steps]) / L),
                         thm2_min_slack_share=float(min(rec['thm2']) / rng)))
    # optimality on RELAXED frames only, against naive policies (review v1, M1). For every policy the frame's
    # hierarchy T' is built by the policy; the order is the tau-optimal legal order of T' (ties: smaller delta*).
    comp = []; CAP = 2_000_000
    for policy in ['threshold', 'greedy', 'flatall']:
        for cap in [.02, .2, np.inf]:
            rel, on, gap, dd, skipped, resolved, nconf = 0, 0, [], [], 0, 0, 0
            for t, (fr, ids) in enumerate(zip(sc['frames'], sc['ids'])):
                f = frames[t]; w = p.width_scale * np.asarray(sc['areas'][t]); q = ref['qs'][t]
                if f['tau_hier'] - f['tau_free_exact'] <= theta: continue
                nconf += 1; vc = cap * rng
                if policy == 'greedy': s_, _, steps_, _ = rh.relax_frame(fr, ids, w, q, p, theta, f['tau_free_exact'], vc)
                else: s_, steps_, _ = rh.relax_frame_threshold(fr, ids, w, q, p, theta, f['tau_free_exact'], vc, prune=policy == 'threshold')
                if not steps_: continue
                rel += 1
                if rh.n_legal_orders(rh.to_tuple(s_)) > CAP: skipped += 1; continue
                O = np.array(rh.leaf_orders(rh.to_tuple(s_)), int); tau = rh.tau_orders(O, w, q, p)
                cand = np.where(tau <= tau.min() + 1e-9)[0]; dl = Filling(f['n']).delta(O[cand], f['V'])
                d = float(dl.min()); tbest = float(tau.min())
                Ft = f_at(f['pts'], d); on += int(tbest <= Ft + .5 * L / NPIX); gap.append((tbest - Ft) / L); dd.append(d / rng)
                resolved += int(tbest - f['tau_free_exact'] <= theta + .5 * L / NPIX)
            comp.append(dict(policy=policy, cap=cap, conflict_frames=nconf, resolved=resolved, relaxed_frames=rel, evaluated=rel - skipped, on_frontier=on,
                             gap_mean=float(np.mean(gap)) if gap else 0., gap_max=float(np.max(gap)) if gap else 0.,
                             delta_mean=float(np.mean(dd)) if dd else 0.))
    return dict(dataset=name, axis=L, value_range=rng, theta=theta, seconds=time.perf_counter() - t0,
                max_leaves=int(max(f['n'] for f in frames)), certificate=cert, tightness=tightness,
                frontier=fr_rows, ours=ours, relaxed_only=comp)


def main():
    names = [a for a in sys.argv[1:] if not a.startswith('--')] or list(rp.LOADERS)
    for n in names:
        print('running', n, flush=True); r = analyse(n)
        if r is None: print('  cached exact frontier', flush=True); continue
        (OUT / f'attainable_{n}.json').write_text(json.dumps(r, indent=1, default=float))
        c, tt = r['certificate'], r['tightness']
        print(f"  {r['seconds']:.0f}s, n<= {r['max_leaves']}: conflicts exact {c['conflict_frames_exact']} (old {c['conflict_frames_old']}), "
              f"tau_free old-exact max {c['tau_free_old_minus_exact_max_share']:.4f}, space max {c['space_cost_max_share']:.3f}, F(0)=tau* check {c['check_F0_eq_tauhier_max']:.1e}")
        print(f"  bound tightness: {tt['tight_within_half_pixel']}/{tt['breakpoints']} breakpoints tight; gap mean {tt['gap_mean']:.4f} p90 {tt['gap_p90']:.4f} max {tt['gap_max']:.4f} (min {tt['min_gap']:.4f})")
        for c in r['relaxed_only']:
            print(f"   [{c['policy']:9s} cap {c['cap']}] conflicts {c['conflict_frames']}, resolved {c['resolved']}, relaxed {c['relaxed_frames']:3d} (evaluated {c['evaluated']}), on frontier {c['on_frontier']:3d}, "
                  f"gap mean {c['gap_mean']:.4f} max {c['gap_max']:.4f}, delta* mean {c['delta_mean']:.3f}", flush=True)
        for o in r['ours']:
            print(f"   cap {o['cap']}: E {o['E_share']:.3f} D_lca {o['D_lca_share']:.3f} D_opt {o['D_opt_share']:.3f} "
                  f"pareto-opt frames {o['frames_pareto_optimal']}/{o['frames']} excess mean {o['excess_over_attainable_mean_share']:.4f} "
                  f"max {o['excess_over_attainable_max_share']:.4f}; F@D {o['F_at_Dopt']:.3f} Phi@D {o['Phi_at_Dopt']:.3f}; thm2 slack {o['thm2_min_slack_share']:.4f}", flush=True)


def plot():
    """Figure: certified bound Phi, exact attainable frontier F, and our layouts (LCA vs optimal filling)."""
    import figstyle as fs; fs.apply(); plt = tr.plt
    names = [n for n in rp.LOADERS if (OUT / f'attainable_{n}.json').exists()]
    TITLE = dict(era5='ERA5 1999/2000', era5_2014='ERA5 2013/14', wildfire='Wildfire 2019', ring='Ring', gaussians='Gaussians')
    fig, axs = plt.subplots(1, len(names), figsize=(fs.TEXT_W, 1.75), layout='constrained')
    for ax, n in zip(np.atleast_1d(axs), names):
        r = json.loads((OUT / f'attainable_{n}.json').read_text())
        d = [x['delta'] * 100 for x in r['frontier']]
        ax.step(d, [x['F'] * 100 for x in r['frontier']], where='post', color='#0072b2', lw=1.1, label='exact frontier F')
        ax.step(d, [x['Phi'] * 100 for x in r['frontier']], where='post', color='k', lw=.7, ls='--', label='certified bound Φ')
        for o in r['ours']:
            ax.plot(o['D_lca_share'] * 100, o['E_share'] * 100, 'o', mfc='none', color='#009e73', ms=4.5)
            ax.plot(o['D_opt_share'] * 100, o['E_share'] * 100, 'o', color='#009e73', ms=4.5)
            ax.plot([o['D_opt_share'] * 100, o['D_lca_share'] * 100], [o['E_share'] * 100] * 2, '-', color='#009e73', lw=.5)
        ax.set(title=TITLE.get(n, n), xlabel='$d_{top}$ (% of value range)', xlim=(-2, 72))
    np.atleast_1d(axs)[0].set_ylabel('τ(π), % of axis')
    np.atleast_1d(axs)[0].plot([], [], 'o', color='#009e73', label='R, optimal filling'); np.atleast_1d(axs)[0].plot([], [], 'o', mfc='none', color='#009e73', label='R, LCA filling')
    np.atleast_1d(axs)[0].legend(fontsize=5.5, handlelength=1.2, borderpad=.3, labelspacing=.25)
    fig.savefig(OUT / 'fig_frontier_exact.png', dpi=300); fig.savefig(OUT / 'fig_frontier_exact.pdf'); plt.close(fig)


if __name__ == '__main__':
    if sys.argv[1:] == ['plot']: plot()
    else: main(); plot()
