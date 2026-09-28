"""Width-free, calibration-free certificate (answers "baselines use other width models").

Drop widths, gaps, eccentricity and canvas (w = 0, g = 0): anchors are points whose order is a legal
leaf order. For a fixed order pi the smallest max |c(u_i) - q_i| over ANY monotone calibration c of
the map axis to the reference axis is
    tau_pt(pi) = max(0, max_{i before j in pi} (q_i - q_j) / 2)      (half the largest inverted gap),
and tau_pt* = min over legal orders. Every 1-D map whose anchors follow a hierarchy-consistent order
(TMTM, ST-MTM, ours without relaxation) -- whatever its width model and however its axis is read --
deviates from the reference by at least tau_pt* in that frame; tau_pt* <= tau* of the interval model.
For each method we also report tau_pt(pi_method): its deviation under the best monotone calibration.
Run: .venv/bin/python -W ignore prototypes/pointcert.py
"""
from pathlib import Path
import sys, json
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import replicate as rp, misreading as mr, relax_hierarchy as rh, task_reference as tr
from ramtm.error_budget import leaf_orders

OUT = tr.OUT


def tau_pt(orders, q):
    Q = np.asarray(q)[np.asarray(orders)]                                  # (m, n) references in map order
    if Q.shape[1] < 2: return np.zeros(len(Q))
    run_max = np.maximum.accumulate(Q, 1)                                  # largest earlier reference
    return np.maximum(0., ((run_max[:, :-1] - Q[:, 1:]) / 2).max(1))


def main():
    res = {}
    for name in rp.LOADERS:
        ds = rp.LOADERS[name](); sc = ds['sc']
        M, ext, conflict, ref = mr.method_positions(ds)
        L = ref['extent']; theta = .02 * L
        star, per = [], {m: [] for m in M}
        for t, (fr, ids) in enumerate(zip(sc['frames'], sc['ids'])):
            q = np.asarray(ref['qs'][t])
            star.append(float(tau_pt(leaf_orders(sc['hier'][t]), q).min()))
            for m, D in M.items():
                o = np.argsort(np.asarray(D['u'][t]), kind='stable')
                per[m].append(float(tau_pt([o], q)[0]))
        S = np.array(star)
        r = dict(axis=L, frames=len(S), conflict_frames_pt=int(np.sum(S > theta)), conflict_share_pt=float(np.mean(S > theta)),
                 max_share=float(S.max() / L), median_conflict_share=float(np.median(S[S > theta]) / L) if np.any(S > theta) else 0.,
                 methods={})
        for m, v in per.items():
            v = np.array(v)
            r['methods'][m] = dict(mean_share=float(v.mean() / L), frames_over_theta=int(np.sum(v > theta)),
                                   excess_mean_share=float(np.mean(v - S) / L), below_certificate=int(np.sum(v < S - 1e-9)))
        res[name] = r
        print(f"{name:10s} width-free certificate > theta in {r['conflict_frames_pt']}/{r['frames']} frames ({r['conflict_share_pt']:.0%}), max {r['max_share']:.1%}")
        for m, x in r['methods'].items():
            print(f"    {m:22s} mean {x['mean_share']:.3f}  frames>theta {x['frames_over_theta']:3d}  excess over certificate {x['excess_mean_share']:.3f}  below cert {x['below_certificate']}", flush=True)
    (OUT / 'pointcert.json').write_text(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
