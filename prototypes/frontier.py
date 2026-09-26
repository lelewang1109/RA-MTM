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
    # frontier
    Phi = np.zeros((len(DELTAS), len(s0)))
    for t, (fr, st) in enumerate(zip(sc['frames'], s0)):
        w = p.width_scale * np.asarray(sc['areas'][t]); q = ref['qs'][t]
        Phi[:, t] = th.frontier_frame(fr, st, w, q, p, NPIX, [d * rng for d in DELTAS])
    frontier = [dict(delta=d, mean_Phi_share=float(np.mean(Phi[k]) / L)) for k, d in enumerate(DELTAS)]
    # achieved points + theorem check
    ach, checks = [], dict(frames=0, violated_frames=0, theorem_violations=0, min_slack=np.inf, ratio=[])
    for cap in CAPS:
        o = rh.run(ds, cap, make_figure=False, return_internal=True)
        R = o['_internal']['results']['R_relaxed']; rows = R['_rows']; me = R['_me']
        maxerr = np.array([np.max(abs(r['x'] - r['reference'])) for r in rows])
        dtop = np.array([m.max() if len(m) else 0. for m in me])
        for t, (fr, st, r) in enumerate(zip(sc['frames'], s0, rows)):
            checks['frames'] += 1
            bad = th.violated_nodes(st, tuple(int(i) for i in r['order']))
            if not bad: continue
            checks['violated_frames'] += 1
            bound = max(abs(float(fr.values[par] - fr.values[v])) for v, par in bad) / 2
            slack = dtop[t] - bound
            checks['min_slack'] = min(checks['min_slack'], slack / rng)
            if slack < -1e-6 * rng: checks['theorem_violations'] += 1
            if bound > 0: checks['ratio'].append(dtop[t] / (2 * bound))
        D = float(dtop.max()); E = float(maxerr.mean())
        # frontier at the achieved distortion (per frame Phi_t(D), interpolated on the delta grid, conservative: next grid point below)
        k = max(i for i, d in enumerate(DELTAS) if d * rng <= D + 1e-12)
        ach.append(dict(cap=cap, D_share=D / rng, E_share=E / L, frontier_at_D=float(np.mean(Phi[k]) / L),
                        mean_dtop_share=float(dtop.mean() / rng)))
    r = np.array(checks.pop('ratio')) if checks['ratio'] else np.array([np.nan])
    checks.update(ratio_median=float(np.nanmedian(r)), ratio_min=float(np.nanmin(r)), ratio_max=float(np.nanmax(r)))
    return dict(dataset=name, axis=L, value_range=rng, frontier=frontier, achieved=ach, theorem2_check=checks)


def main():
    res = {}
    for n in rp.LOADERS:
        print('running', n, flush=True); res[n] = analyse(n)
        c = res[n]['theorem2_check']
        print(f"  Theorem 2: {c['violated_frames']} frames with broken contiguity (of {c['frames']} frame-runs); "
              f"violations {c['theorem_violations']}; min slack {c['min_slack']:.4f} of range; "
              f"d_top / full gap: median {c['ratio_median']:.2f} [min {c['ratio_min']:.2f}, max {c['ratio_max']:.2f}]", flush=True)
        for a in res[n]['achieved']:
            print(f"   cap {a['cap']:>4}: achieved (D {a['D_share']:.3f}, E {a['E_share']:.3f})  frontier at D {a['frontier_at_D']:.3f}", flush=True)
    (OUT / 'frontier.json').write_text(json.dumps(res, indent=1, default=float))
    fig, axs = plt.subplots(1, len(res), figsize=(3.4 * len(res), 3.4), layout='constrained')
    for ax, (n, r) in zip(axs, res.items()):
        ax.step([f['delta'] * 100 for f in r['frontier']], [f['mean_Phi_share'] * 100 for f in r['frontier']], where='post',
                color='k', label='provable lower frontier Φ')
        ax.plot([a['D_share'] * 100 for a in r['achieved']], [a['E_share'] * 100 for a in r['achieved']], 'o-', color='#009e73', label='ours (κ sweep)')
        ax.set(title=n, xlabel='topological distortion d_top (% of value range)', ylabel='mean per-frame max position error (% axis)' if n == 'era5' else '')
        ax.set_xlim(-2, 102)
    axs[0].legend(fontsize=7)
    fig.suptitle('No 1-D map can lie below the black frontier (Theorem 2 + Corollary); green = achieved by certificate-driven relaxation', fontsize=10)
    fig.savefig(OUT / 'frontier.png', dpi=150); plt.close(fig)


if __name__ == '__main__':
    main()
