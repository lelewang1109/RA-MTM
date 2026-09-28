"""Run the full evidence chain identically on every dataset.

  1. certificate: conflict prevalence (H > theta), max / median H, space cost      (RQ1)
  2. trade-off:   relaxation caps kappa in {0, 2%, 20%, inf}                       (RQ3)
  3. misreading:  reversal rates vs 2-D truth and claimed axis, reader eps in {1, 2, 5}%,
                  windows k in {1, 2, 4}, shuffle null, frame-bootstrap CIs       (RQ2)
Outputs prototypes/output/replicate_{summary.json, <dataset>_*.json} and replicate_overview.png.
Run: .venv/bin/python -W ignore prototypes/replicate.py [dataset ...]
"""
from pathlib import Path
import sys, json, time
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import general_method as gm, relax_hierarchy as rh, misreading as mr, datasets_extra as dx, task_reference as tr

OUT = tr.OUT; plt = tr.plt
LOADERS = dict(era5=gm.era5, era5_2014=dx.era5_2014, wildfire=dx.wildfire, ring=gm.ring, gaussians=gm.gaussians)
CAPS = [0., .02, .2, np.inf]
EPS = [.01, .02, .05]


def _js(o):
    return o.tolist() if hasattr(o, 'tolist') else float(o)


def run(name):
    t0 = time.perf_counter(); ds = LOADERS[name](); sc = ds['sc']
    trade = {}
    for cap in CAPS:
        r = rh.run(ds, cap, make_figure=False)
        trade[str(cap)] = dict(r['results']['R_relaxed'], frames_relaxed=r['frames_relaxed'])
        if cap == 0.:
            log = r['frame_log']; theta = r['theta']; L = r['canvas']; frange = r['field_range']; refl = r['reference']
    H = np.array([d['tau_hier'] - d['tau_free'] for d in log]); F = np.array([d['tau_free'] for d in log])
    cert = dict(frames=len(log), leaves=[int(min(map(len, sc['ids']))), int(max(map(len, sc['ids'])))],
                tracks=int(len(set(k for fr in sc['tracks'] for k in fr))), reference=refl, axis=L, theta=theta,
                conflict_frames=int(np.sum(H > theta)), conflict_share=float(np.mean(H > theta)),
                H_max_share=float(H.max() / L), H_median_conflict_share=float(np.median(H[H > theta]) / L) if np.any(H > theta) else 0.,
                space_cost_max_share=float(F.max() / L), field_range=frange, H_per_frame=(H / L).tolist(), F_per_frame=(F / L).tolist())
    cache = mr.method_positions(ds); mis = []; paired = []
    for e in EPS:
        rows, ev, pr = mr.analyse(ds, e, cache); mis += rows; paired += pr
    out = dict(dataset=name, meta=ds.get('meta'), certificate=cert, tradeoff=trade, misreading=mis, paired=paired, seconds=time.perf_counter() - t0)
    (OUT / f'replicate_{name}.json').write_text(json.dumps(out, indent=1, default=_js))
    return out


def overview(results):
    names = list(results)
    fig, axs = plt.subplots(2, len(names), figsize=(3.3 * len(names), 6.2), layout='constrained', squeeze=False)
    methods = ['TMTM', 'ST-MTM', 'fixed-X anchored', 'ours: auto direction', 'ours: relaxed']
    colors = ['#999999', '#56b4e9', '#e69f00', '#0072b2', '#009e73']
    for j, n in enumerate(names):
        r = results[n]; c = r['certificate']
        ax = axs[0, j]; t = np.arange(c['frames'])
        ax.bar(t, np.array(c['F_per_frame']) * 100, color='#999999', width=.9)
        ax.bar(t, np.array(c['H_per_frame']) * 100, bottom=np.array(c['F_per_frame']) * 100, color='#d55e00', width=.9)
        ax.axhline(2, color='k', ls=':', lw=.8)
        ax.set(title=f"{n}\nconflict {c['conflict_frames']}/{c['frames']} frames", xlabel='time step', ylabel='% of axis' if j == 0 else '')
        ax = axs[1, j]; k = 2; nclear = 0
        for i, (m, col) in enumerate(zip(methods, colors)):
            x = [z for z in r['misreading'] if z['method'] == m and z['k'] == k and z['eps_frac'] == .02]
            if not x or x[0]['T2D_clear'] == 0: continue
            x = x[0]; lo, hi = x['T2D_ci95']; nclear = x['T2D_clear']
            ax.bar(i, x['T2D_reversal_rate'] * 100, color=col, yerr=[[max(0, (x['T2D_reversal_rate'] - lo) * 100)], [max(0, (hi - x['T2D_reversal_rate']) * 100)]], capsize=2)
            ax.plot([i - .4, i + .4], [x['T2D_null_reversal_rate'] * 100] * 2, 'k--', lw=.8)
        ax.set_xticks(range(len(methods)), ['TMTM', 'ST', 'fixX', 'A', 'R'], fontsize=8)
        ax.set(ylabel='sign-disagreement rate % (vs 2-D)' if j == 0 else '', title=f'k={k}, n={nclear}; dashed = permutation null')
    fig.suptitle('Replication: certificate conflicts (top) and approach/separation reversals (bottom); orange = hierarchy cost, grey = space cost', fontsize=10)
    fig.savefig(OUT / 'replicate_overview.png', dpi=150); plt.close(fig)


def summary(results):
    lines = []
    for n, r in results.items():
        c = r['certificate']; tr0 = r['tradeoff']['0.0']; t2 = r['tradeoff']['0.02']; t20 = r['tradeoff']['0.2']; ti = r['tradeoff']['inf']
        lines.append(f"\n=== {n}  frames {c['frames']} leaves {c['leaves']} tracks {c['tracks']}  ref: {c['reference']}")
        lines.append(f"  RQ1 conflict frames {c['conflict_frames']}/{c['frames']} ({c['conflict_share']:.0%}); H max {c['H_max_share']:.1%} of axis; "
                     f"median H in conflict {c['H_median_conflict_share']:.1%}; max space cost {c['space_cost_max_share']:.1%}")
        rng = c['field_range']
        def tl(t, tag): return (f"{tag}: mean err {t['ref_err_mean']:.2f} ({(t['ref_err_mean']/tr0['ref_err_mean']-1):+.0%}), "
                                f"merge change max {t['merge_err_max']:.2f} ({t['merge_err_max']/rng:.1%} of range), pairs changed {t['pairs_merge_changed']/max(1,t['pairs']):.1%}")
        lines += ['  RQ3 ' + tl(t2, 'kappa 2%'), '      ' + tl(t20, 'kappa 20%'), '      ' + tl(ti, 'kappa inf')]
        for k in (1, 2, 4):
            row = []
            for m in ['TMTM', 'ST-MTM', 'ours: auto direction', 'ours: relaxed']:
                x = [z for z in r['misreading'] if z['method'] == m and z['k'] == k and z['eps_frac'] == .02][0]
                row.append(f"{m.replace('ours: ','')} {x['T2D_reversal_rate']:.3f}[{x['T2D_ci95'][0] if x['T2D_ci95'] else float('nan'):.2f},{x['T2D_ci95'][1] if x['T2D_ci95'] else float('nan'):.2f}](ch {x['T2D_null_reversal_rate']:.2f})")
            lines.append(f"  RQ2 k={k} n={x['T2D_clear']}: " + ' | '.join(row))
        for e in EPS:
            row = []
            for m in ['TMTM', 'ST-MTM', 'ours: relaxed']:
                x = [z for z in r['misreading'] if z['method'] == m and z['k'] == 2 and z['eps_frac'] == e][0]
                row.append(f"{m.replace('ours: ','')} {x['T2D_reversal_rate']:.3f}(ch {x['T2D_null_reversal_rate']:.2f})")
            lines.append(f"      eps {e:.0%} k=2: " + ' | '.join(row) + f"   relaxed vs own axis {[z for z in r['misreading'] if z['method']=='ours: relaxed' and z['k']==2 and z['eps_frac']==e][0]['claim_reversal_rate']:.3f}")
        lines.append(f"  runtime {r['seconds']:.0f} s")
    return '\n'.join(lines)


if __name__ == '__main__':
    args = sys.argv[1:]
    if args[:1] == ['--summarize']:            # rebuild overview/summary from saved JSON
        results = {n: json.loads((OUT / f'replicate_{n}.json').read_text()) for n in LOADERS if (OUT / f'replicate_{n}.json').exists()}
    else:
        results = {}
        for n in (args or list(LOADERS)):
            print('running', n, flush=True); results[n] = run(n)
    overview(results)
    s = summary(results); print(s)
    (OUT / 'replicate_summary.txt').write_text(s)
