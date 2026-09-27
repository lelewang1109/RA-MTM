"""General (no per-case input) task-referenced merge tree maps.

Everything below is decided from the data or by one dataset-independent rule:

1. Reference phi (automatic): among directions phi_a(x)=a.x and radial distances
   phi_c(x)=|x-c|, choose the one capturing most of the features' real 2-D motion,
       capture(phi) = sum (Delta phi(E))^2 / sum |Delta E|^2  in [0,1],
   over all matched extremum steps. Direction optimum = top eigenvector of the motion
   scatter (closed form); radial optimum = grid + Nelder-Mead over an extended box.
   If the radial optimum runs to the box edge it is a direction in disguise -> use the
   direction. Sign of a: mean motion projects positive.
2. Model constants: one canvas-relative rule for every dataset (L = axis extent):
   whole-domain area -> half the axis (width_scale = 0.5 L / domain_area),
   gap = L/240, extra budget Delta = L/120, rho = 0.5.
3. Conflict layout: min-max (A). Strategy B (tolerance s_i = 1 + v_i / mean v, gated by
   hierarchy cost > theta) is still computed and reported as an ablation: it does NOT
   generalise (more false motion on Ring and ERA5), so the method does not use it.
4. Disclosure (C): true reference drawn where |u - q| > theta.
   theta = 0.02 L is the single legibility constant, identical for all datasets.
Run: .venv/bin/python -W ignore prototypes/general_method.py
"""
from pathlib import Path
import sys, json, time
from itertools import permutations
from dataclasses import replace, asdict
import numpy as np
from scipy.optimize import minimize
sys.path.insert(0, str(Path(__file__).resolve().parent))
import task_reference as tr
import conflict_strategies as cs
from experiments import era5 as ep
from experiments.ring.dataset import generate
from ramtm.error_budget import Parameters, solve_sequence
from ramtm.reference_points import reference_points_from_frames

ROOT = tr.ROOT; OUT = tr.OUT; plt = tr.plt
THETA_FRACTION = .02            # the one global constant (display legibility)


# ------------------------------------------------------- 1. automatic phi
def motion_pairs(sc, ext):
    prev, cur = [], []
    for t in range(1, len(ext)):
        lk = {k: i for i, k in enumerate(sc['tracks'][t - 1])}
        for i, k in enumerate(sc['tracks'][t]):
            if k in lk: prev.append(ext[t - 1][lk[k]]); cur.append(ext[t][i])
    return np.array(prev), np.array(cur)


def capture_direction(a, P0, P1):
    d = P1 - P0; tot = np.sum(d * d)
    return float(np.sum((d @ a) ** 2) / tot) if tot > 0 else 0.


def capture_radial(c, P0, P1):
    d = P1 - P0; tot = np.sum(d * d)
    dr = np.linalg.norm(P1 - c, axis=1) - np.linalg.norm(P0 - c, axis=1)
    return float(np.sum(dr * dr) / tot) if tot > 0 else 0.


def auto_reference(sc, ext, lo, hi, allow_radial=False):
    """lo, hi: world bounding box of the domain."""
    P0, P1 = motion_pairs(sc, ext); d = P1 - P0
    S = d.T @ d
    w, V = np.linalg.eigh(S); a = V[:, -1]
    if np.sum(d @ a) < 0: a = -a
    cap_dir = capture_direction(a, P0, P1)
    span = hi - lo; blo, bhi = lo - span, hi + span        # extended search box
    gx = np.linspace(blo[0], bhi[0], 61); gy = np.linspace(blo[1], bhi[1], 61)
    best = max(((capture_radial(np.array([x, y]), P0, P1), x, y) for x in gx for y in gy))
    r = minimize(lambda c: -capture_radial(c, P0, P1), best[1:], method='Nelder-Mead',
                 options=dict(xatol=1e-3 * span.max(), fatol=1e-6))
    c = np.clip(r.x, blo, bhi); cap_rad = capture_radial(c, P0, P1)
    at_edge = bool(np.any(np.isclose(c, blo, atol=.02 * span.max()) | np.isclose(c, bhi, atol=.02 * span.max())))
    corners = np.array([[lo[0], lo[1]], [hi[0], lo[1]], [lo[0], hi[1]], [hi[0], hi[1]]])
    cand = dict(direction=dict(capture=cap_dir, a=a.tolist(), angle_deg=float(np.degrees(np.arctan2(a[1], a[0])))),
                radial=dict(capture=cap_rad, c=c.tolist(), at_search_edge=at_edge),
                fixed_x=dict(capture=capture_direction(np.array([1., 0.]), P0, P1)),
                fixed_y=dict(capture=capture_direction(np.array([0., 1.]), P0, P1)),
                matched_steps=int(len(d)))
    # Radial selection is reported but NOT used: on tracked extrema it follows tracking
    # artifacts (Ring: true centre explains 7% of tracked motion). Directions only.
    if allow_radial and cap_rad > cap_dir + 1e-3 and not at_edge:
        kind = 'radial'; qs = [np.linalg.norm(e - c, axis=1) for e in ext]
        origin, extent = 0., float(np.max(np.linalg.norm(corners - c, axis=1)))
        label = f'distance from auto centre ({c[0]:.1f}, {c[1]:.1f})'
    else:
        kind = 'direction'; qs = [e @ a for e in ext]
        proj = corners @ a; origin, extent = float(proj.min()), float(proj.max() - proj.min())
        label = f'position along auto direction {cand["direction"]["angle_deg"]:.0f}°'
    return dict(kind=kind, qs=qs, origin=origin, extent=extent, label=label, candidates=cand)


# ------------------------------------------------- 2. universal constants
def universal_parameters(origin, extent, domain_area):
    L = extent
    return Parameters(canvas=L, canvas_origin=origin, width_scale=.5 * L / domain_area,
                      gap=L / 240, extra_budget=L / 120, rho=.5)


# ------------------------------------------- 3. certificate & conflict gate
def tau_free(w, q, p):
    n = len(w)
    if n <= 6:
        vals = [v for o in permutations(range(n)) if (v := tr.lp_tau(w, q, o, p)) is not None]
        return min(vals), True
    order = list(np.argsort(q)); best = tr.lp_tau(w, q, tuple(order), p); improved = True
    while improved:                                   # adjacent-swap hill climb (upper bound)
        improved = False
        for i in range(n - 1):
            o = order.copy(); o[i], o[i + 1] = o[i + 1], o[i]
            v = tr.lp_tau(w, q, tuple(o), p)
            if v is not None and (best is None or v < best - 1e-9): best, order, improved = v, o, True
    return best, False


def speed_tolerance(sc, qs):
    steps = {}
    for t in range(1, len(qs)):
        lk = {k: i for i, k in enumerate(sc['tracks'][t - 1])}
        for i, k in enumerate(sc['tracks'][t]):
            if k in lk: steps.setdefault(k, []).append(abs(qs[t][i] - qs[t - 1][lk[k]]))
    v = {k: float(np.mean(s)) for k, s in steps.items()}
    vbar = float(np.mean(list(v.values()))) if v else 0.
    return {k: 1 + (x / vbar if vbar > 0 else 0.) for k, x in v.items()}


# ------------------------------------------------------------ datasets
def ring():
    fields, coords, _ = generate()
    sc = ep.scene_from_fields(fields, coords, 210 ** 2 / 196, 'split')
    return dict(name='ring', sc=sc, lo=coords.min(0), hi=coords.max(0), domain_area=210. ** 2, nominal=196,
                cmap='magma', vrange=None, native_span=210.)


def gaussians():
    fields, coords, meta = tr.gaussian_fields()
    span = meta['span']; sc = ep.scene_from_fields(fields, coords, (span / 63) ** 2, 'split')
    return dict(name='gaussians', sc=sc, lo=coords.min(0), hi=coords.max(0), domain_area=64 * 64 * (span / 63) ** 2,
                nominal=1024, cmap='magma', vrange=None, native_span=span, meta=meta)


def era5():
    """Main ERA5 setting since 2026-09-27: expanded window, true minima only (prototypes/era5_expanded.py)."""
    import era5_expanded as ee
    return ee.loader('1999', 'era5')


def era5_crop():
    """Previous setting: protocol window cropped, boundary minima kept."""
    ep.SOURCE = (ROOT / 'data/real/ERA5_MSLP/ERA5_MSLP_19991117_20000114_12h_arco.nc').resolve()
    sc = ep.extract(step=1)
    cell = sc['protocol']['cell_area_layout']; grid = sc['protocol']['grid']
    return dict(name='era5', sc=sc, lo=sc['coords'].min(0), hi=sc['coords'].max(0), domain_area=grid * grid * cell,
                nominal=4096, cmap='RdBu_r', vrange=(1013.25 - 35, 1013.25 + 35), native_span=120.)


# ------------------------------------------------------------------ run
def run(ds):
    sc = ds['sc']; t0 = time.perf_counter()
    ext = reference_points_from_frames(sc['frames'], sc['ids'], kind='extremum')
    ref = auto_reference(sc, ext, ds['lo'], ds['hi'])
    p = universal_parameters(ref['origin'], ref['extent'], ds['domain_area'])
    theta = THETA_FRACTION * p.canvas
    rowsA = cs.solve_weighted_sequence(sc, ref['qs'], {}, p)
    per = []
    for t, (r, a) in enumerate(zip(rowsA, sc['areas'])):
        tf, exact = tau_free(p.width_scale * np.asarray(a), r['reference'], p)
        per.append(dict(t=t, leaves=len(a), tau_hier=r['tau'], tau_free=tf, tau_free_exact=exact))
    conflict = {d['t'] for d in per if d['tau_free'] is not None and d['tau_hier'] - d['tau_free'] > theta}
    tol = speed_tolerance(sc, ref['qs'])
    rowsB = cs.solve_weighted_sequence(sc, ref['qs'], tol, p, active_frames=conflict)
    for rows in (rowsA, rowsB): cs.validate_weighted(sc, rows, p)
    mapsA, *_ = tr.render_checked(sc, rowsA, p, ds['nominal'])
    mapsB, _, _, lengthB, _ = tr.render_checked(sc, rowsB, p, ds['nominal'])
    v0 = .005 * p.canvas                                  # evaluation only
    out = dict(dataset=ds['name'], reference=dict(kind=ref['kind'], label=ref['label'], **ref['candidates']),
               parameters=asdict(p), theta=theta, frames=len(rowsA), leaves_max=max(map(len, sc['ids'])),
               conflict_frames=len(conflict), tau_free_exact_frames=sum(d['tau_free_exact'] for d in per),
               tau_hier_max=float(max(d['tau_hier'] for d in per)),
               hierarchy_cost_max=float(max(d['tau_hier'] - d['tau_free'] for d in per)),
               A=cs.evaluate(sc, rowsA, p, v0, theta), B=cs.evaluate(sc, rowsB, p, v0, theta),
               A_C=cs.disclosure(rowsA, theta), B_C=cs.disclosure(rowsB, theta),
               raster_length=lengthB, topology_equal_all_frames=True, invariants='passed',
               seconds=time.perf_counter() - t0)
    # contrast: collaborator's fixed-X view (their protocol), for the figure only
    base = {}
    px = replace(Parameters(), canvas=ds['native_span'], width_scale=.5 * ds['native_span'] / ds['domain_area'],
                 gap=ds['native_span'] / 240, extra_budget=ds['native_span'] / 120, rho=.5,
                 canvas_origin=float(min(ds['lo'][0], 0.)))
    try:
        xr = solve_sequence(sc['centers'], sc['areas'], sc['hier'], px, reference_axis=0, feature_ids=sc['tracks'],
                            reference_points=ext)
        base['fixed-X RA-MTM'] = (tr.render_checked(sc, xr, px, ds['nominal'])[0], (px.canvas_origin, px.canvas_origin + px.canvas), 'world x')
    except Exception as e:
        out.setdefault('baseline_errors', {})['fixed-X'] = repr(e)
    for m in ['TMTM', 'ST-MTM']:
        try:
            kw = dict(canvas=ds['native_span'], length=ds['nominal'], refine_raster=False, strict_checks=False)
            if ds['name'] == 'ring': kw['stmtm_parameters'] = ep.b2.LayoutParameters.from_preset('ring')
            base[m] = (ep.run_method(sc, m, px, **kw)['maps'], (0, 1), 'native position / extent')
        except Exception as e:
            out.setdefault('baseline_errors', {})[m] = repr(e)
    figure(ds, sc, rowsA, mapsA, p, theta, per, conflict, ref, base)
    return out


def figure(ds, sc, rows, maps, p, theta, per, conflict, ref, base):
    T = len(rows)
    lo, hi = ds['vrange'] or np.quantile(sc['fields'], [0, 1])
    order = ['TMTM', 'ST-MTM', 'fixed-X RA-MTM']
    fig = plt.figure(figsize=(16, 5.2))
    gs = fig.add_gridspec(1, 4, wspace=.25, left=.045, right=.99, top=.84, bottom=.13)
    for j, m in enumerate(order):
        ax = fig.add_subplot(gs[0, j])
        if m not in base: ax.text(.5, .5, f'{m} failed', ha='center'); ax.set_axis_off(); continue
        mp, ext, yl = base[m]
        ax.imshow(mp, origin='lower', aspect='auto', extent=[-.5, T - .5, *ext], vmin=lo, vmax=hi, cmap=ds['cmap'])
        ax.set(title=m, xlabel='time step', ylabel=yl)
    ax = fig.add_subplot(gs[0, 3])
    cs.draw(ax, sc, rows, maps, p, 'General RA-MTM: auto direction + certificate + C', theta,
            [dict(d) for d in per], None, lo, hi)
    ax.images[0].set_cmap(ds['cmap'])
    ax.set_ylabel(ref['label'])
    fig.suptitle(f"{ds['name']}: auto reference = {ref['kind']} "
                 f"(motion captured {ref['candidates'][ref['kind']]['capture']:.2f} vs fixed-X {ref['candidates']['fixed_x']['capture']:.2f}); "
                 f"{len(conflict)} conflict frames; no per-dataset settings", fontsize=10.5)
    fig.savefig(OUT / f"{ds['name']}_general.png", dpi=150); plt.close(fig)


def main():
    report = {}
    for make in (ring, gaussians, era5):
        ds = make(); print('running', ds['name'], flush=True)
        report[ds['name']] = run(ds)
        r = report[ds['name']]
        print(json.dumps({k: r[k] for k in ['reference', 'conflict_frames', 'hierarchy_cost_max', 'A', 'B', 'A_C', 'B_C', 'seconds']},
                         default=float, indent=1), flush=True)
    (OUT / 'general_metrics.json').write_text(json.dumps(report, indent=1, default=float))


if __name__ == '__main__':
    main()
