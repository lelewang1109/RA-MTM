"""Prototype: what should a task-referenced map do when reference and hierarchy conflict?

A  min-max compromise       : minimise max_i |u_i - q_i| (current RA-MTM behaviour).
B  stability-priority        : minimise max_i |u_i - q_i| / s_i with per-TRACK tolerance
                               s = 1 + kappa * min(1, mean reference speed / v0).
                               Stationary tracks (s=1) are protected, moving tracks
                               absorb the unavoidable deviation, so the layout does not
                               invent motion for stationary context. s is constant per
                               track, hence temporally consistent.
C  disclosure (render layer) : wherever |u - q| > theta, draw the true reference q as a
                               ghost tick joined to the anchor, and shade frames whose
                               hierarchy cost (tau_hier - tau_free) exceeds theta.
                               Applied on top of A or B.

A and B share one compact weighted LP/QP solver (below), so only the weights differ.
The collaborator's solver is untouched; compact-A is checked against solve_frame.
Run: .venv/bin/python prototypes/conflict_strategies.py
"""
from pathlib import Path
import sys, json
from itertools import combinations
import numpy as np
from scipy.optimize import minimize
sys.path.insert(0, str(Path(__file__).resolve().parent))
import task_reference as tr
from ramtm.error_budget import constraints, checked_lp, leaf_orders, InfeasibleLayout

OUT = tr.OUT
plt = tr.plt


# ------------------------------------------------------------ weighted solver
def solve_frame_weighted(c, measure, hierarchy, q, s, p, previous=None, previous_q=None, mask=None, weight_qp=False):
    """Same model as ramtm.error_budget.solve_frame, but |u_i-q_i| <= s_i * tau."""
    n = len(q); w = p.width_scale * np.asarray(measure, float); q = np.asarray(q, float); s = np.asarray(s, float)
    mask = np.ones(n, bool) if mask is None else np.asarray(mask, bool)
    cands = []
    for order in leaf_orders(hierarchy):
        A, b, bounds = constraints(w, order, p)
        L = np.c_[-A, np.zeros(len(A))]
        E = np.c_[np.eye(n), np.zeros((n, n)), -s]          # u - q <= s tau
        F = np.c_[-np.eye(n), np.zeros((n, n)), -s]         # q - u <= s tau
        lp = checked_lp(np.r_[np.zeros(2 * n), 1.], np.vstack([L, E, F]), np.r_[-b, q, -q], bounds + [(0, None)])
        if lp is not None: cands.append((order, A, b, bounds, lp))
    if not cands: raise InfeasibleLayout('no legal order fits')
    tau = min(x[-1].fun for x in cands); budget = tau + p.extra_budget
    pairs_all = None; best = None
    goal = None
    if previous is not None and mask.any():
        goal = previous[mask] + q[mask] - previous_q[mask]
    for order, A, b, bounds, lp in cands:
        if lp.fun > budget + 1e-8: continue
        R = np.c_[np.eye(n), np.zeros((n, n))]
        Ab = np.vstack([A, R, -R]); bb = np.r_[b, q - s * budget, -q - s * budget]
        start = checked_lp(np.zeros(2 * n), -Ab, -bb, bounds)
        if start is None: continue
        pairs = list(combinations(order, 2)); B = np.zeros((len(pairs), 2 * n))
        d = np.array([np.linalg.norm(c[i] - c[j]) for i, j in pairs])
        for k, (i, j) in enumerate(pairs): B[k, j] = 1; B[k, i] = -1
        D = np.c_[-np.eye(n), np.eye(n)]
        gw = p.geometry_weight / max(1, len(pairs)); rw = p.reference_weight / n
        ew = p.eccentricity_weight / n; tw = p.motion_weight / max(1, int(mask.sum()))
        # weight_qp=False: tolerances act only on the hard budget (LP + QP constraints);
        # weight_qp=True additionally divides the QP reference term by s^2.
        sq = s ** 2 if weight_qp else np.ones(n)
        def fun(v):
            val = gw * np.sum((B @ v - d) ** 2) + ew * np.sum((D @ v) ** 2) + rw * np.sum((v[:n] - q) ** 2 / sq)
            if goal is not None: val += tw * np.sum((v[:n][mask] - goal) ** 2)
            return val
        def jac(v):
            g = 2 * gw * B.T @ (B @ v - d) + 2 * ew * D.T @ (D @ v)
            g[:n] += 2 * rw * (v[:n] - q) / sq
            if goal is not None: g[:n][mask] += 2 * tw * (v[:n][mask] - goal)
            return g
        opt = minimize(lambda v: fun(v) / 1000, start.x, jac=lambda v: jac(v) / 1000, method='SLSQP', bounds=bounds,
                       constraints={'type': 'ineq', 'fun': lambda v: Ab @ v - bb, 'jac': lambda v: Ab},
                       options={'ftol': 1e-13, 'maxiter': 2000})
        x = opt.x if (opt.success and np.min(Ab @ opt.x - bb) > -1e-6) else start.x
        val = fun(x)
        if best is None or val < best['objective'] - 1e-9:
            best = dict(x=x[:n], z=x[n:], w=w, order=order, tau=float(tau), budget=float(budget), objective=val,
                        reference=q.copy(), qp_success=bool(opt.success))
    return best


def solve_weighted_sequence(sc, qs, tol, p, weight_qp=False, active_frames=None):
    """active_frames: frames where tolerances apply (None = all). Elsewhere s=1, i.e. exactly A."""
    rows = []
    for t, (c, a, h, ids, q) in enumerate(zip(sc['centers'], sc['areas'], sc['hier'], sc['tracks'], qs)):
        prev = prevq = mask = None
        if t:
            lk = {k: i for i, k in enumerate(sc['tracks'][t - 1])}
            mask = np.array([k in lk for k in ids]); prev = np.zeros(len(ids)); prevq = np.zeros(len(ids))
            for i, k in enumerate(ids):
                if mask[i]: j = lk[k]; prev[i] = rows[-1]['x'][j]; prevq[i] = rows[-1]['reference'][j]
        on = active_frames is None or t in active_frames
        s = np.array([tol.get(k, 1.) if on else 1. for k in ids])
        r = solve_frame_weighted(c, a, h, q, s, p, prev, prevq, mask, weight_qp)
        r['feature_ids'] = list(ids); r['s'] = s
        rows.append(r)
    return rows


def stability_tolerance(sc, qs, v0, kappa):
    """Per-track tolerance from mean reference speed over the whole track (offline, constant)."""
    steps = {}
    for t in range(1, len(qs)):
        lk = {k: i for i, k in enumerate(sc['tracks'][t - 1])}
        for i, k in enumerate(sc['tracks'][t]):
            if k in lk: steps.setdefault(k, []).append(abs(qs[t][i] - qs[t - 1][lk[k]]))
    return {k: 1 + kappa * min(1., float(np.mean(v)) / v0) for k, v in steps.items()}


# ---------------------------------------------------------------- metrics
def motion_metrics(sc, rows, v0):
    false_motion, missed = [], []
    for t in range(1, len(rows)):
        lk = {k: i for i, k in enumerate(sc['tracks'][t - 1])}
        for i, k in enumerate(sc['tracks'][t]):
            if k not in lk: continue
            j = lk[k]
            dq = rows[t]['reference'][i] - rows[t - 1]['reference'][j]; du = rows[t]['x'][i] - rows[t - 1]['x'][j]
            (false_motion if abs(dq) < v0 else missed).append(abs(du - dq))
    return dict(stationary_false_motion_mean=float(np.mean(false_motion)) if false_motion else 0.,
                stationary_false_motion_total=float(np.sum(false_motion)),
                moving_motion_error_mean=float(np.mean(missed)) if missed else 0.)


def disclosure(rows, theta):
    """C: readable position = q where a ghost is drawn (|u-q|>theta), else u."""
    marks = [int(np.sum(abs(r['x'] - r['reference']) > theta)) for r in rows]
    eff = np.concatenate([np.where(abs(r['x'] - r['reference']) > theta, 0., abs(r['x'] - r['reference'])) for r in rows])
    return dict(ghost_marks_total=int(sum(marks)), frames_with_ghosts=int(sum(m > 0 for m in marks)),
                effective_read_error_max=float(eff.max()), effective_read_error_mean=float(eff.mean()))


def evaluate(sc, rows, p, v0, theta, focus=None):
    e = np.concatenate([abs(r['x'] - r['reference']) for r in rows])
    m = dict(ref_err_max=float(e.max()), ref_err_mean=float(e.mean()), ref_err_max_norm=float(e.max() / p.canvas),
             **motion_metrics(sc, rows, v0))
    if focus:
        for name, k in focus.items():
            tt = [t for t in range(len(rows)) if k in sc['tracks'][t]]
            u = np.array([rows[t]['x'][sc['tracks'][t].index(k)] for t in tt])
            q = np.array([rows[t]['reference'][sc['tracks'][t].index(k)] for t in tt])
            m[f'{name}_apparent_drift'] = float(np.max(abs((u - u[0]) - (q - q[0]))))
            m[f'{name}_err_last'] = float(abs(u[-1] - q[-1]))
    return m


# ------------------------------------------------------------------ figure
def draw(ax, sc, rows, maps, p, title, theta=None, per=None, truth=None, lo=0, hi=1):
    T = len(rows)
    ax.imshow(maps, origin='lower', aspect='auto', extent=[-.5, T - .5, p.canvas_origin, p.canvas_origin + p.canvas],
              vmin=lo, vmax=hi, cmap='magma')
    if theta is not None and per is not None:
        for d in per:
            if d['tau_free'] is not None and d['tau_hier'] - d['tau_free'] > theta:
                ax.axvspan(d['t'] - .5, d['t'] + .5, color='#e69f00', alpha=.12, lw=0)
    tracks = sorted(set(k for fr in sc['tracks'] for k in fr))
    for k in tracks:
        tt = [t for t in range(T) if k in sc['tracks'][t]]
        if len(tt) < 3: continue
        ix = [sc['tracks'][t].index(k) for t in tt]
        u = np.array([rows[t]['x'][i] for t, i in zip(tt, ix)]); q = np.array([rows[t]['reference'][i] for t, i in zip(tt, ix)])
        ax.plot(tt, u, '-', color='white', lw=.9)
        if theta is not None:
            bad = abs(u - q) > theta
            for t, uu, qq in zip(np.array(tt)[bad], u[bad], q[bad]):
                ax.plot([t, t], [uu, qq], color='#56b4e9', lw=.5, alpha=.8)
            ax.plot(np.array(tt)[bad], q[bad], '_', color='#56b4e9', ms=5, mew=1.3)
    if truth is not None:
        for label, (vals, style) in truth.items():
            ax.plot(np.arange(len(vals)) if np.ndim(vals) else [0, T - 1], vals if np.ndim(vals) else [vals, vals],
                    style, lw=1.1, label=label)
        ax.legend(loc='upper right', fontsize=6.5, framealpha=.6)
    ax.set(title=title, xlabel='time step')


def run_scene(scene, kappa=4.):
    sc, p = scene['sc'], scene['p_ref']
    v0 = .005 * p.canvas            # "stationary" = reference moves < 0.5% of axis per step
    theta = max(2 * p.gap, .02 * p.canvas)
    tol = stability_tolerance(sc, scene['qs'], v0, kappa)
    rowsA = solve_weighted_sequence(sc, scene['qs'], {}, p)
    ref = tr.solve_scalar_reference(sc, scene['qs'], p)       # collaborator solver, for the sanity check
    sanity = dict(max_anchor_diff_compactA_vs_solve_frame=float(max(np.max(abs(a['x'] - r['x'])) for a, r in zip(rowsA, ref))),
                  max_tau_diff=float(max(abs(a['tau'] - r['tau']) for a, r in zip(rowsA, ref))))
    per = tr.summarize(sc, ref, p, p.canvas)['per_frame']
    # B is gated by the certificate: re-weight only where the HIERARCHY cost exceeds theta
    conflict = {d['t'] for d in per if d['tau_free'] is not None and d['tau_hier'] - d['tau_free'] > theta}
    rowsB = solve_weighted_sequence(sc, scene['qs'], tol, p, active_frames=conflict)
    rowsBu = solve_weighted_sequence(sc, scene['qs'], tol, p)                   # ablation: ungated
    rowsBq = solve_weighted_sequence(sc, scene['qs'], tol, p, weight_qp=True)   # ablation: ungated + QP weights
    out = dict(parameters=dict(v0=v0, theta=theta, kappa=kappa), sanity=sanity,
               conflict_frames=sorted(conflict), tolerances={int(k): v for k, v in tol.items()})
    maps = {}
    for name, rows in [('A', rowsA), ('B', rowsB), ('B_ungated', rowsBu), ('B_ungated_qpweighted', rowsBq)]:
        validate_weighted(sc, rows, p)
        maps[name], *_ = tr.render_checked(sc, rows, p, scene['nominal'])
        out[name] = evaluate(sc, rows, p, v0, theta, scene.get('focus'))
        out[name + '+C'] = {**out[name], **disclosure(rows, theta)}
    return out, rowsA, rowsB, maps, per, theta


def validate_weighted(sc, rows, p):
    for t, (r, a, h) in enumerate(zip(rows, sc['areas'], sc['hier'])):
        o = np.array(r['order'])
        assert tuple(o) in leaf_orders(h), t
        assert np.allclose(r['w'], p.width_scale * a, atol=1e-12), t
        assert np.min(r['z'] - r['w'] / 2) >= p.canvas_origin - 1e-6 and np.max(r['z'] + r['w'] / 2) <= p.canvas_origin + p.canvas + 1e-6, t
        assert np.all(abs(r['x'] - r['z']) <= p.rho * r['w'] / 2 + 1e-6), t
        assert np.all(np.diff(r['z'][o]) - (r['w'][o[:-1]] + r['w'][o[1:]]) / 2 >= p.gap - 1e-6), t
        assert np.all(abs(r['x'] - r['reference']) <= r['s'] * r['budget'] + 1e-6), t


def gaussian_with_focus():
    scene = tr.gaussian_scene()
    fields, coords, meta = tr.gaussian_fields()
    ext0 = scene['ext'][0]; ids0 = scene['sc']['tracks'][0]
    near = lambda pt: ids0[int(np.argmin(np.linalg.norm(ext0 - pt, axis=1)))]
    scene['focus'] = dict(l2=near(meta['l2']), l3=near(meta['l3'][0]))
    scene['truth_lines'] = {'true d(l3,l1)': (np.linalg.norm(meta['l3'] - meta['l1'], axis=1), ':'),
                            'true d(l2,l1)': (float(np.linalg.norm(meta['l2'] - meta['l1'])), ':')}
    return scene


def main():
    report = {}
    for scene in (gaussian_with_focus(), tr.ring_scene()):
        print('running', scene['name'], flush=True)
        out, rowsA, rowsB, maps, per, theta = run_scene(scene)
        report[scene['name']] = out
        sc, p = scene['sc'], scene['p_ref']
        lo, hi = np.quantile(sc['fields'], [0, 1])
        truth = scene.get('truth_lines') or {scene['truth']['label']: (scene['truth']['values'], ':')}
        fig, axs = plt.subplots(1, 4, figsize=(16, 4.6), sharey=True, layout='constrained')
        ylim = (0, min(p.canvas, 1.2 * max(max(np.max(r['x']) for r in rowsA), np.max(scene['truth']['values'])) + 5))
        for ax, (title, rows, key, disc) in zip(axs, [('A  min-max compromise', rowsA, 'A', False),
                                                      ('B  stability priority', rowsB, 'B', False),
                                                      ('A + C  disclosure', rowsA, 'A', True),
                                                      ('B + C  (proposed)', rowsB, 'B', True)]):
            draw(ax, sc, rows, maps[key], p, title, theta if disc else None, per if disc else None, truth, lo, hi)
            ax.set_ylim(*ylim)
        axs[0].set_ylabel(scene['label'])
        fig.suptitle(f"{scene['name']}: conflict strategies  (white = anchor u; blue tick = true reference q, "
                     f"drawn when |u−q| > θ={theta:.1f}; orange = frames where hierarchy cost > θ)", fontsize=10)
        fig.savefig(OUT / f"{scene['name']}_conflict_strategies.png", dpi=160); plt.close(fig)
        print(json.dumps(out, indent=1, default=float), flush=True)
    (OUT / 'conflict_metrics.json').write_text(json.dumps(report, indent=1, default=float))


if __name__ == '__main__':
    main()
