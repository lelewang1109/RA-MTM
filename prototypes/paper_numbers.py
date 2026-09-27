"""Print every number used in paper/pacificvis2027/main.tex (and draft_zh.md), grouped by section, from the saved
JSON outputs. Each line names its source file, so every claim can be traced.
Run: .venv/bin/python prototypes/paper_numbers.py
Sources are produced by: replicate.py, robustness.py, pointcert.py, persistence.py, witness_stats.py, eval_v2.py,
attainable.py, filling.py, generality.py, stmtm_grid.py, sensitivity.py, fig_teaser.py / fig_witness.py (printed values).
"""
import json
from pathlib import Path
OUT = Path(__file__).resolve().parent / 'output'
J = lambda f: json.loads((OUT / f).read_text()) if (OUT / f).exists() else None
REAL = ['era5', 'era5_2014', 'wildfire']; ALL = REAL + ['ring', 'gaussians']
pct = lambda x: f'{100 * x:.1f}%'


def sec(t): print(f'\n== {t}')


sec('RQ1 prevalence (replicate_*.json: certificate)')
for n in ALL:
    r = J(f'replicate_{n}.json')
    if r: c = r['certificate']; print(f"  {n:10s} H>theta {c['conflict_frames']}/{c['frames']} ({pct(c['conflict_share'])}), H max {pct(c['H_max_share'])}, median in conflict {pct(c['H_median_conflict_share'])}, space max {pct(c['space_cost_max_share'])}")
rb = J('robustness.json')
if rb:
    for n, v in rb.items():
        a = [x for x in v if str(x['direction']).startswith('auto')][0]
        fixed = [x['share_theta_2'] for x in v if not str(x['direction']).startswith('auto')]
        print(f"  {n:10s} theta 1%/5%: {pct(a['share_theta_1'])}/{pct(a['share_theta_5'])}; fixed directions {pct(min(fixed))}-{pct(max(fixed))} (robustness.json)")
pc = J('pointcert.json')
if pc:
    for n, r in pc.items():
        print(f"  {n:10s} width-free cert > theta {pct(r['conflict_share_pt'])}; TMTM mean {pct(r['methods']['TMTM']['mean_share'])} ST-MTM {pct(r['methods']['ST-MTM']['mean_share'])}; unavoidable {pct(r['methods']['TMTM']['mean_share'] - r['methods']['TMTM']['excess_mean_share'])} (pointcert.json)")
ps = J('persistence.json')
if ps:
    for n, rows in ps.items():
        print('  ' + f'{n:10s} persistence: ' + '; '.join(f"eps {pct(x['eps'])}: removed {pct(x['removed_share'])}, conflicts {pct(x['conflict_share'])}" for x in rows) + ' (persistence.json)')
wi = J('witness.json')
if wi:
    for n, r in wi.items(): print(f"  {n:10s} witness/tau* median {pct(r['median'])} (witness.json)")

sec('RQ2 reader proxy, k=2, eps=2% (eval_v2.json): reversal / miss / error')
ev = J('eval_v2.json')
if ev:
    for n in REAL + ['ring']:
        if n not in ev: continue
        P = {(x['method'], x['k'], x['eps']): x for x in ev[n]['proxy']}
        print(f"  {n}: clear cases {P[('A', 2, .02)]['clear']}")
        for m in ['TMTM', 'ST-MTM', 'fixed-X anchored', 'A', 'R 2%', 'R 20%', 'R inf', 'oracle q', 'oracle x']:
            x = P.get((m, 2, .02))
            if x: print(f"     {m:16s} {pct(x['reversal']):>6s} / {pct(x['miss']):>6s} / {pct(x['error']):>6s}  null {pct(x['null_reversal'])}  feature-flag recall {pct(x['feature_flag_recall'])} share {pct(x['feature_flag_share'])} lift {x['feature_flag_lift']}")
        for m, d in ev[n]['dstar'].items(): print(f"     delta* {m}: max {pct(d['max_share'])} of range ({d['max']:.2f}), mean {pct(d['mean_share'])}")
        for x in ev[n]['paired']:
            if x['k'] == 2 and x['eps'] == .02:
                print(f"     {x['method']} - {x['other']}: rev {100*x['rev']['diff']:+.1f} [{100*x['rev']['ci95'][0]:+.1f}, {100*x['rev']['ci95'][1]:+.1f}] sig {x['rev']['significant']} ({x['blocks']} blocks)")
    sig = tot = better = 0
    for n in REAL:
        for x in ev[n]['paired']:
            if x['method'] == 'R 20%' and x['other'] == 'ST-MTM':
                tot += 1; better += x['rev']['diff'] < 0; sig += x['rev']['significant'] and x['rev']['diff'] < 0
    print(f"  robustness: R20 < ST-MTM in {better}/{tot} settings, significant in {sig}")

sec('RQ2 ST-MTM parameter grid (stmtm_grid.json)')
sg = J('stmtm_grid.json')
if sg:
    for n, r in sg.items():
        b, e = r['best_reversal'], r['best_error']
        print(f"  {n:10s} best reversal {pct(b['reversal'])} (miss {pct(b['miss'])}, {b['weights']}, r={b['r']}, lambda={b['lam']}); best error {pct(e['error'])}")

sec('RQ3 frontier (attainable_*.json)')
for n in ALL:
    a = J(f'attainable_{n}.json')
    if not a: continue
    t = a['tightness']; print(f"  {n:10s} F-Phi mean {pct(t['gap_mean'])}, within half pixel {t['tight_within_half_pixel']}/{t['breakpoints']}, max {pct(t['gap_max'])}")
    for c in a.get('relaxed_only', []):
        print(f"     {c['policy']:9s} kappa {c['cap']}: conflicts {c.get('conflict_frames')}, resolved {c.get('resolved')}, relaxed {c['relaxed_frames']}, evaluated {c.get('evaluated')}, on frontier {c['on_frontier']}")
fl = J('filling.json')
if fl:
    for n, rows in fl.items():
        print('  ' + f'{n:10s} filling LCA->opt max d_top: ' + '; '.join(f"kappa {x['cap']}: {pct(x['D_lca_share'])}->{pct(x['D_opt_share'])}" for x in rows))
for n in REAL:
    r = J(f'replicate_{n}.json')
    if r:
        t0 = r['tradeoff']['0.0']; rng = r['certificate']['field_range']
        for c in ['0.02', '0.2']:
            t = r['tradeoff'][c]; print(f"  {n:10s} kappa {c}: mean error {t['ref_err_mean']/t0['ref_err_mean']-1:+.0%}, LCA d_top max {t['merge_err_max']:.2f} ({pct(t['merge_err_max']/rng)})")

sec('Hidden costs (eval_v2.json: hidden)')
if ev:
    for n in ['era5', 'wildfire']:
        for m, h in ev[n]['hidden'].items():
            print(f"  {n:10s} {m:16s} flips {h['order_flip_rate']:.3f} jitter {h['jitter']:.3f} stress {h['stress']:.3f} NN {h['nn_preservation']:.3f}")

sec('RQ4 dendrogram (generality.json, dendrogram_demo.json)')
g = J('generality.json'); dd = J('dendrogram_demo.json')
if g:
    for h in g['hierarchies']: print(f"  {h['hierarchy']:42s} tau* {pct(h['tau_star_share'])}, H {pct(h['H_share'])}")
    print('  rank reference: ' + ', '.join(pct(x['tau_star_share']) for x in g['rank_reference']))
    print('  scalability: ' + ', '.join(f"{x['leaves']} leaves {x['seconds']:.2f}s" for x in g['scalability']))
if dd: print(f"  OLO max {pct(dd['olo_max_share'])}, median {pct(dd['olo_median_share'])}, rows over tau* {pct(dd['olo_share_rows_over_tau'])}, reference order max {pct(dd['ref_max_share'])}")

sec('Preprocessing sensitivity (sensitivity.json)')
se = J('sensitivity.json')
if se:
    for k, r in se.items():
        pr = r['proxy'] or {}
        if r.get('error'): print(f"  {k:16s} (proxy failed: {r['error'][:60]})")
        print(f"  {k:16s} leaves {r['leaves_mean']:.1f}, conflicts {pct(r['conflict_share'])}; rev/err " + '  '.join(f"{m} {pct(pr[m]['reversal'])}/{pct(pr[m]['error'])}" for m in pr))
