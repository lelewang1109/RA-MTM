"""Prototype: certificate-driven LOCAL relaxation of merge-tree contiguity.

Problem: on ERA5, 58% of frames have hierarchy cost (tau_hier - tau_free) > theta,
i.e. keeping every subtree contiguous forces large reference errors.

Rule (no per-dataset parameters; theta = 0.02 L is the single global constant):
  for each frame with hierarchy cost > theta:
     repeat: among non-root merge nodes whose flattening lowers tau*, flatten the
             WEAKEST one (smallest |f(node) - f(parent)|, i.e. least persistent merge);
     until hierarchy cost <= theta or no flattening helps.
  "Flatten v" = splice v's children into v's parent, so they may interleave with
  their former aunts/uncles. v's leaves then meet in the 1-D map only at the parent's
  level: the map shows that merge at f(parent) instead of f(v).

Cost is measured on the RENDERED map: for every leaf pair, the 1-D merge level
(min between anchors for split trees, max for join trees) vs. the true LCA value.
Unrelaxed frames must keep the exact merge tree (signature check).
Run: .venv/bin/python -W ignore prototypes/relax_hierarchy.py
"""
from pathlib import Path
import sys, json, time
from itertools import combinations
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import task_reference as tr
import conflict_strategies as cs
import general_method as gm
from experiments import era5 as ep
from ramtm.error_budget import leaf_orders
from ramtm.reference_anchored import render_sequence
from ramtm.reference_points import reference_points_from_frames

OUT = tr.OUT; plt = tr.plt


# ------------------------------------------------------------- tree helpers
def node_tree(fr, leaves):
    """Branching structure: leaf -> rank int; merge node -> [node_id, [children]]."""
    rank = {k: i for i, k in enumerate(leaves)}
    def visit(k):
        ch = fr.children[k]
        if not ch: return rank[k]
        if len(ch) == 1: return visit(ch[0])
        return [k, [visit(c) for c in ch]]
    return visit(fr.root)


def to_tuple(s):
    return s if isinstance(s, int) else tuple(to_tuple(c) for c in s[1])


def merge_nodes(s, parent=None, out=None):
    out = [] if out is None else out
    if not isinstance(s, int):
        if parent is not None: out.append((s[0], parent))
        for c in s[1]: merge_nodes(c, s[0], out)
    return out


def flatten(s, node):
    if isinstance(s, int): return s
    kids = []
    for c in s[1]:
        if not isinstance(c, int) and c[0] == node: kids.extend(flatten(g, node) for g in c[1])
        else: kids.append(flatten(c, node))
    return [s[0], kids]


# ------------------------------------------- closed-form tau for fixed orders
def tau_orders(orders, w, q, p):
    """Exact min-max reference deviation for each fixed order (rows of `orders`).

    With windows |z_i - q_i| <= tau + h_i (h = rho w/2), canvas [a, a+L], chain
    separations S_ij, feasibility of a chain with box windows is lo_i + S_ij <= hi_j
    for all i <= j, which gives
      tau* = max(0, max_{i<j} (q_i - q_j + S_ij - h_i - h_j)/2,
                    max_i  a + D_i - q_i - h_i,  max_i  q_i - h_i - (a + L - E_i)).
    Returns inf where total width + gaps exceed the canvas.
    """
    O = np.asarray(orders); m, n = O.shape
    W = w[O]; Q = q[O]; H = p.rho * W / 2
    D = np.cumsum(W, 1) - W / 2 + p.gap * np.arange(n)                  # min distance from a to z
    E = (W.sum(1, keepdims=True) - np.cumsum(W, 1)) + W / 2 + p.gap * (n - 1 - np.arange(n))
    a, L = p.canvas_origin, p.canvas
    t1 = np.max(a + D - Q - H, 1); t2 = np.max(Q - H - (a + L - E), 1)
    S = D[:, None, :] - D[:, :, None]                                     # S[i,j] = D_j - D_i
    pair = (Q[:, :, None] - Q[:, None, :] + S - H[:, :, None] - H[:, None, :]) / 2
    iu = np.triu_indices(n, 1)
    t0 = pair[:, iu[0], iu[1]].max(1) if n > 1 else np.full(m, -np.inf)
    tau = np.maximum.reduce([np.zeros(m), t0, t1, t2])
    over = W.sum(1) + (n - 1) * p.gap > L + 1e-9
    tau[over] = np.inf
    return tau


def best_tau(struct, w, q, p, cap=200000):
    orders = leaf_orders(to_tuple(struct))
    if len(orders) > cap: return None, len(orders)
    return float(tau_orders(orders, w, q, p).min()), len(orders)


def relax_frame(fr, leaves, w, q, p, theta, tfree, value_cap=np.inf):
    s = node_tree(fr, leaves)
    cur, n_orders = best_tau(s, w, q, p)
    steps = []
    while cur - tfree > theta:
        cands = []
        for node, parent in merge_nodes(s):
            s2 = flatten(s, node); t2, n2 = best_tau(s2, w, q, p)
            cost = abs(float(fr.values[node] - fr.values[parent]))
            if t2 is not None and t2 < cur - 1e-9 and cost <= value_cap:
                cands.append((abs(float(fr.values[node] - fr.values[parent])), t2, node, s2, n2))
        if not cands: break
        cost, t2, node, s, n_orders = min(cands, key=lambda c: (c[0], c[1]))
        steps.append(dict(node=int(node), merge_level_change=cost, tau_after=t2)); cur = t2
    return s, cur, steps, n_orders


def relax_frame_threshold(fr, leaves, w, q, p, theta, tfree, value_cap=np.inf, N=4096):
    """Frontier-aligned policy: flatten every merge with gap <= value_cap, then prune (strongest first)
    any flattening whose removal does not raise tau* (within half a pixel). Handles plateaus where only
    a SET of flattenings helps (greedy single steps cannot)."""
    import theory as th
    s0 = node_tree(fr, leaves); g = th.gaps(fr, s0)
    tau = lambda S: th.dp_tau(w, q, th.to_tree(th.flatten_set(s0, S)), p, N)
    W = [v for v, gv in g.items() if gv <= value_cap + 1e-12]
    if not W: return s0, [], tau([])
    tW = tau(W); tol = .5 * p.canvas / N
    for v in sorted(W, key=lambda v: -g[v]):
        W2 = [x for x in W if x != v]
        if tau(W2) <= tW + tol: W = W2
    steps = [dict(node=int(v), merge_level_change=g[v]) for v in W]
    return th.flatten_set(s0, W), steps, tW


# -------------------------------------------------------- sequence solving
def solve_sequence_structs(sc, qs, structs, p):
    rows = []
    for t, (c, a, st, ids, q) in enumerate(zip(sc['centers'], sc['areas'], structs, sc['tracks'], qs)):
        prev = prevq = mask = None
        if t:
            lk = {k: i for i, k in enumerate(sc['tracks'][t - 1])}
            mask = np.array([k in lk for k in ids]); prev = np.zeros(len(ids)); prevq = np.zeros(len(ids))
            for i, k in enumerate(ids):
                if mask[i]: j = lk[k]; prev[i] = rows[-1]['x'][j]; prevq[i] = rows[-1]['reference'][j]
        w = p.width_scale * np.asarray(a); orders = leaf_orders(to_tuple(st))
        tau = tau_orders(orders, w, q, p)
        keep = [o for o, v in zip(orders, tau) if v <= tau.min() + p.extra_budget + 1e-9]
        r = cs.solve_frame_weighted(c, a, to_tuple(st), q, np.ones(len(q)), p, prev, prevq, mask, orders=keep)
        r['feature_ids'] = list(ids); r['s'] = np.ones(len(q)); rows.append(r)
    return rows


def validate_relaxed(sc, rows, structs, p):
    """Same invariants as validate_weighted, but legality w.r.t. the relaxed hierarchy."""
    for t, (r, a, st) in enumerate(zip(rows, sc['areas'], structs)):
        o = np.array(r['order'])
        assert tuple(o) in set(leaf_orders(to_tuple(st))), t
        assert np.allclose(r['w'], p.width_scale * np.asarray(a), atol=1e-12), t
        assert np.min(r['z'] - r['w'] / 2) >= p.canvas_origin - 1e-6 and np.max(r['z'] + r['w'] / 2) <= p.canvas_origin + p.canvas + 1e-6, t
        assert np.all(abs(r['x'] - r['z']) <= p.rho * r['w'] / 2 + 1e-6), t
        assert np.all(np.diff(r['z'][o]) - (r['w'][o[:-1]] + r['w'][o[1:]]) / 2 >= p.gap - 1e-6), t
        assert np.all(abs(r['x'] - r['reference']) <= r['budget'] + 1e-6), t


def render(sc, rows, p, length):
    while True:
        try:
            maps, ds, _ = render_sequence(sc['frames'], sc['ids'], rows, p.canvas, length, canvas_origin=p.canvas_origin)
            return maps, ds, length
        except ValueError as e:
            if 'increase resolution' not in str(e) or length >= 131072: raise
            length *= 2


def merge_errors(sc, maps, ds, kind):
    """Per frame: |1-D merge level - true LCA value| over all leaf pairs (scalar units)."""
    per = []
    for t, (fr, sk) in enumerate(zip(sc['frames'], ds)):
        col = maps[:, t]; order = list(sk.ordering); anc = np.asarray(sk.anchors)
        errs = []
        for i, j in combinations(range(len(order)), 2):
            lo, hi = sorted((anc[i], anc[j])); seg = col[lo:hi + 1]
            level = seg.min() if kind == 'split' else seg.max()
            errs.append(abs(float(level) - float(fr.values[fr.lca(order[i], order[j])])))
        per.append(np.array(errs))
    return per


# ---------------------------------------------------------------- run
def run(ds, value_cap_fraction=np.inf, make_figure=True, return_internal=False, policy='threshold'):
    sc = ds['sc']; kind = sc['trees'][0].kind; t0 = time.perf_counter()
    ext = reference_points_from_frames(sc['frames'], sc['ids'], kind='extremum')
    ref = gm.auto_reference(sc, ext, ds['lo'], ds['hi'])
    p = gm.universal_parameters(ref['origin'], ref['extent'], ds['domain_area']); theta = gm.THETA_FRACTION * p.canvas
    # sanity: closed form == LP on the full-hierarchy orders of a few frames
    chk = 0.
    for t in range(0, len(sc['ids']), max(1, len(sc['ids']) // 8)):
        w = p.width_scale * np.asarray(sc['areas'][t]); q = ref['qs'][t]
        for o in leaf_orders(sc['hier'][t])[:64]:
            lp = tr.lp_tau(w, q, o, p); cf = tau_orders([o], w, q, p)[0]
            if lp is not None: chk = max(chk, abs(lp - cf))
    value_cap = value_cap_fraction * float(np.ptp(sc['fields']))
    structs, frame_log = [], []
    for t, (fr, ids) in enumerate(zip(sc['frames'], sc['ids'])):
        w = p.width_scale * np.asarray(sc['areas'][t]); q = ref['qs'][t]
        tfree, exact = gm.tau_free(w, q, p)
        s0 = node_tree(fr, ids); th, _ = best_tau(s0, w, q, p)
        if th - tfree > theta and policy == 'threshold':
            s, steps, tr_ = relax_frame_threshold(fr, ids, w, q, p, theta, tfree, value_cap); n_orders = len(leaf_orders(to_tuple(s)))
        elif th - tfree > theta:
            s, tr_, steps, n_orders = relax_frame(fr, ids, w, q, p, theta, tfree, value_cap)
        else:
            s, tr_, steps, n_orders = s0, th, [], None
        structs.append(s)
        frame_log.append(dict(t=t, leaves=len(ids), tau_hier=th, tau_free=tfree, tau_relaxed=tr_,
                              relaxed_nodes=len(steps), steps=steps, orders_after=n_orders))
    rowsA = cs.solve_weighted_sequence(sc, ref['qs'], {}, p)
    rowsR = solve_sequence_structs(sc, ref['qs'], structs, p)
    cs.validate_weighted(sc, rowsA, p)
    validate_relaxed(sc, rowsR, structs, p)
    out = dict(dataset=ds['name'], closed_form_vs_lp_max_diff=chk, reference=ref['label'], theta=theta,
               canvas=p.canvas, frames=len(structs))
    results = {}
    for name, rows in [('A_full_hierarchy', rowsA), ('R_relaxed', rowsR)]:
        maps, dsk, length = render(sc, rows, p, ds['nominal'])
        me = merge_errors(sc, maps, dsk, kind)
        sig_ok = [ep.signature(maps[:, t], tree.kind) == ep.signature(tree) for t, tree in enumerate(sc['trees'])]
        e = np.concatenate([abs(r['x'] - r['reference']) for r in rows])
        relaxed = {d['t'] for d in frame_log if d['relaxed_nodes']} if name == 'R_relaxed' else set()
        allpairs = np.concatenate(me) if me else np.array([])
        results[name] = dict(
            ref_err_mean=float(e.mean()), ref_err_p95=float(np.quantile(e, .95)), ref_err_max=float(e.max()),
            frames_err_over_theta=int(sum(np.max(abs(r['x'] - r['reference'])) > theta for r in rows)),
            topology_exact_frames=int(sum(sig_ok)),
            topology_exact_unrelaxed_frames=int(sum(ok for t, ok in enumerate(sig_ok) if t not in relaxed)),
            unrelaxed_frames=len(sig_ok) - len(relaxed),
            pairs=int(len(allpairs)), pairs_merge_changed=int(np.sum(allpairs > 1e-4)),
            merge_err_max=float(allpairs.max()) if len(allpairs) else 0.,
            merge_err_mean_changed=float(allpairs[allpairs > 1e-4].mean()) if np.any(allpairs > 1e-4) else 0.,
            raster_length=length)
        results[name]['_maps'] = maps; results[name]['_rows'] = rows; results[name]['_me'] = me
    out['frames_relaxed'] = int(sum(d['relaxed_nodes'] > 0 for d in frame_log))
    out['nodes_relaxed_total'] = int(sum(d['relaxed_nodes'] for d in frame_log))
    out['frames_still_over_theta_after_relax'] = int(sum(d['tau_relaxed'] - d['tau_free'] > theta for d in frame_log))
    out['field_range'] = float(np.ptp(sc['fields']))
    out['results'] = {k: {kk: vv for kk, vv in v.items() if not kk.startswith('_')} for k, v in results.items()}
    out['seconds'] = time.perf_counter() - t0
    out['value_cap_fraction'] = value_cap_fraction; out['policy'] = policy
    out['max_legal_orders_after_relax'] = int(max([d['orders_after'] or 0 for d in frame_log] + [0]))
    if make_figure: figure(ds, sc, p, theta, frame_log, results, ref)
    out['frame_log'] = frame_log
    if return_internal:
        out['_internal'] = dict(results=results, structs=structs, ref=ref, p=p, theta=theta)
    return out


def figure(ds, sc, p, theta, log, res, ref):
    T = len(log); lo, hi = ds['vrange'] or np.quantile(sc['fields'], [0, 1])
    fig = plt.figure(figsize=(15, 7.4))
    g = fig.add_gridspec(2, 3, height_ratios=[1, 3.2], width_ratios=[1, 1, .8], hspace=.1, wspace=.25,
                         left=.05, right=.98, top=.9, bottom=.08)
    for j, (name, title) in enumerate([('A_full_hierarchy', 'A  full hierarchy (current)'),
                                       ('R_relaxed', 'R  certificate-driven local relaxation')]):
        ax = fig.add_subplot(g[1, j]); r = res[name]
        cs.draw(ax, sc, r['_rows'], r['_maps'], p, '', None, None, None, lo, hi); ax.images[0].set_cmap(ds['cmap'])
        ax.set_ylabel(ref['label'] if j == 0 else '')
        top = fig.add_subplot(g[0, j], sharex=ax)
        err = [np.max(abs(rw['x'] - rw['reference'])) for rw in r['_rows']]
        top.bar(range(T), err, color='#d55e00' if j == 0 else '#009e73', width=.9)
        top.axhline(theta, color='k', lw=.8, ls=':'); top.set_ylim(0, max(err) * 1.05 + 1)
        top.set(title=title, ylabel='max |u−q|'); top.tick_params(labelbottom=False)
        if j == 1:
            for d in log:
                if d['relaxed_nodes']: ax.plot(d['t'], p.canvas_origin + p.canvas * .985, 'v', color='#009e73', ms=3)
    ax = fig.add_subplot(g[1, 2])
    me = np.concatenate(res['R_relaxed']['_me']); me = me[me > 1e-4]
    if len(me): ax.hist(me, bins=30, color='#009e73')
    unit = 'hPa' if ds['name'] == 'era5' else 'scalar units'
    ax.set(title='R: merge-level change of affected leaf pairs', xlabel=f'|1-D merge level − true| ({unit})', ylabel='leaf pairs')
    fig.suptitle(f"{ds['name']}: local hierarchy relaxation (green ▼ = relaxed frame; dotted = θ); "
                 f"{ref['label']}", fontsize=10.5)
    fig.savefig(OUT / f"{ds['name']}_relax.png", dpi=150); plt.close(fig)


def main():
    report = {}
    for make in (gm.era5, gm.ring, gm.gaussians):
        ds = make(); print('running', ds['name'], flush=True)
        r = run(ds); report[ds['name']] = r
        print(json.dumps({k: v for k, v in r.items() if k != 'frame_log'}, indent=1, default=float), flush=True)
    (OUT / 'relax_metrics.json').write_text(json.dumps(report, indent=1, default=float))


if __name__ == '__main__':
    main()
