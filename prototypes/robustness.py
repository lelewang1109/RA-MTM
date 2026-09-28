"""RQ1 robustness: share of frames with hierarchy cost H > theta, across reference directions and thresholds.
Directions: 8 fixed angles (0..157.5 deg) + automatic motion direction. theta in {1, 2, 5}% of axis.
Run: .venv/bin/python -W ignore prototypes/robustness.py
"""
from pathlib import Path
import sys, json
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import general_method as gm, relax_hierarchy as rh, replicate as rp, task_reference as tr
from ramtm.reference_points import reference_points_from_frames

OUT = tr.OUT
ANGLES = list(np.arange(0, 180, 22.5)); THETAS = [.01, .02, .05]


def run(name):
    ds = rp.LOADERS[name](); sc = ds['sc']
    ext = reference_points_from_frames(sc['frames'], sc['ids'], kind='extremum')
    auto = gm.auto_reference(sc, ext, ds['lo'], ds['hi'])
    lo, hi = ds['lo'], ds['hi']; corners = np.array([[lo[0], lo[1]], [hi[0], lo[1]], [lo[0], hi[1]], [hi[0], hi[1]]])
    dirs = [('auto %.0f°' % auto['candidates']['direction']['angle_deg'], np.array(auto['candidates']['direction']['a']))]
    dirs += [('%.1f°' % a, np.array([np.cos(np.deg2rad(a)), np.sin(np.deg2rad(a))])) for a in ANGLES]
    out = []
    for label, a in dirs:
        proj = corners @ a; p = gm.universal_parameters(float(proj.min()), float(np.ptp(proj)), ds['domain_area'])
        H = []
        for t, (fr, ids) in enumerate(zip(sc['frames'], sc['ids'])):
            w = p.width_scale * np.asarray(sc['areas'][t]); q = ext[t] @ a
            tf, _ = gm.tau_free(w, q, p); th_, _ = rh.best_tau(rh.node_tree(fr, ids), w, q, p)
            H.append((th_ - tf) / p.canvas)
        H = np.array(H)
        out.append(dict(direction=label, **{f'share_theta_{int(t*100)}': float(np.mean(H > t)) for t in THETAS}, H_max=float(H.max())))
        print(f"{name:10s} {label:10s} " + '  '.join(f"θ={int(t*100)}%: {np.mean(H > t):.0%}" for t in THETAS) + f"   H max {H.max():.1%}", flush=True)
    return out


if __name__ == '__main__':
    res = {n: run(n) for n in ['era5', 'era5_2014', 'wildfire']}
    (OUT / 'robustness.json').write_text(json.dumps(res, indent=1))
    for n, rows in res.items():
        s2 = [r['share_theta_2'] for r in rows[1:]]
        print(f"{n}: over 8 fixed directions, share(H > 2%) = {min(s2):.0%}–{max(s2):.0%} (auto {rows[0]['share_theta_2']:.0%})")
