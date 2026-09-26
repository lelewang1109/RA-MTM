"""Theorem 2 check and position-topology frontier on all datasets.

For every relaxation cap kappa and every frame:
  - d_top_t          measured merge-level distortion of the rendered 1-D map (max over leaf pairs)
  - violated nodes   nodes of the ORIGINAL tree whose leaf set is non-contiguous in the map order
  - Theorem 2 bound  max over violated v of (f(parent v) - f(v)) / 2   -> must satisfy d_top_t >= bound
Lower frontier (Corollary): Phi_t(delta) = tau*(flatten all nodes with gap <= 2 delta), exact by DP.
Any 1-D map satisfies  maxerr_t >= Phi_t(d_top_t);  aggregated: mean_t maxerr_t >= mean_t Phi_t(D), D = max_t d_top_t.
Run: .venv/bin/python -W ignore prototypes/frontier.py
"""
from pathlib import Path
import sys, json
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import theory as th, relax_hierarchy as rh, replicate as rp, task_reference as tr

OUT = tr.OUT; plt = tr.plt
CAPS = [0., .01, .02, .05, .1, .2, .5, np.inf]
DELTAS = [0., .005, .01, .02, .05, .1, .15, .2, .3, .5, .75, 1.]     # fraction of value range
NPIX = 1024


def analyse(name):
    ds = rp.LOADERS[name](); sc = ds['sc']
    rng = float(np.ptp(sc['fields']))
    base = rh.run(ds, 0., make_figure=False, return_internal=True)['_internal']
    ref, p = base['ref'], base['p']; L = p.canvas
    s0 = [rh.node_tree(fr, ids) for fr, ids in zip(sc['frames'], sc['ids'])]
    # frontier: exact per-frame step functions, certified lower bounds (relaxed discretisation - half pixel)
    steps = []
    for t, (fr, st) in enumerate(zip(sc['frames'], s0)):
        w = p.width_scale * np.asarray(sc['areas'][t]); q = ref['qs'][t]
        steps.append(th.frontier_steps(fr, st, w, q, p, NPIX))
    grid = sorted(set([0.] + [b for st_ in steps for b, _ in st_] + [d * rng for d in DELTAS]))
    frontier = [dict(delta=g / rng, mean_Phi_share=float(np.mean([th.phi_at(st_, g) for st_ in steps]) / L)) for g in grid]
    # achieved points + theorem check
    ach, checks = [], dict(frames=0, violated_frames=0, theorem_violations=0, min_slack=np.inf, ratio=[])
    for cap in CAPS:
        o = rh.run(ds, cap, make_figure=False, return_internal=True)
        R = o['_internal']['results']['R_relaxed']; rows = R['_rows']; me = R['_me']
        maxerr = np.array([np.max(abs(r['x'] - r['reference'])) for r in rows])
        dtop = np.array([m.max() if len(m) else 0. for m in me])
        for t, (fr, st, r) in enumerate(zip(sc['frames'], s0, rows)):
            checks['frames'] += 1
            if maxerr[t] < th.phi_at(steps[t], dtop[t]) - 1e-9: checks['corollary_violations'] = checks.get('corollary_violations', 0) + 1
            bad = th.violated_nodes(st, tuple(int(i) for i in r['order']))
            if not bad: continue
            checks['violated_frames'] += 1
            bound = max(abs(float(fr.values[par] - fr.values[v])) for v, par in bad) / 2
            slack = dtop[t] - bound
            checks['min_slack'] = min(checks['min_slack'], slack / rng)
            if slack < -1e-6 * rng: checks['theorem_violations'] += 1
            if bound > 0: checks['ratio'].append(dtop[t] / (2 * bound))
        D = float(dtop.max()); E = float(maxerr.mean())
        ach.append(dict(cap=cap, D_share=D / rng, E_share=E / L, frontier_at_D=float(np.mean([th.phi_at(st_, D) for st_ in steps]) / L),
                        frontier_per_frame_mean=float(np.mean([th.phi_at(st_, dt_) for st_, dt_ in zip(steps, dtop)]) / L),
                        mean_dtop_share=float(dtop.mean() / rng), unresolved_frames=int(o['frames_still_over_theta_after_relax'])))
    r = np.array(checks.pop('ratio')) if checks['ratio'] else np.array([np.nan])
    checks.setdefault('corollary_violations', 0)
    checks.update(ratio_median=float(np.nanmedian(r)), ratio_min=float(np.nanmin(r)), ratio_max=float(np.nanmax(r)),
                  ratio_p90=float(np.nanpercentile(r, 90)))
    return dict(dataset=name, axis=L, value_range=rng, frontier=frontier, achieved=ach, theorem2_check=checks)


def main():
    res = {}
    for n in rp.LOADERS:
        print('running', n, flush=True); res[n] = analyse(n)
        c = res[n]['theorem2_check']
        print(f"  Theorem 2: {c['violated_frames']} frames with broken contiguity (of {c['frames']} frame-runs); "
              f"violations {c['theorem_violations']}; Corollary-1 per-frame violations {c['corollary_violations']}; min slack {c['min_slack']:.4f} of range; "
              f"d_top / max broken gap: median {c['ratio_median']:.2f}, p90 {c['ratio_p90']:.2f}, max {c['ratio_max']:.2f}", flush=True)
        for a in res[n]['achieved']:
            print(f"   cap {a['cap']:>4}: achieved (D {a['D_share']:.3f}, E {a['E_share']:.3f})  certified frontier at D {a['frontier_at_D']:.3f}; unresolved {a['unresolved_frames']}", flush=True)
    (OUT / 'frontier.json').write_text(json.dumps(res, indent=1, default=float))
    fig, axs = plt.subplots(1, len(res), figsize=(3.4 * len(res), 3.4), layout='constrained')
    for ax, (n, r) in zip(axs, res.items()):
        ax.step([f['delta'] * 100 for f in r['frontier']], [f['mean_Phi_share'] * 100 for f in r['frontier']], where='post',
                color='k', label='certified lower frontier Φ')
        ax.plot([a['D_share'] * 100 for a in r['achieved']], [a['E_share'] * 100 for a in r['achieved']], 'o', color='#009e73', label='ours (κ sweep; points only)')
        ax.set(title=n, xlabel='topological distortion d_top (% of value range)', ylabel='mean per-frame max position error (% axis)' if n == 'era5' else '')
        ax.set_xlim(-2, 102)
    axs[0].legend(fontsize=7)
    fig.suptitle('No 1-D map can lie below the black frontier (Theorem 2 + Corollary); green points = achieved layouts (not connected: only points are achieved)', fontsize=10)
    fig.savefig(OUT / 'frontier.png', dpi=150); plt.close(fig)


if __name__ == '__main__':
    main()
