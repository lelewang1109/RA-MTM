"""Reader-threshold sensitivity of the misreading pilot (method constants fixed at theta = 2%).
Run: .venv/bin/python -W ignore prototypes/misreading_sensitivity.py"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import misreading as mr, general_method as gm
EPS = [.01, .02, .05]
rows = []
for make in (gm.era5, gm.ring, gm.gaussians):
    ds = make(); cache = mr.method_positions(ds)
    for e in EPS:
        r, _, _ = mr.analyse(ds, e, cache); rows += r
(mr.OUT / 'misreading_sensitivity.json').write_text(json.dumps(rows, indent=1, default=float))
for ds, k in [('era5', 2), ('ring', 2), ('gaussians', 8)]:
    print(f'\n== {ds} k={k}: reversal vs 2-D truth [CI] (chance)  | vs claimed axis   for reader eps = 1% / 2% / 5%')
    for m in ['TMTM', 'ST-MTM', 'fixed-X anchored', 'ours: auto direction', 'ours: relaxed']:
        cells = []
        for e in EPS:
            x = [r for r in rows if r['dataset'] == ds and r['method'] == m and r['k'] == k and r['eps_frac'] == e][0]
            cells.append(f"{x['T2D_reversal_rate']:.3f}[{x['T2D_ci95'][0]:.2f},{x['T2D_ci95'][1]:.2f}]({x['T2D_null_reversal_rate']:.2f}) n={x['T2D_clear']:3d} |{x['claim_reversal_rate']:.3f}")
        print(f"{m:22s} " + '   '.join(cells))
