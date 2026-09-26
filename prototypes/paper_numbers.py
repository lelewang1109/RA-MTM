"""Print every number used in the evaluation section of paper/draft_zh.md from the saved JSON results."""
import json
from pathlib import Path
OUT = Path(__file__).resolve().parent / 'output'
names = ['era5', 'era5_2014', 'wildfire', 'ring', 'gaussians']
R = {n: json.loads((OUT / f'replicate_{n}.json').read_text()) for n in names if (OUT / f'replicate_{n}.json').exists()}
F = json.loads((OUT / 'frontier.json').read_text())

print('== RQ2 reversal / missed (k=2, eps=2%), 2-D truth; permutation null')
for n, r in R.items():
    for m in ['TMTM', 'ST-MTM', 'ours: auto direction', 'ours: relaxed']:
        x = [z for z in r['misreading'] if z['method'] == m and z['k'] == 2 and z['eps_frac'] == .02][0]
        if x['T2D_clear'] == 0: continue
        ci = x['T2D_ci95']
        print(f"{n:10s} {m:22s} n={x['T2D_clear']:4d} rev {x['T2D_reversal_rate']:.3f} [{ci[0]:.2f},{ci[1]:.2f}] miss {x['T2D_missed_rate']:.3f} null {x['T2D_null_reversal_rate']:.3f} | own-axis rev {x['claim_reversal_rate']:.3f}")
print('\n== paired differences (relaxed - other), k=2, eps=2%, 8-frame blocks')
for n, r in R.items():
    for d in r.get('paired', []):
        if d['k'] == 2 and d['eps_frac'] == .02:
            print(f"{n:10s} {d['comparison']:30s} rev diff {d['reversal_diff']:+.3f} [{d['reversal_diff_ci95'][0]:+.3f},{d['reversal_diff_ci95'][1]:+.3f}]  missed diff {d['missed_diff']:+.3f} [{d['missed_diff_ci95'][0]:+.3f},{d['missed_diff_ci95'][1]:+.3f}]")
print('\n== eps sensitivity (k=2): TMTM / ST-MTM / relaxed reversal')
for n, r in R.items():
    row = []
    for e in [.01, .02, .05]:
        v = [[z for z in r['misreading'] if z['method'] == m and z['k'] == 2 and z['eps_frac'] == e][0]['T2D_reversal_rate'] for m in ['TMTM', 'ST-MTM', 'ours: relaxed']]
        row.append(f"{int(e*100)}%: " + '/'.join(f'{x:.3f}' for x in v))
    print(f"{n:10s} " + '   '.join(row))
print('\n== RQ3 trade-off (threshold+prune): mean err change, max merge change, pairs changed, unresolved')
for n, r in R.items():
    t0 = r['tradeoff']['0.0']; rng = r['certificate']['field_range']
    for c in ['0.02', '0.2', 'inf']:
        t = r['tradeoff'][c]
        print(f"{n:10s} kappa {c:5s}: mean err {t['ref_err_mean']:.2f} ({t['ref_err_mean']/t0['ref_err_mean']-1:+.0%}) max d_top {t['merge_err_max']:.2f} ({t['merge_err_max']/rng:.1%} range) pairs {t['pairs_merge_changed']/max(1,t['pairs']):.1%} relaxed frames {t['frames_relaxed']}")
print('\n== frontier: theorem checks and achieved vs certified frontier')
for n, f in F.items():
    c = f['theorem2_check']
    print(f"{n:10s} Thm2 viol {c['theorem_violations']} Cor1 viol {c['corollary_violations']} broken-frames {c['violated_frames']} ratio median {c['ratio_median']:.2f} p90 {c['ratio_p90']:.2f} max {c['ratio_max']:.2f}")
    for a in f['achieved']:
        print(f"      cap {a['cap']}: D {a['D_share']:.3f} E {a['E_share']:.3f} frontier@D {a['frontier_at_D']:.3f} gap {100*(a['E_share']-a['frontier_at_D']):.2f}pp unresolved {a['unresolved_frames']}")
