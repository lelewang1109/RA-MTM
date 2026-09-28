"""Prototype: task-referenced merge tree maps (one map, task-defined reference).

Does not modify the collaborator's solver. Reuses solve_frame with an explicit
per-leaf scalar reference q_i = phi(E_i, t), where E_i is the leaf extremum.

Scenes
  ring      : phi = radial distance from the ring epicentre.
  gaussians : replica of the ST-MTM motivating scene (two static blobs l1, l2 on a
              shared plateau + one moving blob l3); phi = distance to focus l1.

Validation per scene
  - collaborator invariants (legal leaf order, exact widths, gaps, canvas, budget)
  - rendered 1-D scalar map has the same merge-tree signature as the input frame
  - hierarchy cost: tau* with the merge-tree hierarchy vs. tau* over all orders
Run: .venv/bin/python prototypes/task_reference.py
"""
from pathlib import Path
import sys, json, time
from itertools import permutations
from dataclasses import replace, asdict
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
from experiments import era5 as ep
from experiments.ring.dataset import generate
from ramtm.error_budget import (Parameters, solve_frame, solve_sequence, constraints,
                                checked_lp, leaf_orders, InfeasibleLayout)
from ramtm.reference_anchored import render_sequence
from ramtm.reference_points import reference_points_from_frames

OUT = ROOT / 'prototypes' / 'output'
plt = ep.plt


# ---------------------------------------------------------------- solving
def solve_scalar_reference(sc, qs, p):
    """solve_sequence with an explicit scalar reference per leaf (same temporal logic)."""
    rows = []
    for t, (c, a, h, ids, q) in enumerate(zip(sc['centers'], sc['areas'], sc['hier'], sc['tracks'], qs)):
        previous = previous_q = mask = None
        if t:
            lookup = {k: i for i, k in enumerate(sc['tracks'][t - 1])}
            mask = np.array([k in lookup for k in ids])
            previous = np.zeros(len(ids)); previous_q = np.zeros(len(ids))
            for i, k in enumerate(ids):
                if mask[i]:
                    j = lookup[k]; previous[i] = rows[-1]['x'][j]; previous_q[i] = rows[-1]['reference'][j]
        row = solve_frame(c, a, h, previous, previous_q, p, mask, reference=np.asarray(q, float))
        row['feature_ids'] = list(ids)
        rows.append(row)
    return rows


def lp_tau(w, q, order, p):
    n = len(w)
    A, b, bounds = constraints(w, order, p)
    L = np.c_[-A, np.zeros(len(A))]
    E = np.c_[np.eye(n), np.zeros((n, n)), -np.ones(n)]
    F = np.c_[-np.eye(n), np.zeros((n, n)), -np.ones(n)]
    r = checked_lp(np.r_[np.zeros(2 * n), 1.], np.vstack([L, E, F]), np.r_[-b, q, -q], bounds + [(0, None)])
    return None if r is None else float(r.fun)


def free_tau(w, q, p, exact_limit=7):
    """Min-max reference deviation over ALL leaf orders (hierarchy dropped)."""
    n = len(w)
    orders = permutations(range(n)) if n <= exact_limit else [tuple(np.argsort(q))]
    vals = [v for o in orders if (v := lp_tau(w, q, o, p)) is not None]
    return (min(vals) if vals else None), n <= exact_limit


# -------------------------------------------------------------- rendering
def render_checked(sc, rows, p, length):
    attempts = []
    while True:
        try:
            maps, ds, errors = render_sequence(sc['frames'], sc['ids'], rows, p.canvas, length,
                                               canvas_origin=p.canvas_origin)
        except ValueError as e:
            if 'increase resolution' not in str(e) or length >= 131072: raise
            attempts.append(dict(length=length, reason='raster')); length *= 2; continue
        bad = [t for t, tr in enumerate(sc['trees']) if ep.signature(maps[:, t], tr.kind) != ep.signature(tr)]
        attempts.append(dict(length=length, topology_failed=bad))
        if not bad: return maps, ds, errors, length, attempts
        if length >= 131072: raise RuntimeError('topology mismatch persists')
        length *= 2


def validate(sc, rows, p):
    """Collaborator's invariants from experiments/public.py::solve_view."""
    for t, (r, a, h) in enumerate(zip(rows, sc['areas'], sc['hier'])):
        o = np.array(r['order'])
        assert tuple(o) in leaf_orders(h), t
        assert np.allclose(r['w'], p.width_scale * a, rtol=0, atol=1e-12), t
        assert np.min(r['z'] - r['w'] / 2) >= p.canvas_origin - 1e-6, t
        assert np.max(r['z'] + r['w'] / 2) <= p.canvas_origin + p.canvas + 1e-6, t
        assert np.all(abs(r['x'] - r['z']) <= p.rho * r['w'] / 2 + 1e-6), t
        assert np.all(np.diff(r['z'][o]) - (r['w'][o[:-1]] + r['w'][o[1:]]) / 2 >= p.gap - 1e-6), t
        assert np.max(abs(r['x'] - r['reference'])) <= r['budget'] + 1e-6, t
        assert r['tau'] - 1e-6 <= np.max(abs(r['x'] - r['reference'])), t


def summarize(sc, rows, p, span_for_norm):
    per = []
    for t, (r, a) in enumerate(zip(rows, sc['areas'])):
        e = r['x'] - r['reference']
        tf, exact = free_tau(p.width_scale * np.asarray(a), r['reference'], p)
        per.append(dict(t=t, leaves=len(a), tau_hier=r['tau'], tau_free=tf, tau_free_exact=exact,
                        max_abs_err=float(np.max(abs(e))), mean_abs_err=float(np.mean(abs(e))),
                        total_width=float(np.sum(r['w']))))
    errs = np.concatenate([abs(r['x'] - r['reference']) for r in rows])
    hc = [d['tau_hier'] - d['tau_free'] for d in per if d['tau_free'] is not None]
    return dict(per_frame=per,
                reference_nmae=float(errs.mean() / span_for_norm),
                reference_p95_norm=float(np.quantile(errs, .95) / span_for_norm),
                tau_max=float(max(d['tau_hier'] for d in per)),
                frames_with_conflict=int(sum(d['tau_hier'] > 1e-6 for d in per)),
                frames_with_hierarchy_cost=int(sum(x > 1e-6 for x in hc)),
                hierarchy_cost_max=float(max(hc)) if hc else None)


# ----------------------------------------------------------------- scenes
def ring_scene():
    fields, coords, meta = generate()
    sc = ep.scene_from_fields(fields, coords, 210 ** 2 / 196, 'split')
    centre = np.array(meta['actual_float32_property_values']['center'])
    ext = reference_points_from_frames(sc['frames'], sc['ids'], kind='extremum')
    qs = [np.linalg.norm(e - centre, axis=1) for e in ext]
    span = 210.
    base = replace(ep.P, canvas=span, width_scale=1 / (2 * span), rho=.5, gap=.5 * span / 120, extra_budget=span / 120)
    rmax = float(np.ceil(np.max(np.linalg.norm(coords - centre, axis=1))))
    p_ref = replace(base, canvas=rmax)
    radius = np.array([meta['actual_float32_property_values']['mu0'] + t * meta['actual_float32_property_values']['muChange']
                       for t in range(len(fields))])
    return dict(name='ring', sc=sc, qs=qs, ext=ext, p_ref=p_ref, p_x=base, span=span, nominal=196,
                label='Radial distance from ring centre', truth=dict(label='analytic ring radius', values=radius),
                meta=dict(centre=centre.tolist(), canvas=rmax))


def gaussian_fields(T=64, n=64, span=120.):
    g = np.linspace(0, span, n); X, Y = np.meshgrid(g, g)
    l1, l2 = np.array([25., 25.]), np.array([85., 85.])
    # l3 starts near l2 (39 units) and ends equidistant from l1 and l2 (51 units each),
    # never crossing l2 or the l1-l2 ridge; d(l3,l1) drops below d(l2,l1)=85 mid-sequence.
    start, end = np.array([115., 60.]), np.array([75., 35.])
    s = 7.
    def blob(c, amp): return amp * np.exp(-((X - c[0]) ** 2 + (Y - c[1]) ** 2) / (2 * s * s))
    # plateau (ridge) joining l1-l2 so they merge high in the split tree; l3 stays isolated
    d = l2 - l1; tt = np.clip(((X - l1[0]) * d[0] + (Y - l1[1]) * d[1]) / (d @ d), 0, 1)
    ridge = .5 * np.exp(-((X - (l1[0] + tt * d[0])) ** 2 + (Y - (l1[1] + tt * d[1])) ** 2) / (2 * 9. ** 2))
    fields, l3 = [], []
    for t in range(T):
        c3 = start + (end - start) * min(1., t / (T * .8)); l3.append(c3)
        fields.append(blob(l1, 1.) + blob(l2, .95) + ridge + blob(c3, 1.05))
    coords = np.c_[X.ravel(), Y.ravel()]
    return np.asarray(fields, np.float64), coords, dict(l1=l1, l2=l2, l3=np.array(l3), span=span)


def gaussian_scene():
    fields, coords, meta = gaussian_fields()
    span = meta['span']
    sc = ep.scene_from_fields(fields, coords, (span / 63) ** 2, 'split')
    ext = reference_points_from_frames(sc['frames'], sc['ids'], kind='extremum')
    # focus = the track whose extremum is nearest l1 in the first frame (fixed identity)
    focus_track = sc['tracks'][0][int(np.argmin(np.linalg.norm(ext[0] - meta['l1'], axis=1)))]
    qs = []
    for e, tr in zip(ext, sc['tracks']):
        f = e[tr.index(focus_track)]
        qs.append(np.linalg.norm(e - f, axis=1))
    diag = float(np.ceil(span * np.sqrt(2)))
    base = replace(ep.P, canvas=span, width_scale=.25 * span / (span * span), rho=.5, gap=.5, extra_budget=1.)
    p_ref = replace(base, canvas=diag)
    d12 = float(np.linalg.norm(meta['l2'] - meta['l1']))
    return dict(name='gaussians', sc=sc, qs=qs, ext=ext, p_ref=p_ref, p_x=base, span=span, nominal=2048,
                label=f'Distance to focus feature (track {focus_track})',
                truth=dict(label='true d(l3,l1)', values=np.linalg.norm(meta['l3'] - meta['l1'], axis=1), d12=d12),
                meta=dict(focus_track=int(focus_track), canvas=diag, d12=d12))


# -------------------------------------------------------------------- run
def run(scene):
    sc, p = scene['sc'], scene['p_ref']
    t0 = time.perf_counter()
    rows = solve_scalar_reference(sc, scene['qs'], p); t_solve = time.perf_counter() - t0
    validate(sc, rows, p)
    maps, ds, raster, length, attempts = render_checked(sc, rows, p, scene['nominal'])
    summ = summarize(sc, rows, p, p.canvas)
    # contrast: single X-axis RA view on the same extremum targets (current mainline X view)
    px = scene['p_x']
    xrows = solve_sequence(sc['centers'], sc['areas'], sc['hier'], px, reference_axis=0,
                           feature_ids=sc['tracks'], reference_points=scene['ext'])
    xmaps, *_ = render_checked(sc, xrows, px, scene['nominal'])
    base = {}
    for m in ['TMTM', 'ST-MTM']:
        try:
            kw = dict(canvas=scene['span'], length=scene['nominal'], refine_raster=False, strict_checks=False)
            if scene['name'] == 'ring': kw['stmtm_parameters'] = ep.b2.LayoutParameters.from_preset('ring')
            base[m] = ep.run_method(sc, m, px, **kw)['maps']
        except Exception as e:  # baselines are context only; record, don't hide
            base[m] = None; summ.setdefault('baseline_errors', {})[m] = repr(e)
    summ.update(scene=scene['name'], frames=len(rows), leaves_per_frame=[len(a) for a in sc['areas']],
                solve_seconds=t_solve, raster_length=length, raster_attempts=attempts,
                topology_equal_all_frames=True, invariants='passed', parameters=asdict(p), meta=scene['meta'])
    # truth readout (analytic): how far are the task-relevant anchors from the analytic quantity?
    tr = scene['truth']['values']
    if scene['name'] == 'ring':
        dev = [np.mean(abs(r['x'] - tr[t])) for t, r in enumerate(rows) if tr[t] > 5]
        summ['anchor_vs_analytic_radius_mae'] = float(np.mean(dev))
    else:
        l3_track = [k for k in sc['tracks'][-1] if k != scene['meta']['focus_track']]
        summ['tracks_last_frame'] = sc['tracks'][-1]
    figure(scene, rows, maps, xmaps, base, summ)
    return summ, rows


def figure(scene, rows, maps, xmaps, base, summ):
    sc, p = scene['sc'], scene['p_ref']; T = len(rows); times = np.arange(T)
    lo, hi = np.quantile(sc['fields'], [0, 1]); cmap = 'magma'
    fig = plt.figure(figsize=(15, 6.2))
    gs = fig.add_gridspec(2, 4, height_ratios=[1, 4], hspace=.08, wspace=.28, left=.05, right=.98, top=.88, bottom=.1)
    panels = [('TMTM', base.get('TMTM'), (0, 1), 'native position / extent'),
              ('ST-MTM', base.get('ST-MTM'), (0, 1), 'native position / extent'),
              ('RA-MTM, world-X reference', xmaps, (0, scene['p_x'].canvas), 'world x')]
    for j, (title, m, ext, yl) in enumerate(panels):
        ax = fig.add_subplot(gs[1, j])
        if m is None: ax.text(.5, .5, 'baseline failed\n(see metrics)', ha='center'); ax.set_axis_off(); continue
        ax.imshow(m, origin='lower', aspect='auto', extent=[-.5, T - .5, *ext], vmin=lo, vmax=hi, cmap=cmap)
        ax.set(title=title, xlabel='time step', ylabel=yl)
    ax = fig.add_subplot(gs[1, 3])
    im = ax.imshow(maps, origin='lower', aspect='auto', extent=[-.5, T - .5, p.canvas_origin, p.canvas_origin + p.canvas],
                   vmin=lo, vmax=hi, cmap=cmap)
    # certificate overlay: reference (dashed) vs anchor (solid) for each track
    tracks = sorted(set(k for fr in sc['tracks'] for k in fr))
    for k in tracks:
        tt = [t for t in range(T) if k in sc['tracks'][t]]
        if len(tt) < 3: continue
        ix = [sc['tracks'][t].index(k) for t in tt]
        ax.plot(tt, [rows[t]['reference'][i] for t, i in zip(tt, ix)], '--', color='#56b4e9', lw=.8)
        ax.plot(tt, [rows[t]['x'][i] for t, i in zip(tt, ix)], '-', color='white', lw=.8)
    tv = scene['truth']['values']
    ax.plot(times, tv, ':', color='#00ff88', lw=1.4, label=scene['truth']['label'])
    if 'd12' in scene['truth']: ax.axhline(scene['truth']['d12'], color='#e69f00', lw=1, ls=':', label='true d(l2,l1)')
    ax.set(title='Task-referenced RA-MTM (proposed)', xlabel='time step', ylabel=scene['label'],
           ylim=(0, min(p.canvas, 1.15 * max(np.max(tv), max(np.max(r['x']) for r in rows)) + 10)))
    ax.legend(loc='upper left', fontsize=7, framealpha=.6)
    cax = fig.add_subplot(gs[0, 3], sharex=ax)
    per = summ['per_frame']
    cax.bar(times, [d['tau_hier'] for d in per], color='#d55e00', width=.9, label='τ* (hierarchy)')
    cax.plot(times, [d['tau_free'] if d['tau_free'] is not None else np.nan for d in per], 'k.', ms=3, label='τ* (no hierarchy)')
    cax.set(ylabel='τ*'); cax.tick_params(labelbottom=False); cax.legend(fontsize=7, loc='upper left', ncol=2)
    fig.colorbar(im, ax=fig.axes[:4], orientation='horizontal', fraction=.03, pad=.12, label='scalar value')
    fig.suptitle(f"{scene['name']}: one task-referenced map vs baselines   "
                 f"(dashed = reference q, solid = anchor u; top strip = certificate τ*)", fontsize=11)
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{scene['name']}_task_reference.png", dpi=170)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    for make in (ring_scene, gaussian_scene):
        scene = make(); print('running', scene['name'], flush=True)
        summ, _ = run(scene)
        report[scene['name']] = summ
        print({k: v for k, v in summ.items() if k not in ('per_frame', 'parameters', 'raster_attempts', 'leaves_per_frame')}, flush=True)
    (OUT / 'metrics.json').write_text(json.dumps(report, indent=1, default=float))


if __name__ == '__main__':
    main()
